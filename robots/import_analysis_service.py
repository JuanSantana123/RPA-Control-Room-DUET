# ============================================================
# DUET CORE - ROBOTS - ANÁLISE DE PACOTE PARA IMPORTAÇÃO
# ============================================================
#
# Responsabilidade:
#
# - receber o ZIP antes da importação;
# - validar o pacote utilizando a mesma política de segurança
#   utilizada pelos Releases;
# - ler o duet-release.json quando existir;
# - localizar todos os arquivos Python do pacote;
# - informar o EntryPoint publicado, quando existir;
# - sugerir main.py quando aplicável, SEM selecioná-lo
#   automaticamente.
#
# IMPORTANTE:
#
# Este service NÃO:
#
# - cria Robot;
# - cria RobotVersion;
# - altera banco de dados;
# - executa código do pacote;
# - instala dependências;
# - escolhe EntryPoint automaticamente.
#
# A criação/importação real continua pertencendo a
# robots/import_service.py.
# ============================================================

import tempfile
from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)

from packaging import (
    project_packager as packager,
)

from releases.service import (
    read_package,
    safe_name,
)

from robots.import_package import (
    get_manifest_entrypoint,
    list_import_python_files,
    normalize_import_entrypoint,
    read_import_source_manifest,
    suggest_import_entrypoint,
)


# ============================================================
# ANALISAR PACOTE
# ============================================================

async def analyze_robot_package_service(
    file: UploadFile,
) -> dict:
    """
    Analisa um pacote ZIP antes da importação definitiva.

    O objetivo desta operação é permitir ao frontend conhecer:

        - os arquivos Python existentes;
        - o EntryPoint imutável de um Release DUET;
        - uma possível sugestão de EntryPoint para ZIP comum.

    Nenhuma entidade de Robot ou RobotVersion é criada aqui.
    """

    # ========================================================
    # 1. NOME DO ARQUIVO
    # ========================================================

    filename = safe_name(
        file.filename or ""
    )

    if not filename.lower().endswith(".zip"):

        raise HTTPException(
            status_code=400,
            detail=(
                "A importação de pacote aceita somente "
                "arquivos .zip."
            ),
        )

    # ========================================================
    # 2. CONTEÚDO RECEBIDO
    # ========================================================

    try:

        uploaded_bytes = await file.read()

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Não foi possível ler o pacote enviado."
            ),
        ) from error

    if not uploaded_bytes:

        raise HTTPException(
            status_code=400,
            detail="O pacote enviado está vazio.",
        )

    # ========================================================
    # 3. VALIDAÇÃO SEGURA DO ZIP
    # ========================================================
    #
    # read_package() é a mesma leitura utilizada pelo fluxo de
    # Release/Import do DUET.
    #
    # Dessa forma a análise não cria uma segunda política
    # independente de segurança.
    # ========================================================

    packager.BUILD_TEMP_REPOSITORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory(
        dir=packager.BUILD_TEMP_REPOSITORY
    ) as temp_dir:

        temp_package = (
            Path(temp_dir)
            / "import-analysis.zip"
        )

        temp_package.write_bytes(
            uploaded_bytes
        )

        contents = read_package(
            temp_package
        )

    # ========================================================
    # 4. MANIFESTO DE ORIGEM
    # ========================================================
    #
    # consume=False é importante.
    #
    # A análise apenas inspeciona o manifesto. O conteúdo do
    # pacote permanece intacto para as validações seguintes.
    # ========================================================

    source_manifest = (
        read_import_source_manifest(
            contents,
            consume=False,
        )
    )

    # ========================================================
    # 5. ARQUIVOS PYTHON
    # ========================================================

    python_files = (
        list_import_python_files(
            contents
        )
    )

    if not python_files:

        raise HTTPException(
            status_code=409,
            detail=(
                "O pacote não contém nenhum arquivo Python (.py)."
            ),
        )

    # ========================================================
    # 6. ENTRYPOINT PUBLICADO
    # ========================================================
    #
    # Um Release DUET moderno pode possuir:
    #
    #     entrypoint_path
    #
    # no duet-release.json.
    #
    # Esse valor pertence à versão publicada e é imutável.
    # Portanto ele será bloqueado no frontend.
    # ========================================================

    configured_entrypoint = (
        get_manifest_entrypoint(
            source_manifest
        )
    )

    if configured_entrypoint:

        configured_entrypoint = (
            normalize_import_entrypoint(
                configured_entrypoint
            )
        )

        if configured_entrypoint not in contents:

            raise HTTPException(
                status_code=409,
                detail=(
                    "O pacote não contém o EntryPoint "
                    "configurado no duet-release.json: "
                    f"{configured_entrypoint}."
                ),
            )

        if configured_entrypoint not in python_files:

            raise HTTPException(
                status_code=409,
                detail=(
                    "O EntryPoint configurado no "
                    "duet-release.json não é um arquivo "
                    f"Python válido: {configured_entrypoint}."
                ),
            )

    # ========================================================
    # 7. SUGESTÃO
    # ========================================================
    #
    # Para ZIP comum:
    #
    #     main.py
    #
    # pode ser apresentado como sugestão.
    #
    # Ele NÃO é selecionado automaticamente. A decisão continua
    # sendo explícita do usuário no frontend.
    #
    # Para Release DUET o EntryPoint já está configurado e,
    # portanto, não precisamos fazer inferência.
    # ========================================================

    suggested_entrypoint = None

    if configured_entrypoint is None:

        suggested_entrypoint = (
            suggest_import_entrypoint(
                python_files
            )
        )

    # ========================================================
    # 8. RESPOSTA
    # ========================================================

    return {
        "status":
            "success",

        "filename":
            filename,

        "python_files":
            python_files,

        "configured_entrypoint":
            configured_entrypoint,

        "suggested_entrypoint":
            suggested_entrypoint,

        "entrypoint_locked":
            configured_entrypoint is not None,
    }