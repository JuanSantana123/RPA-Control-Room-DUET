# ============================================================
# DUET CORE - SEGURANÇA DE ARTEFATOS
# ============================================================
#
# Regras compartilhadas de segurança para pacotes ZIP.
#
# Este módulo NÃO conhece FastAPI, banco, Robot ou Library.
# Ele trabalha exclusivamente com arquivos e lança
# ArtifactSecurityError quando encontra um artefato inseguro.
# ============================================================

import stat
import zipfile

from pathlib import Path, PurePosixPath


# ============================================================
# LIMITES PADRÃO
# ============================================================

MAX_UPLOAD_SIZE = 250 * 1024 * 1024
MAX_ZIP_FILES = 10_000
MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024
MAX_SINGLE_FILE_SIZE = 200 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


# ============================================================
# NOMES RESERVADOS DO WINDOWS
# ============================================================

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{
        f"{prefix}{numero}"
        for prefix in ("COM", "LPT")
        for numero in range(1, 10)
    },
}


class ArtifactSecurityError(Exception):
    """
    Erro de segurança ou integridade estrutural de artefato.
    """

    pass


# ============================================================
# NOME DO ARQUIVO RECEBIDO
# ============================================================

def validar_nome_zip(
    filename: str,
) -> str:
    """
    Valida o nome físico de um ZIP recebido.

    Não permite que o filename carregue caminho.
    """

    if not isinstance(filename, str):

        raise ArtifactSecurityError(
            "Nome do arquivo inválido."
        )

    nome = filename.strip()

    if not nome:

        raise ArtifactSecurityError(
            "Nome do arquivo não informado."
        )

    if "\x00" in nome:

        raise ArtifactSecurityError(
            "Nome do arquivo inválido."
        )

    if (
        "/" in nome
        or "\\" in nome
        or nome in {".", ".."}
    ):

        raise ArtifactSecurityError(
            "O nome do arquivo não pode conter caminhos."
        )

    _validar_componente_windows(
        nome
    )

    if Path(nome).suffix.lower() != ".zip":

        raise ArtifactSecurityError(
            "Apenas pacotes ZIP são permitidos."
        )

    return nome


# ============================================================
# COMPONENTE WINDOWS
# ============================================================

def _validar_componente_windows(
    componente: str,
) -> None:
    """
    Valida individualmente um nome de arquivo/diretório.

    Bloqueia comportamentos perigosos ou ambíguos no Windows:
    ADS, device names, trailing dot/space e caracteres proibidos.
    """

    if not componente:

        raise ArtifactSecurityError(
            "ZIP contém componente de caminho vazio."
        )

    if componente in {".", ".."}:

        raise ArtifactSecurityError(
            "ZIP contém componente de caminho inválido."
        )

    if len(componente) > 255:

        raise ArtifactSecurityError(
            "ZIP contém nome excessivamente longo."
        )

    if componente.endswith((".", " ")):

        raise ArtifactSecurityError(
            "ZIP contém nome incompatível com Windows."
        )

    # ":" em qualquer componente também bloqueia NTFS ADS:
    #
    #     arquivo.py:stream
    #
    if any(
        caractere in '<>:"/\\|?*'
        or ord(caractere) < 32
        for caractere in componente
    ):

        raise ArtifactSecurityError(
            "ZIP contém nome incompatível com Windows."
        )

    # Windows trata, por exemplo:
    #
    #     CON
    #     CON.txt
    #     COM1.py
    #
    # como nomes reservados.
    nome_base = (
        componente
        .split(".", 1)[0]
        .upper()
    )

    if nome_base in WINDOWS_RESERVED_NAMES:

        raise ArtifactSecurityError(
            "ZIP contém nome reservado do Windows."
        )


# ============================================================
# CAMINHO DE MEMBRO DO ZIP
# ============================================================

def normalizar_membro_zip(
    member_name: str,
) -> PurePosixPath:
    """
    Normaliza e valida o caminho lógico de um membro ZIP.

    A função é pública para que Packager/Libraries possam
    reutilizar exatamente a mesma interpretação de caminho.
    """

    if not member_name:

        raise ArtifactSecurityError(
            "ZIP contém entrada sem nome."
        )

    if "\x00" in member_name:

        raise ArtifactSecurityError(
            "ZIP contém nome inválido."
        )

    nome = member_name.replace(
        "\\",
        "/",
    )

    if nome.startswith("/"):

        raise ArtifactSecurityError(
            "ZIP contém caminho absoluto."
        )

    caminho = PurePosixPath(
        nome
    )

    if not caminho.parts:

        raise ArtifactSecurityError(
            "ZIP contém caminho inválido."
        )

    if ".." in caminho.parts:

        raise ArtifactSecurityError(
            "ZIP contém tentativa de path traversal."
        )

    for componente in caminho.parts:

        _validar_componente_windows(
            componente
        )

    return caminho


# ============================================================
# SYMLINK
# ============================================================

def _membro_eh_symlink(
    info: zipfile.ZipInfo,
) -> bool:
    """
    Detecta symlink através do modo Unix armazenado no ZIP.
    """

    modo = (
        info.external_attr >> 16
    )

    return stat.S_ISLNK(
        modo
    )


# ============================================================
# VALIDAÇÃO COMPLETA
# ============================================================

def validar_zip(
    zip_path,
    *,
    max_zip_size: int | None = MAX_UPLOAD_SIZE,
    max_uncompressed_size: int = MAX_UNCOMPRESSED_SIZE,
    max_single_file_size: int = MAX_SINGLE_FILE_SIZE,
    max_files: int = MAX_ZIP_FILES,
    max_compression_ratio: int = MAX_COMPRESSION_RATIO,
) -> None:
    """
    Valida integralmente um ZIP.

    Proteções:

    - Zip Slip;
    - caminhos absolutos;
    - caminhos incompatíveis com Windows;
    - NTFS Alternate Data Streams;
    - device names do Windows;
    - symlinks;
    - ZIP criptografado;
    - duplicidade case-insensitive;
    - colisão arquivo/diretório;
    - ZIP bomb;
    - arquivos individuais excessivos;
    - excesso de membros;
    - corrupção / CRC inválido.

    max_zip_size=None:
        não aplica limite ao tamanho compactado neste nível.
        Útil quando o chamador já possui sua própria política.
    """

    caminho_zip = Path(
        zip_path
    )

    if not caminho_zip.is_file():

        raise ArtifactSecurityError(
            "Pacote ZIP não encontrado."
        )

    if (
        max_zip_size is not None
        and caminho_zip.stat().st_size > max_zip_size
    ):

        raise ArtifactSecurityError(
            "Pacote excede o tamanho máximo permitido."
        )

    if not zipfile.is_zipfile(
        caminho_zip
    ):

        raise ArtifactSecurityError(
            "Arquivo enviado não é um ZIP válido."
        )

    try:

        with zipfile.ZipFile(
            caminho_zip,
            "r",
        ) as zip_file:

            membros = zip_file.infolist()

            if len(membros) > max_files:

                raise ArtifactSecurityError(
                    "ZIP excede a quantidade máxima de arquivos."
                )

            tamanho_total = 0

            # Caminhos canônicos Windows já observados.
            arquivos = set()
            diretorios = set()

            for info in membros:

                caminho = normalizar_membro_zip(
                    info.filename
                )

                if _membro_eh_symlink(
                    info
                ):

                    raise ArtifactSecurityError(
                        "ZIP contém link simbólico."
                    )

                if info.flag_bits & 0x1:

                    raise ArtifactSecurityError(
                        "ZIP criptografado não é permitido."
                    )

                partes_casefold = tuple(
                    parte.casefold()
                    for parte in caminho.parts
                )

                chave = "/".join(
                    partes_casefold
                )

                # Registra todos os ancestrais como diretórios.
                ancestrais = {
                    "/".join(
                        partes_casefold[:indice]
                    )
                    for indice in range(
                        1,
                        len(partes_casefold),
                    )
                }

                if info.is_dir():

                    # "foo" já foi registrado como arquivo e agora
                    # aparece como diretório.
                    if chave in arquivos:

                        raise ArtifactSecurityError(
                            "ZIP contém colisão entre arquivo e diretório."
                        )

                    diretorios.add(
                        chave
                    )

                    continue

                # Mesmo arquivo duas vezes ou diferença apenas de caixa:
                #
                # main.py
                # MAIN.py
                if chave in arquivos:

                    raise ArtifactSecurityError(
                        "ZIP contém arquivos duplicados."
                    )

                # Um diretório já registrado possui exatamente o mesmo
                # nome que este arquivo.
                if chave in diretorios:

                    raise ArtifactSecurityError(
                        "ZIP contém colisão entre arquivo e diretório."
                    )

                # Exemplo inseguro:
                #
                # primeiro membro: foo
                # segundo membro:  foo/bar.py
                if any(
                    ancestral in arquivos
                    for ancestral in ancestrais
                ):

                    raise ArtifactSecurityError(
                        "ZIP contém colisão entre arquivo e diretório."
                    )

                arquivos.add(
                    chave
                )

                diretorios.update(
                    ancestrais
                )

                if (
                    info.file_size
                    > max_single_file_size
                ):

                    raise ArtifactSecurityError(
                        "ZIP contém arquivo excessivamente grande."
                    )

                tamanho_total += (
                    info.file_size
                )

                if (
                    tamanho_total
                    > max_uncompressed_size
                ):

                    raise ArtifactSecurityError(
                        "ZIP excede o tamanho máximo descompactado."
                    )

                if (
                    info.file_size > 0
                    and info.compress_size == 0
                ):

                    raise ArtifactSecurityError(
                        "ZIP possui taxa de compressão inválida."
                    )

                if info.compress_size > 0:

                    taxa = (
                        info.file_size
                        / info.compress_size
                    )

                    if (
                        taxa
                        > max_compression_ratio
                    ):

                        raise ArtifactSecurityError(
                            "ZIP possui taxa de compressão suspeita."
                        )

            arquivo_corrompido = (
                zip_file.testzip()
            )

            if arquivo_corrompido:

                raise ArtifactSecurityError(
                    "ZIP corrompido."
                )

    except ArtifactSecurityError:
        raise

    except (
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ) as error:

        raise ArtifactSecurityError(
            "Arquivo ZIP inválido ou corrompido."
        ) from error


# ============================================================
# CAMINHO RELATIVO SEGURO
# ============================================================

def caminho_relativo_seguro(
    path,
    root,
) -> str:
    """
    Confirma que path pertence fisicamente à root e devolve
    caminho relativo em formato POSIX.
    """

    raiz = Path(
        root
    ).resolve()

    caminho = Path(
        path
    ).resolve()

    try:

        relativo = caminho.relative_to(
            raiz
        )

    except ValueError as error:

        raise ArtifactSecurityError(
            "Artefato fora do diretório permitido."
        ) from error

    return relativo.as_posix()