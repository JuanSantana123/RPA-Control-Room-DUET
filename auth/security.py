# ============================================================
# SEGURANÇA DE AUTENTICAÇÃO
# ============================================================

# Importa o CryptContext do Passlib.
# Ele será responsável por criar e verificar os hashes
# das senhas dos usuários.
from passlib.context import CryptContext

# Biblioteca padrão utilizada para consultar configurações
# de segurança fornecidas pelo ambiente de execução.
import os
# ============================================================
# CONFIGURAÇÃO DO HASH
# ============================================================

# Cria o contexto utilizado para trabalhar com senhas.
#
# bcrypt é o algoritmo que será utilizado para gerar
# o hash da senha.
#
# deprecated="auto" informa ao Passlib para considerar
# automaticamente algoritmos antigos como desatualizados
# caso futuramente adicionemos outro algoritmo.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# HASH DUMMY PARA AUTENTICAÇÃO
# ============================================================
#
# Utilizado quando uma tentativa de autenticação informa um
# username que não existe.
#
# Mesmo sem um usuário real, executamos uma verificação bcrypt
# para aproximar o custo computacional do caminho utilizado
# quando o usuário existe e a senha está incorreta.
#
# Isso reduz a diferença observável de tempo entre:
#
#     - username inexistente;
#     - username existente com senha incorreta.
#
# O hash é criado uma única vez quando este módulo é carregado.
# Ele NÃO representa a senha de nenhum usuário e nunca é salvo
# no banco de dados.
# ============================================================

DUMMY_PASSWORD_HASH = pwd_context.hash(
    "DUET-DUMMY-PASSWORD-NOT-A-REAL-USER"
)

# ============================================================
# GERAR HASH DA SENHA
# ============================================================

def gerar_hash_senha(senha: str) -> str:
    """
    Recebe a senha original e retorna o hash dela.

    A senha original nunca deve ser salva no banco.
    """

    # Transforma a senha em um hash seguro.
    return pwd_context.hash(senha)


# ============================================================
# VERIFICAR SENHA
# ============================================================

def verificar_senha(        
    senha: str,
    senha_hash: str
) -> bool:
    """
    Verifica se a senha informada corresponde ao hash
    armazenado no banco.
    """

    # Compara a senha informada com o hash existente.
    #
    # O resultado será:
    # True  -> senha correta
    # False -> senha incorreta
    return pwd_context.verify(
        senha,
        senha_hash
    )


# ============================================================
# VALIDAR TAMANHO DE SENHA PARA AUTENTICAÇÃO
# ============================================================

def senha_compativel_com_bcrypt(
    senha: str,
) -> bool:
    """
    Verifica se a senha recebida pode ser processada com
    segurança pelo bcrypt.

    O bcrypt trabalha com no máximo 72 bytes de entrada.

    Importante:
        o limite é medido em bytes UTF-8 e não simplesmente
        na quantidade de caracteres Python.

    Esta função é utilizada durante login/token para evitar
    que uma entrada excessivamente grande alcance diretamente
    o backend bcrypt e provoque uma exceção inesperada.
    """

    if not isinstance(senha, str):
        return False

    return len(
        senha.encode("utf-8")
    ) <= 72
# ============================================================
# EXECUTAR VERIFICAÇÃO DUMMY
# ============================================================

def executar_verificacao_senha_dummy(
    senha: str,
) -> None:
    """
    Executa uma verificação bcrypt sem utilizar a credencial
    de nenhum usuário real.

    Esta função é utilizada quando o username informado na
    autenticação não existe.

    O retorno da verificação é intencionalmente ignorado,
    pois o objetivo é apenas executar uma operação bcrypt
    equivalente à validação normal de senha.
    """

    pwd_context.verify(
        senha,
        DUMMY_PASSWORD_HASH,
    )
# ============================================================
# VALIDAR POLÍTICA DE SENHA
# ============================================================

def validar_politica_senha(senha: str) -> tuple[bool, str | None]:
    """
    Valida uma senha antes de ela ser transformada em hash.

    Regras atuais do Control Room:

        - a senha não pode ser vazia;
        - deve possuir pelo menos 8 caracteres;
        - deve possuir no máximo 72 bytes em UTF-8.

    O limite de 72 bytes é importante porque o algoritmo
    bcrypt possui essa limitação para a entrada utilizada
    na geração e verificação do hash.

    Retorno:

        (True, None)
            Senha válida.

        (False, mensagem)
            Senha inválida e mensagem que pode ser devolvida
            pela camada de negócio.
    """

    # --------------------------------------------------------
    # VALIDAR EXISTÊNCIA
    # --------------------------------------------------------

    if not senha:
        return (
            False,
            "A senha não pode ser vazia.",
        )

    # --------------------------------------------------------
    # VALIDAR TAMANHO MÍNIMO
    # --------------------------------------------------------

    if len(senha) < 8:
        return (
            False,
            "A senha deve possuir pelo menos 8 caracteres.",
        )

    # --------------------------------------------------------
    # VALIDAR LIMITE DO BCRYPT
    # --------------------------------------------------------
    #
    # Usamos bytes UTF-8, e não apenas len(senha), porque
    # caracteres Unicode podem ocupar mais de um byte.
    # --------------------------------------------------------

    tamanho_bytes = len(
        senha.encode("utf-8")
    )

    if tamanho_bytes > 72:
        return (
            False,
            "A senha deve possuir no máximo 72 bytes.",
        )

    return True, None

# ============================================================
# CONFIGURAÇÃO DE COOKIE
# ============================================================

def cookie_secure_habilitado() -> bool:
    """
    Informa se o cookie de autenticação deve utilizar
    a flag Secure.

    A configuração é controlada pela variável de ambiente:

        CONTROL_ROOM_COOKIE_SECURE

    Valores reconhecidos como verdadeiros:

        1
        true
        yes
        on

    Quando a variável não estiver definida, o padrão é False.

    Isso mantém o desenvolvimento local via HTTP funcionando,
    enquanto permite exigir HTTPS em produção sem alterar
    código-fonte.
    """

    valor = os.getenv(
        "CONTROL_ROOM_COOKIE_SECURE",
        "false",
    )

    return valor.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }