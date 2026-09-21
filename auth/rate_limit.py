# ============================================================
# AUTH - RATE LIMIT
# ============================================================
#
# Responsabilidade deste módulo:
#
#     - centralizar a política de proteção contra tentativas
#       repetidas de autenticação;
#     - normalizar username e IP;
#     - consultar bloqueios;
#     - registrar falhas de forma segura no PostgreSQL;
#     - ativar o bloqueio após o limite configurado;
#     - limpar o estado após autenticação bem-sucedida.
#
# A persistência utiliza PostgreSQL.
#
# A chave lógica do controle é:
#
#     username + ip_address
#
# O módulo NÃO:
#
#     - valida senha;
#     - autentica usuário;
#     - cria sessão;
#     - cria Bearer Token;
#     - interpreta X-Forwarded-For;
#     - grava cookies.
#
# Essas responsabilidades permanecem em suas respectivas
# camadas.
# ============================================================

from datetime import datetime, timedelta

# case:
#     permite decidir atomicamente, dentro do PostgreSQL,
#     quando o contador deve ser reiniciado e quando o
#     bloqueio deve ser ativado.
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models import AuthRateLimit


# ============================================================
# POLÍTICA DO RATE LIMIT
# ============================================================

MAX_TENTATIVAS_AUTH = 5

DURACAO_BLOQUEIO_MINUTOS = 15


# ============================================================
# NORMALIZAR USERNAME
# ============================================================

def normalizar_username_rate_limit(
    username: str,
) -> str:
    """
    Normaliza o username utilizado como parte da chave
    lógica do rate limit.

    Regras:

        - remove espaços das extremidades;
        - converte para minúsculas.

    Exemplos:

        "Admin"   -> "admin"
        " admin " -> "admin"
    """

    return username.strip().lower()


# ============================================================
# NORMALIZAR IP
# ============================================================

def normalizar_ip_rate_limit(
    ip_origem: str | None,
) -> str:
    """
    Normaliza o endereço IP utilizado pelo rate limit.

    Caso o endereço não esteja disponível, utiliza "unknown".

    IMPORTANTE:

    Este módulo não interpreta X-Forwarded-For ou outros
    cabeçalhos de proxy.

    A decisão sobre qual IP é confiável pertence à camada
    HTTP / infraestrutura.
    """

    if not ip_origem:
        return "unknown"

    ip_normalizado = ip_origem.strip()

    if not ip_normalizado:
        return "unknown"

    return ip_normalizado


# ============================================================
# CALCULAR FIM DO BLOQUEIO
# ============================================================

def calcular_bloqueio_ate(
    agora: datetime | None = None,
) -> datetime:
    """
    Calcula o instante em que o bloqueio deverá terminar.

    O parâmetro 'agora' é opcional para permitir testes
    determinísticos.
    """

    momento_atual = (
        agora
        if agora is not None
        else datetime.utcnow()
    )

    return (
        momento_atual
        + timedelta(
            minutes=DURACAO_BLOQUEIO_MINUTOS
        )
    )


# ============================================================
# VERIFICAR DATA DE BLOQUEIO
# ============================================================

def bloqueio_esta_ativo(
    bloqueado_ate: datetime | None,
    agora: datetime | None = None,
) -> bool:
    """
    Retorna True quando bloqueado_ate ainda estiver no futuro.

    Retorna False quando:

        - não existe bloqueio;
        - o bloqueio já expirou.
    """

    if bloqueado_ate is None:
        return False

    momento_atual = (
        agora
        if agora is not None
        else datetime.utcnow()
    )

    return bloqueado_ate > momento_atual


# ============================================================
# CONSULTAR ESTADO
# ============================================================

def obter_estado_rate_limit(
    db: Session,
    username: str,
    ip_origem: str | None,
) -> AuthRateLimit | None:
    """
    Busca o registro de rate limit correspondente à combinação:

        username normalizado + IP normalizado

    Nenhuma alteração é realizada no banco.
    """

    username_normalizado = (
        normalizar_username_rate_limit(
            username
        )
    )

    ip_normalizado = (
        normalizar_ip_rate_limit(
            ip_origem
        )
    )

    return db.execute(
        select(AuthRateLimit).where(
            AuthRateLimit.username
            == username_normalizado,

            AuthRateLimit.ip_address
            == ip_normalizado,
        )
    ).scalar_one_or_none()

# ============================================================
# CONSULTAR BLOQUEIO ATIVO
# ============================================================

def obter_bloqueio_ativo(
    db: Session,
    username: str,
    ip_origem: str | None,
    agora: datetime | None = None,
) -> datetime | None:
    """
    Retorna a data/hora final do bloqueio quando a combinação
    username + IP estiver atualmente bloqueada.

    Retorna None quando:

        - não existe registro;
        - ainda não existe bloqueio;
        - o bloqueio já expirou.

    Quando encontra um bloqueio expirado, remove o estado
    anterior para que a próxima falha inicie um novo ciclo.
    """

    momento_atual = (
        agora
        if agora is not None
        else datetime.utcnow()
    )

    estado = obter_estado_rate_limit(
        db=db,
        username=username,
        ip_origem=ip_origem,
    )

    if estado is None:
        return None

    # --------------------------------------------------------
    # BLOQUEIO AINDA ATIVO
    # --------------------------------------------------------

    if bloqueio_esta_ativo(
        bloqueado_ate=estado.blocked_until,
        agora=momento_atual,
    ):
        return estado.blocked_until

    # --------------------------------------------------------
    # BLOQUEIO EXPIRADO
    # --------------------------------------------------------
    #
    # Somente registros que chegaram efetivamente ao estado
    # bloqueado são removidos aqui.
    #
    # Se blocked_until for None, ainda existem falhas válidas
    # sendo contabilizadas e o registro deve permanecer.
    # --------------------------------------------------------

    if estado.blocked_until is not None:
        db.delete(estado)
        db.commit()

    return None


# ============================================================
# VERIFICAR BLOQUEIO
# ============================================================

def autenticacao_esta_bloqueada(
    db: Session,
    username: str,
    ip_origem: str | None,
    agora: datetime | None = None,
) -> bool:
    """
    Retorna True quando existe bloqueio ativo para a combinação
    username + IP.

    Esta função permanece como uma interface simples para os
    pontos que precisam apenas saber se existe bloqueio.
    """

    return (
        obter_bloqueio_ativo(
            db=db,
            username=username,
            ip_origem=ip_origem,
            agora=agora,
        )
        is not None
    )


# ============================================================
# CALCULAR RETRY-AFTER
# ============================================================

def calcular_retry_after_segundos(
    bloqueado_ate: datetime,
    agora: datetime | None = None,
) -> int:
    """
    Calcula quantos segundos ainda faltam para o fim do bloqueio.

    O resultado pode ser utilizado diretamente no header HTTP:

        Retry-After: <segundos>

    Retorna no mínimo 1 segundo enquanto um bloqueio estiver
    sendo tratado como ativo.
    """

    momento_atual = (
        agora
        if agora is not None
        else datetime.utcnow()
    )

    segundos_restantes = (
        bloqueado_ate - momento_atual
    ).total_seconds()

    if segundos_restantes <= 1:
        return 1

    # Arredondamento para cima evita liberar o cliente alguns
    # milissegundos antes do término efetivo do bloqueio.
    return int(segundos_restantes) + 1
# ============================================================
# REGISTRAR FALHA
# ============================================================

def registrar_falha_autenticacao(
    db: Session,
    username: str,
    ip_origem: str | None,
    agora: datetime | None = None,
) -> dict:
    """
    Registra uma falha de autenticação de forma atômica.

    A operação utiliza UPSERT nativo do PostgreSQL:

        INSERT ... ON CONFLICT DO UPDATE

    O PostgreSQL executa atomicamente:

        - criação do primeiro registro;
        - incremento do contador;
        - reinício de uma sequência antiga de falhas;
        - ativação do bloqueio;
        - atualização dos timestamps.

    Uma sequência de falhas é considerada antiga quando
    last_failed_at ultrapassa a janela configurada de
    DURACAO_BLOQUEIO_MINUTOS.

    Isso evita que, por exemplo, quatro falhas ocorridas há
    vários dias sejam somadas a uma nova falha de hoje.

    Retorno:

        {
            "failed_attempts": int,
            "blocked": bool,
            "blocked_until": datetime | None,
        }
    """

    momento_atual = (
        agora
        if agora is not None
        else datetime.utcnow()
    )

    username_normalizado = (
        normalizar_username_rate_limit(
            username
        )
    )

    ip_normalizado = (
        normalizar_ip_rate_limit(
            ip_origem
        )
    )

    # --------------------------------------------------------
    # JANELA DA SEQUÊNCIA DE FALHAS
    # --------------------------------------------------------
    #
    # Se a última falha estiver antes deste instante, a
    # sequência anterior é considerada expirada.
    # --------------------------------------------------------

    limite_sequencia = (
        momento_atual
        - timedelta(
            minutes=DURACAO_BLOQUEIO_MINUTOS
        )
    )

    # --------------------------------------------------------
    # EXPRESSÃO BASE DO UPSERT
    # --------------------------------------------------------

    comando = insert(
        AuthRateLimit
    ).values(
        username=username_normalizado,
        ip_address=ip_normalizado,
        failed_attempts=1,
        last_failed_at=momento_atual,
        blocked_until=None,
        created_at=momento_atual,
        updated_at=momento_atual,
    )

    # --------------------------------------------------------
    # NOVO CONTADOR
    # --------------------------------------------------------
    #
    # Caso a sequência anterior tenha ficado inativa por mais
    # de 15 minutos, esta tentativa começa novamente em 1.
    #
    # Caso contrário, incrementamos o contador existente.
    #
    # A expressão é executada pelo próprio PostgreSQL.
    # --------------------------------------------------------

    novas_tentativas = case(
        (
            AuthRateLimit.last_failed_at.is_(None),
            1,
        ),
        (
            AuthRateLimit.last_failed_at < limite_sequencia,
            1,
        ),
        else_=AuthRateLimit.failed_attempts + 1,
    )

    # --------------------------------------------------------
    # NOVO BLOCKED_UNTIL
    # --------------------------------------------------------
    #
    # Se a sequência anterior expirou, não carregamos um
    # bloqueio antigo para a nova sequência.
    #
    # Se esta tentativa atingir o limite, o bloqueio é criado
    # dentro do MESMO UPDATE que altera failed_attempts.
    #
    # Se já existir um bloqueio ainda pertencente à sequência
    # atual, preservamos o horário original para não estender
    # o bloqueio a cada requisição.
    # --------------------------------------------------------

    novo_blocked_until = case(
        (
            AuthRateLimit.last_failed_at.is_(None),
            None,
        ),
        (
            AuthRateLimit.last_failed_at < limite_sequencia,
            None,
        ),
        (
            AuthRateLimit.blocked_until.is_not(None),
            AuthRateLimit.blocked_until,
        ),
        (
            novas_tentativas >= MAX_TENTATIVAS_AUTH,
            calcular_bloqueio_ate(
                momento_atual
            ),
        ),
        else_=None,
    )

    # --------------------------------------------------------
    # UPSERT ATÔMICO
    # --------------------------------------------------------
    #
    # A UniqueConstraint:
    #
    #     username + ip_address
    #
    # garante que requisições concorrentes para a mesma chave
    # sejam serializadas pelo PostgreSQL durante o conflito.
    #
    # Contador e blocked_until são calculados no mesmo UPDATE.
    # --------------------------------------------------------

    comando = comando.on_conflict_do_update(
        index_elements=[
            AuthRateLimit.username,
            AuthRateLimit.ip_address,
        ],
        set_={
            "failed_attempts": novas_tentativas,
            "last_failed_at": momento_atual,
            "blocked_until": novo_blocked_until,
            "updated_at": momento_atual,
        },
    ).returning(
        AuthRateLimit.failed_attempts,
        AuthRateLimit.blocked_until,
    )

    resultado = db.execute(
        comando
    ).one()

    failed_attempts = resultado.failed_attempts
    blocked_until = resultado.blocked_until

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------
    #
    # O UPSERT inteiro é confirmado em uma única transação.
    #
    # Não existe mais um segundo UPDATE ORM para ativar o
    # bloqueio depois do incremento.
    # --------------------------------------------------------

    db.commit()

    return {
        "failed_attempts": failed_attempts,
        "blocked": bloqueio_esta_ativo(
            bloqueado_ate=blocked_until,
            agora=momento_atual,
        ),
        "blocked_until": blocked_until,
    }
# RESET APÓS SUCESSO
# ============================================================

def resetar_rate_limit_autenticacao(
    db: Session,
    username: str,
    ip_origem: str | None,
) -> None:
    """
    Remove o histórico de falhas da combinação username + IP.

    Deve ser chamado somente depois que a autenticação tiver
    sido validada com sucesso.

    O DELETE é executado diretamente no PostgreSQL e funciona
    mesmo quando não existe registro.
    """

    username_normalizado = (
        normalizar_username_rate_limit(
            username
        )
    )

    ip_normalizado = (
        normalizar_ip_rate_limit(
            ip_origem
        )
    )

    db.execute(
        delete(AuthRateLimit).where(
            AuthRateLimit.username
            == username_normalizado,

            AuthRateLimit.ip_address
            == ip_normalizado,
        )
    )

    db.commit()