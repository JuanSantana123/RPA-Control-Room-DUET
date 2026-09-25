# ============================================================
# DUET CORE - MIGRAÇÃO DE CREDENCIAIS DE DISPOSITIVO
# ============================================================
#
# Objetivo:
#
# 1. evoluir vault_credentials para suportar dois escopos:
#
#       automation
#       device
#
# 2. identificar o tipo técnico da credencial:
#
#       generic
#       windows
#
# 3. permitir credenciais de Device sem pasta;
#
# 4. adicionar agents.execution_credential_id;
#
# 5. criar FK:
#
#       agents.execution_credential_id
#           ->
#       vault_credentials.id
#
# 6. preservar integralmente as credenciais existentes.
#
#
# IMPORTANTE
# ----------
#
# Esta migration:
#
# - NÃO apaga credenciais;
# - NÃO apaga campos secretos;
# - NÃO recria vault_credentials;
# - NÃO recria agents;
# - NÃO altera Robots;
# - NÃO altera Executions;
# - NÃO altera Schedules;
# - NÃO altera o Scheduler;
# - NÃO descriptografa nenhum segredo;
# - pode ser executada novamente com segurança.
#
#
# BACKFILL
# --------
#
# Todas as credenciais já existentes serão classificadas como:
#
#       scope = "automation"
#       credential_type = "generic"
#
# Portanto o comportamento atual do Vault permanece intacto.
#
#
# BANCO
# -----
#
# Esta migration foi preparada para PostgreSQL.
# ============================================================

from sqlalchemy import inspect, text

from database import engine


# ============================================================
# CONSTANTES
# ============================================================

VAULT_TABLE = "vault_credentials"
AGENTS_TABLE = "agents"

AGENT_CREDENTIAL_FK_NAME = (
    "fk_agents_execution_credential_id_vault_credentials"
)

VAULT_SCOPE_INDEX_NAME = (
    "ix_vault_credentials_scope"
)

VAULT_TYPE_INDEX_NAME = (
    "ix_vault_credentials_credential_type"
)

AGENT_CREDENTIAL_INDEX_NAME = (
    "ix_agents_execution_credential_id"
)


# ============================================================
# HELPERS DE INSPEÇÃO
# ============================================================

def obter_dialeto() -> str:
    """Retorna o dialeto realmente utilizado pelo Control Room."""

    return engine.dialect.name.lower()


def obter_tabelas() -> set[str]:
    """Retorna as tabelas existentes no banco sem modificar nada."""

    return set(
        inspect(
            engine
        ).get_table_names()
    )


def obter_colunas(
    table_name: str,
) -> dict[str, dict]:
    """Retorna as colunas existentes indexadas pelo nome."""

    return {
        column["name"]: column
        for column in inspect(
            engine
        ).get_columns(
            table_name
        )
    }


def obter_foreign_keys(
    table_name: str,
) -> list[dict]:
    """Retorna as Foreign Keys existentes da tabela."""

    return inspect(
        engine
    ).get_foreign_keys(
        table_name
    )


def obter_indices(
    table_name: str,
) -> list[dict]:
    """Retorna os índices existentes da tabela."""

    return inspect(
        engine
    ).get_indexes(
        table_name
    )


def foreign_key_existe(
    *,
    table_name: str,
    constrained_column: str,
    referred_table: str,
) -> bool:
    """
    Confirma a existência da FK pela coluna e tabela de destino.

    Não dependemos somente do nome porque instalações anteriores
    podem ter criado a mesma FK com outro identificador.
    """

    return any(
        foreign_key.get(
            "constrained_columns"
        )
        ==
        [
            constrained_column
        ]
        and
        foreign_key.get(
            "referred_table"
        )
        ==
        referred_table
        for foreign_key in obter_foreign_keys(
            table_name
        )
    )


def indice_existe(
    *,
    table_name: str,
    index_name: str,
) -> bool:
    """Confirma se um índice já existe pelo nome."""

    return any(
        index.get(
            "name"
        )
        ==
        index_name
        for index in obter_indices(
            table_name
        )
    )


# ============================================================
# VALIDAÇÃO INICIAL
# ============================================================

def validar_pre_requisitos() -> None:
    """
    Bloqueia a migration antes de qualquer ALTER caso o ambiente
    não seja o esperado.
    """

    dialect = obter_dialeto()

    if dialect != "postgresql":

        raise RuntimeError(
            "Esta migration foi preparada para PostgreSQL. "
            f"Banco detectado: {dialect}."
        )


    tabelas = obter_tabelas()


    if VAULT_TABLE not in tabelas:

        raise RuntimeError(
            'A tabela "vault_credentials" não existe. '
            "Nenhuma alteração foi aplicada."
        )


    if AGENTS_TABLE not in tabelas:

        raise RuntimeError(
            'A tabela "agents" não existe. '
            "Nenhuma alteração foi aplicada."
        )


# ============================================================
# 1 - VAULT_CREDENTIALS.SCOPE
# ============================================================

def garantir_scope() -> None:
    """
    Adiciona e normaliza vault_credentials.scope.

    Credenciais existentes recebem "automation".
    """

    print(
        "[1/7] Verificando vault_credentials.scope..."
    )


    colunas = obter_colunas(
        VAULT_TABLE
    )


    if "scope" not in colunas:

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    ALTER TABLE vault_credentials
                    ADD COLUMN scope VARCHAR
                    """
                )
            )


        print(
            "      coluna criada."
        )

    else:

        print(
            "      coluna já existe."
        )


    with engine.begin() as connection:

        result = connection.execute(
            text(
                """
                UPDATE vault_credentials
                SET scope = 'automation'
                WHERE scope IS NULL
                   OR BTRIM(scope) = ''
                """
            )
        )


    print(
        "      credenciais normalizadas: "
        f"{result.rowcount if result.rowcount is not None else 0}."
    )


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE vault_credentials
                ALTER COLUMN scope
                SET DEFAULT 'automation'
                """
            )
        )


        connection.execute(
            text(
                """
                ALTER TABLE vault_credentials
                ALTER COLUMN scope
                SET NOT NULL
                """
            )
        )


# ============================================================
# 2 - CREDENTIAL_TYPE
# ============================================================

def garantir_credential_type() -> None:
    """
    Adiciona e normaliza vault_credentials.credential_type.

    Credenciais existentes recebem "generic".
    """

    print(
        "[2/7] Verificando vault_credentials.credential_type..."
    )


    colunas = obter_colunas(
        VAULT_TABLE
    )


    if "credential_type" not in colunas:

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    ALTER TABLE vault_credentials
                    ADD COLUMN credential_type VARCHAR
                    """
                )
            )


        print(
            "      coluna criada."
        )

    else:

        print(
            "      coluna já existe."
        )


    with engine.begin() as connection:

        result = connection.execute(
            text(
                """
                UPDATE vault_credentials
                SET credential_type = 'generic'
                WHERE credential_type IS NULL
                   OR BTRIM(credential_type) = ''
                """
            )
        )


    print(
        "      credenciais normalizadas: "
        f"{result.rowcount if result.rowcount is not None else 0}."
    )


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE vault_credentials
                ALTER COLUMN credential_type
                SET DEFAULT 'generic'
                """
            )
        )


        connection.execute(
            text(
                """
                ALTER TABLE vault_credentials
                ALTER COLUMN credential_type
                SET NOT NULL
                """
            )
        )


# ============================================================
# 3 - FOLDER_ID NULLABLE
# ============================================================

def permitir_device_sem_pasta() -> None:
    """
    Permite folder_id = NULL.

    Isso NÃO altera nenhuma credencial existente.
    """

    print(
        "[3/7] Verificando vault_credentials.folder_id..."
    )


    colunas = obter_colunas(
        VAULT_TABLE
    )


    folder_column = colunas.get(
        "folder_id"
    )


    if folder_column is None:

        raise RuntimeError(
            "vault_credentials.folder_id não foi encontrada."
        )


    if folder_column.get(
        "nullable",
        True,
    ):

        print(
            "      coluna já aceita NULL."
        )

        return


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE vault_credentials
                ALTER COLUMN folder_id
                DROP NOT NULL
                """
            )
        )


    print(
        "      coluna agora aceita NULL."
    )


# ============================================================
# 4 - AGENTS.EXECUTION_CREDENTIAL_ID
# ============================================================

def garantir_execution_credential_id() -> None:
    """
    Adiciona a referência da credencial de execução ao Agent.

    O valor inicia NULL para todos os Agents atuais.
    """

    print(
        "[4/7] Verificando agents.execution_credential_id..."
    )


    colunas = obter_colunas(
        AGENTS_TABLE
    )


    if "execution_credential_id" in colunas:

        print(
            "      coluna já existe."
        )

        return


    with engine.begin() as connection:

        connection.execute(
            text(
                """
                ALTER TABLE agents
                ADD COLUMN execution_credential_id INTEGER NULL
                """
            )
        )


    print(
        "      coluna criada."
    )


# ============================================================
# 5 - FK AGENT -> VAULT
# ============================================================

def garantir_fk_agent_credential() -> None:
    """
    Cria a Foreign Key para vault_credentials.id.

    ON DELETE SET NULL:
        remover uma credencial não apaga o Agent.
    """

    print(
        "[5/7] Verificando FK Agent -> Vault..."
    )


    if foreign_key_existe(
        table_name=AGENTS_TABLE,
        constrained_column="execution_credential_id",
        referred_table=VAULT_TABLE,
    ):

        print(
            "      FK já existe."
        )

        return


    with engine.begin() as connection:

        connection.execute(
            text(
                f"""
                ALTER TABLE agents
                ADD CONSTRAINT {AGENT_CREDENTIAL_FK_NAME}
                FOREIGN KEY (execution_credential_id)
                REFERENCES vault_credentials(id)
                ON DELETE SET NULL
                """
            )
        )


    print(
        "      FK criada."
    )


# ============================================================
# 6 - ÍNDICES DO VAULT
# ============================================================

def garantir_indices_vault() -> None:
    """
    Cria índices usados para separar rapidamente:
        automation/device
        generic/windows
    """

    print(
        "[6/7] Verificando índices do Vault..."
    )


    if not indice_existe(
        table_name=VAULT_TABLE,
        index_name=VAULT_SCOPE_INDEX_NAME,
    ):

        with engine.begin() as connection:

            connection.execute(
                text(
                    f"""
                    CREATE INDEX {VAULT_SCOPE_INDEX_NAME}
                    ON vault_credentials (scope)
                    """
                )
            )


        print(
            "      índice de scope criado."
        )

    else:

        print(
            "      índice de scope já existe."
        )


    if not indice_existe(
        table_name=VAULT_TABLE,
        index_name=VAULT_TYPE_INDEX_NAME,
    ):

        with engine.begin() as connection:

            connection.execute(
                text(
                    f"""
                    CREATE INDEX {VAULT_TYPE_INDEX_NAME}
                    ON vault_credentials (credential_type)
                    """
                )
            )


        print(
            "      índice de credential_type criado."
        )

    else:

        print(
            "      índice de credential_type já existe."
        )


# ============================================================
# 7 - ÍNDICE DO AGENT
# ============================================================

def garantir_indice_agent_credential() -> None:
    """
    Cria índice para consultas por credencial associada.
    """

    print(
        "[7/7] Verificando índice do Agent..."
    )


    if indice_existe(
        table_name=AGENTS_TABLE,
        index_name=AGENT_CREDENTIAL_INDEX_NAME,
    ):

        print(
            "      índice já existe."
        )

        return


    with engine.begin() as connection:

        connection.execute(
            text(
                f"""
                CREATE INDEX {AGENT_CREDENTIAL_INDEX_NAME}
                ON agents (execution_credential_id)
                """
            )
        )


    print(
        "      índice criado."
    )


# ============================================================
# VALIDAÇÃO FINAL
# ============================================================

def validar_resultado() -> None:
    """
    Confirma que o banco terminou com as estruturas essenciais.
    """

    print()
    print(
        "Validando estrutura final..."
    )


    vault_columns = obter_colunas(
        VAULT_TABLE
    )


    agent_columns = obter_colunas(
        AGENTS_TABLE
    )


    erros = []


    for column_name in (
        "scope",
        "credential_type",
        "folder_id",
    ):

        if column_name not in vault_columns:

            erros.append(
                f"vault_credentials.{column_name} ausente"
            )


    folder_column = vault_columns.get(
        "folder_id"
    )


    if (
        folder_column
        and
        not folder_column.get(
            "nullable",
            True,
        )
    ):

        erros.append(
            "vault_credentials.folder_id continua NOT NULL"
        )


    if (
        "execution_credential_id"
        not in agent_columns
    ):

        erros.append(
            "agents.execution_credential_id ausente"
        )


    if not foreign_key_existe(
        table_name=AGENTS_TABLE,
        constrained_column="execution_credential_id",
        referred_table=VAULT_TABLE,
    ):

        erros.append(
            "FK agents.execution_credential_id -> "
            "vault_credentials.id ausente"
        )


    with engine.connect() as connection:

        invalid_scope_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM vault_credentials
                WHERE scope IS NULL
                   OR BTRIM(scope) = ''
                """
            )
        ).scalar_one()


        invalid_type_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM vault_credentials
                WHERE credential_type IS NULL
                   OR BTRIM(credential_type) = ''
                """
            )
        ).scalar_one()


    if invalid_scope_count:

        erros.append(
            f"{invalid_scope_count} credencial(is) sem scope"
        )


    if invalid_type_count:

        erros.append(
            f"{invalid_type_count} credencial(is) sem credential_type"
        )


    if erros:

        raise RuntimeError(
            "A migration terminou com inconsistências:\n- "
            +
            "\n- ".join(
                erros
            )
        )


    print(
        "[OK] Estrutura final validada."
    )


# ============================================================
# EXECUÇÃO
# ============================================================

def executar_migracao() -> None:
    """
    Executa a evolução incremental e idempotente do schema.
    """

    print()
    print(
        "="
        *
        72
    )

    print(
        "DUET CORE - MIGRAÇÃO DE CREDENCIAIS DE DISPOSITIVO"
    )

    print(
        "="
        *
        72
    )

    print()


    validar_pre_requisitos()


    print(
        f"Banco detectado: {obter_dialeto()}"
    )

    print()


    garantir_scope()

    garantir_credential_type()

    permitir_device_sem_pasta()

    garantir_execution_credential_id()

    garantir_fk_agent_credential()

    garantir_indices_vault()

    garantir_indice_agent_credential()


    validar_resultado()


    print()
    print(
        "="
        *
        72
    )

    print(
        "MIGRAÇÃO CONCLUÍDA COM SUCESSO"
    )

    print(
        "="
        *
        72
    )

    print()

    print(
        "Credenciais existentes:"
    )

    print(
        '  scope = "automation"'
    )

    print(
        '  credential_type = "generic"'
    )

    print()

    print(
        "Nenhuma credencial foi apagada."
    )

    print(
        "Nenhum segredo foi descriptografado."
    )

    print(
        "Nenhum Robot, Schedule ou Execution foi alterado."
    )

    print()


if __name__ == "__main__":

    executar_migracao()
