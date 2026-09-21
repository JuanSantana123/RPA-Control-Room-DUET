import os
import json
import base64
import ctypes

from pathlib import Path
from ctypes import wintypes

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


# ============================================================
# CONFIGURAÇÃO DA CHAVE MESTRA DO VAULT
# ============================================================

# Nome da pasta utilizada pelo DUET CORE dentro do ProgramData.
VAULT_FOLDER_NAME = "DuetCore"


# Nome do arquivo que armazenará a Master Key protegida
# pelo DPAPI do Windows.
VAULT_KEY_FILE_NAME = "master.key"

# ============================================================
# BACKUP / MIGRAÇÃO DA MASTER KEY
# ============================================================

# Versão atual do formato do arquivo de recuperação.
#
# Isso permite que no futuro o formato seja evoluído sem
# quebrar backups criados por versões anteriores.
VAULT_BACKUP_VERSION = 1


# Identificação gravada dentro do arquivo de backup.
#
# Ela ajuda a impedir que um arquivo qualquer seja tratado
# acidentalmente como um backup válido do Vault.
VAULT_BACKUP_TYPE = "DUET_CORE_VAULT_BACKUP"


# Tamanho mínimo aceito para a senha de recuperação.
#
# A senha não será utilizada diretamente como chave.
# Ela será processada pelo Scrypt.
VAULT_RECOVERY_PASSWORD_MIN_LENGTH = 12
# ============================================================
# CONSTANTES DO WINDOWS DPAPI
# ============================================================

# Impede o Windows de abrir qualquer interface gráfica
# durante a proteção/desproteção da chave.
CRYPTPROTECT_UI_FORBIDDEN = 0x01


# Vincula a proteção da chave à máquina Windows.
#
# Isso permite que o Control Room reutilize a chave
# após reinicializações sem depender do usuário logado.
CRYPTPROTECT_LOCAL_MACHINE = 0x04


# ============================================================
# ESTRUTURA UTILIZADA PELO WINDOWS DPAPI
# ============================================================
#
# CryptProtectData e CryptUnprotectData trabalham com uma
# estrutura chamada DATA_BLOB.
#
# Ela contém:
#
# - tamanho dos dados;
# - ponteiro para os dados.
#
# ============================================================

class DATA_BLOB(ctypes.Structure):

    _fields_ = [
        (
            "cbData",
            wintypes.DWORD
        ),
        (
            "pbData",
            ctypes.POINTER(
                ctypes.c_ubyte
            )
        )
    ]


def _criar_blob(
    dados: bytes
):
    """
    Converte bytes Python para a estrutura DATA_BLOB
    esperada pelas funções do Windows DPAPI.

    Retorna também o buffer original para garantir
    que ele permaneça vivo durante a chamada nativa.
    """

    buffer = ctypes.create_string_buffer(
        dados
    )

    blob = DATA_BLOB(
        len(dados),
        ctypes.cast(
            buffer,
            ctypes.POINTER(
                ctypes.c_ubyte
            )
        )
    )

    return blob, buffer


def _proteger_com_dpapi(
    dados: bytes
) -> bytes:
    """
    Protege dados utilizando o Windows DPAPI.

    A proteção utiliza o escopo da máquina através de
    CRYPTPROTECT_LOCAL_MACHINE.

    O resultado somente poderá ser recuperado através
    do DPAPI da mesma máquina Windows.
    """

    if os.name != "nt":

        raise RuntimeError(
            "O armazenamento protegido do Vault utiliza "
            "Windows DPAPI e somente pode ser executado "
            "em sistemas Windows."
        )

    entrada_blob, entrada_buffer = _criar_blob(
        dados
    )

    saida_blob = DATA_BLOB()

    flags = (
        CRYPTPROTECT_UI_FORBIDDEN
        |
        CRYPTPROTECT_LOCAL_MACHINE
    )

    resultado = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(
            entrada_blob
        ),
        "DUET CORE Vault Master Key",
        None,
        None,
        None,
        flags,
        ctypes.byref(
            saida_blob
        )
    )

    if not resultado:

        codigo_erro = ctypes.get_last_error()

        raise RuntimeError(
            "Não foi possível proteger a chave mestra "
            f"com o Windows DPAPI. Código: {codigo_erro}"
        )

    try:

        return ctypes.string_at(
            saida_blob.pbData,
            saida_blob.cbData
        )

    finally:

        # O Windows aloca a memória da resposta.
        #
        # LocalFree libera essa memória depois que os dados
        # já foram copiados para um objeto Python.
        ctypes.windll.kernel32.LocalFree(
            saida_blob.pbData
        )


def _desproteger_com_dpapi(
    dados_protegidos: bytes
) -> bytes:
    """
    Recupera a Master Key previamente protegida
    pelo Windows DPAPI.
    """

    if os.name != "nt":

        raise RuntimeError(
            "O armazenamento protegido do Vault utiliza "
            "Windows DPAPI e somente pode ser executado "
            "em sistemas Windows."
        )

    entrada_blob, entrada_buffer = _criar_blob(
        dados_protegidos
    )

    saida_blob = DATA_BLOB()

    flags = CRYPTPROTECT_UI_FORBIDDEN

    resultado = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(
            entrada_blob
        ),
        None,
        None,
        None,
        None,
        flags,
        ctypes.byref(
            saida_blob
        )
    )

    if not resultado:

        codigo_erro = ctypes.get_last_error()

        raise RuntimeError(
            "Não foi possível recuperar a chave mestra "
            f"através do Windows DPAPI. Código: {codigo_erro}"
        )

    try:

        return ctypes.string_at(
            saida_blob.pbData,
            saida_blob.cbData
        )

    finally:

        ctypes.windll.kernel32.LocalFree(
            saida_blob.pbData
        )


def _obter_caminho_chave_mestra() -> Path:
    """
    Retorna o local onde a chave protegida do Vault
    será persistida.

    No Windows será utilizado:

    C:\\ProgramData\\DuetCore\\Vault\\master.key
    """

    program_data = os.getenv(
        "PROGRAMDATA"
    )

    if not program_data:

        raise RuntimeError(
            "A variável de ambiente PROGRAMDATA "
            "não está disponível no Windows."
        )

    return (
        Path(program_data)
        / VAULT_FOLDER_NAME
        / "Vault"
        / VAULT_KEY_FILE_NAME
    )


def _validar_chave_mestra(
    chave_bytes: bytes
) -> bytes:
    """
    Garante que a Master Key tenha exatamente
    32 bytes, conforme exigido pelo AES-256.
    """

    if len(chave_bytes) != 32:

        raise RuntimeError(
            "A chave mestra do Vault precisa possuir exatamente "
            "32 bytes para AES-256."
        )

    return chave_bytes



def _validar_senha_recuperacao(
    senha: str
):
    """
    Valida a senha utilizada para proteger o backup
    portátil da Master Key.

    A senha nunca será armazenada no arquivo de backup.
    """

    if not senha:

        raise ValueError(
            "A senha de recuperação não pode estar vazia."
        )

    if len(senha) < VAULT_RECOVERY_PASSWORD_MIN_LENGTH:

        raise ValueError(
            "A senha de recuperação precisa possuir pelo menos "
            f"{VAULT_RECOVERY_PASSWORD_MIN_LENGTH} caracteres."
        )


def _derivar_chave_recuperacao(
    senha: str,
    salt: bytes
) -> bytes:
    """
    Deriva uma chave criptográfica de 32 bytes a partir
    da senha de recuperação.

    O Scrypt torna tentativas de força bruta muito mais
    custosas do que simplesmente aplicar um hash comum.

    Parâmetros:

    n:
        Custo computacional.

    r:
        Custo de memória.

    p:
        Paralelismo.

    length:
        32 bytes para AES-256.
    """

    _validar_senha_recuperacao(
        senha
    )

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2 ** 15,
        r=8,
        p=1
    )

    return kdf.derive(
        senha.encode(
            "utf-8"
        )
    )

def _obter_chave_mestra():
    """
    Obtém a Master Key utilizada pelo Vault.

    Ordem:

    1. master.key protegido pelo Windows DPAPI;
    2. geração automática na primeira instalação.
    """

    # ========================================================
    # CAMINHO DA MASTER KEY PROTEGIDA
    # ========================================================
    #
    # O master.key possui prioridade porque representa a
    # Master Key oficial desta instalação.
    #
    # Isso também garante que uma chave restaurada através
    # de vault-backup.key não seja ignorada por causa de uma
    # variável de ambiente antiga ainda configurada no Windows.
    # ========================================================

    caminho_chave = _obter_caminho_chave_mestra()


    # ========================================================
    # CHAVE JÁ EXISTE
    # ========================================================

    if caminho_chave.exists():

        try:

            conteudo = caminho_chave.read_text(
                encoding="utf-8"
            ).strip()

            dados_protegidos = base64.urlsafe_b64decode(
                conteudo
            )

        except Exception as error:

            raise RuntimeError(
                "Não foi possível ler o arquivo protegido "
                f"da chave mestra: {caminho_chave}"
            ) from error


        # Recupera a Master Key utilizando o DPAPI
        # desta máquina Windows.
        chave_bytes = _desproteger_com_dpapi(
            dados_protegidos
        )


        # Garante que a chave recuperada possui
        # exatamente 32 bytes.
        return _validar_chave_mestra(
            chave_bytes
        )



    # ========================================================
    # PRIMEIRA EXECUÇÃO
    # ========================================================
    #
    # Nenhuma Master Key foi encontrada porque
    # ainda não existe um master.key nesta instalação.
    #
    # Portanto é criada uma nova Master Key aleatória
    # de exatamente 32 bytes para AES-256.
    # ========================================================

    nova_chave = os.urandom(
        32
    )


    # ========================================================
    # PROTEGE A NOVA MASTER KEY COM DPAPI
    # ========================================================

    chave_protegida = _proteger_com_dpapi(
        nova_chave
    )


    # ========================================================
    # PREPARA O CONTEÚDO DO ARQUIVO
    # ========================================================
    #
    # O Base64 aqui NÃO representa a Master Key em texto puro.
    #
    # Ele representa os bytes que já foram protegidos pelo
    # Windows DPAPI.
    # ========================================================

    conteudo_arquivo = base64.urlsafe_b64encode(
        chave_protegida
    ).decode(
        "utf-8"
    )


    # ========================================================
    # CRIA A PASTA DO VAULT
    # ========================================================

    caminho_chave.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # ========================================================
    # GRAVA SEM PERMITIR SOBRESCRITA
    # ========================================================
    #
    # O modo "x" garante que o arquivo só será criado se ele
    # ainda não existir.
    #
    # Isso também protege contra duas instâncias tentando
    # criar a Master Key ao mesmo tempo.
    # ========================================================

    try:

        with open(
            caminho_chave,
            "x",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(
                conteudo_arquivo
            )

    except FileExistsError:

        # Outro processo pode ter criado a Master Key
        # alguns milissegundos antes.
        #
        # Nesse caso descartamos a chave recém-gerada
        # e carregamos a chave oficial já salva.
        return _obter_chave_mestra()


    return nova_chave

def exportar_chave_mestra(
    senha_recuperacao: str
) -> bytes:
    """
    Exporta a Master Key do Vault em formato portátil.

    A Master Key nunca é salva em texto puro.

    Fluxo:

        Master Key
            ↓
        senha de recuperação
            ↓
        Scrypt
            ↓
        chave AES-256
            ↓
        AES-GCM
            ↓
        arquivo portátil

    O resultado desta função pode ser salvo como:

        vault-backup.key
    """

    # --------------------------------------------------------
    # VALIDA SENHA
    # --------------------------------------------------------

    _validar_senha_recuperacao(
        senha_recuperacao
    )


    # --------------------------------------------------------
    # RECUPERA A MASTER KEY ATUAL
    # --------------------------------------------------------

    master_key = _obter_chave_mestra()


    # --------------------------------------------------------
    # SALT
    # --------------------------------------------------------
    #
    # O salt NÃO é secreto.
    #
    # Ele garante que duas exportações utilizando a mesma
    # senha produzam chaves derivadas diferentes.
    # --------------------------------------------------------

    salt = os.urandom(
        16
    )


    # --------------------------------------------------------
    # DERIVA A CHAVE A PARTIR DA SENHA
    # --------------------------------------------------------

    chave_recuperacao = _derivar_chave_recuperacao(
        senha_recuperacao,
        salt
    )


    # --------------------------------------------------------
    # NONCE AES-GCM
    # --------------------------------------------------------

    nonce = os.urandom(
        12
    )


    # --------------------------------------------------------
    # AAD
    # --------------------------------------------------------
    #
    # Este valor não é criptografado, porém é autenticado
    # pelo AES-GCM.
    # --------------------------------------------------------

    associated_data = (
        f"{VAULT_BACKUP_TYPE}:"
        f"{VAULT_BACKUP_VERSION}"
    ).encode(
        "utf-8"
    )


    # --------------------------------------------------------
    # CRIPTOGRAFA A MASTER KEY
    # --------------------------------------------------------

    aes = AESGCM(
        chave_recuperacao
    )

    master_key_criptografada = aes.encrypt(
        nonce,
        master_key,
        associated_data
    )


    # --------------------------------------------------------
    # FORMATO DO ARQUIVO
    # --------------------------------------------------------

    backup = {

        "type": VAULT_BACKUP_TYPE,

        "version": VAULT_BACKUP_VERSION,

        "kdf": {
            "name": "scrypt",
            "n": 2 ** 15,
            "r": 8,
            "p": 1
        },

        "cipher": "AES-256-GCM",

        "salt": base64.urlsafe_b64encode(
            salt
        ).decode(
            "utf-8"
        ),

        "nonce": base64.urlsafe_b64encode(
            nonce
        ).decode(
            "utf-8"
        ),

        "encrypted_master_key": base64.urlsafe_b64encode(
            master_key_criptografada
        ).decode(
            "utf-8"
        )
    }


    # --------------------------------------------------------
    # TRANSFORMA EM JSON
    # --------------------------------------------------------

    conteudo = json.dumps(
        backup,
        indent=4,
        ensure_ascii=False
    )


    return conteudo.encode(
        "utf-8"
    )

def importar_chave_mestra(
    conteudo_backup: bytes,
    senha_recuperacao: str
):
    """
    Importa uma Master Key previamente exportada.

    A Master Key recuperada será protegida novamente
    pelo DPAPI do Windows atual.

    IMPORTANTE:

    Esta função NÃO sobrescreve automaticamente um
    master.key existente.

    Isso evita destruir acidentalmente uma instalação
    já configurada.
    """

    # --------------------------------------------------------
    # VALIDA SENHA
    # --------------------------------------------------------

    _validar_senha_recuperacao(
        senha_recuperacao
    )


    # --------------------------------------------------------
    # VERIFICA SE JÁ EXISTE UMA MASTER KEY LOCAL
    # --------------------------------------------------------

    caminho_chave = _obter_caminho_chave_mestra()

    if caminho_chave.exists():

        raise RuntimeError(
            "Já existe uma Master Key configurada neste servidor. "
            "A importação foi cancelada para impedir a substituição "
            "acidental da chave existente."
        )


    # --------------------------------------------------------
    # LÊ O BACKUP
    # --------------------------------------------------------

    try:

        backup = json.loads(
            conteudo_backup.decode(
                "utf-8"
            )
        )

    except Exception as error:

        raise RuntimeError(
            "O arquivo informado não é um backup válido "
            "do Vault."
        ) from error


    # --------------------------------------------------------
    # VALIDA IDENTIFICAÇÃO
    # --------------------------------------------------------

    if backup.get("type") != VAULT_BACKUP_TYPE:

        raise RuntimeError(
            "O arquivo informado não pertence ao Vault "
            "do DUET CORE."
        )


    # --------------------------------------------------------
    # VALIDA VERSÃO
    # --------------------------------------------------------

    if backup.get("version") != VAULT_BACKUP_VERSION:

        raise RuntimeError(
            "A versão deste backup do Vault não é suportada."
        )


    # --------------------------------------------------------
    # VALIDA ALGORITMO
    # --------------------------------------------------------

    kdf_config = backup.get(
        "kdf",
        {}
    )

    if kdf_config.get("name") != "scrypt":

        raise RuntimeError(
            "O algoritmo de derivação de chave deste "
            "backup não é suportado."
        )


    if backup.get("cipher") != "AES-256-GCM":

        raise RuntimeError(
            "O algoritmo de criptografia deste backup "
            "não é suportado."
        )


    # --------------------------------------------------------
    # DECODIFICA OS DADOS
    # --------------------------------------------------------

    try:

        salt = base64.urlsafe_b64decode(
            backup["salt"]
        )

        nonce = base64.urlsafe_b64decode(
            backup["nonce"]
        )

        master_key_criptografada = base64.urlsafe_b64decode(
            backup["encrypted_master_key"]
        )

    except Exception as error:

        raise RuntimeError(
            "O arquivo de backup do Vault está corrompido."
        ) from error


    # --------------------------------------------------------
    # DERIVA NOVAMENTE A CHAVE DA SENHA
    # --------------------------------------------------------

    chave_recuperacao = _derivar_chave_recuperacao(
        senha_recuperacao,
        salt
    )


    # --------------------------------------------------------
    # AAD
    # --------------------------------------------------------

    associated_data = (
        f"{VAULT_BACKUP_TYPE}:"
        f"{VAULT_BACKUP_VERSION}"
    ).encode(
        "utf-8"
    )


    # --------------------------------------------------------
    # RECUPERA A MASTER KEY
    # --------------------------------------------------------

    aes = AESGCM(
        chave_recuperacao
    )

    try:

        master_key = aes.decrypt(
            nonce,
            master_key_criptografada,
            associated_data
        )

    except Exception as error:

        raise RuntimeError(
            "Não foi possível abrir o backup do Vault. "
            "A senha de recuperação pode estar incorreta "
            "ou o arquivo pode ter sido alterado."
        ) from error


    # --------------------------------------------------------
    # VALIDA MASTER KEY
    # --------------------------------------------------------

    _validar_chave_mestra(
        master_key
    )


    # --------------------------------------------------------
    # PROTEGE COM O DPAPI DESTA NOVA MÁQUINA
    # --------------------------------------------------------

    chave_protegida = _proteger_com_dpapi(
        master_key
    )


    conteudo_master_key = base64.urlsafe_b64encode(
        chave_protegida
    ).decode(
        "utf-8"
    )


    # --------------------------------------------------------
    # CRIA DIRETÓRIO
    # --------------------------------------------------------

    caminho_chave.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # GRAVA SEM PERMITIR SOBRESCRITA
    # --------------------------------------------------------

    try:

        with open(
            caminho_chave,
            "x",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(
                conteudo_master_key
            )

    except FileExistsError:

        raise RuntimeError(
            "Uma Master Key foi criada neste servidor "
            "durante a importação. A operação foi cancelada."
        )


    return {
        "status": "success",
        "message": "Master Key importada e protegida pelo Windows DPAPI."
    }
def criptografar(valor: str, associated_data: str = "") -> str:
    """
    Criptografa um valor usando AES-256-GCM.
    """

    if valor is None:
        raise ValueError(
            "Não é possível criptografar um valor None."
        )

    chave = _obter_chave_mestra()

    aes = AESGCM(chave)

    # Nonce aleatório de 12 bytes.
    nonce = os.urandom(12)

    dados = valor.encode("utf-8")

    aad = associated_data.encode("utf-8")

    ciphertext = aes.encrypt(
        nonce,
        dados,
        aad
    )

    # Armazena nonce + conteúdo criptografado.
    resultado = nonce + ciphertext

    return base64.urlsafe_b64encode(
        resultado
    ).decode("utf-8")


def descriptografar(
    valor_criptografado: str,
    associated_data: str = ""
) -> str:
    """
    Descriptografa um valor usando AES-256-GCM.
    """

    if not valor_criptografado:
        raise ValueError(
            "Valor criptografado vazio."
        )

    chave = _obter_chave_mestra()

    aes = AESGCM(chave)

    try:
        dados = base64.urlsafe_b64decode(
            valor_criptografado
        )
    except Exception as error:
        raise RuntimeError(
            "Valor criptografado não está em Base64 válido."
        ) from error

    nonce = dados[:12]
    ciphertext = dados[12:]

    aad = associated_data.encode("utf-8")

    try:
        plaintext = aes.decrypt(
            nonce,
            ciphertext,
            aad
        )
    except Exception as error:
        raise RuntimeError(
            "Não foi possível descriptografar o valor. "
            "A chave ou os dados podem estar incorretos."
        ) from error

    return plaintext.decode("utf-8")