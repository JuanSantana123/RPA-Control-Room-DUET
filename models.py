# Importa os tipos de coluna e recursos necessários
# para definir as tabelas do banco de dados.
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    Numeric,
    Text,
    Boolean,
    UniqueConstraint
)

# Importa a classe Base usada pelo SQLAlchemy
# para registrar os modelos do banco.
from database import Base

# Importa datetime para registrar a data e hora
# de criação dos usuários.
from datetime import datetime

# ============================================================
# AGENT
# ============================================================

class Agent(Base):

    __tablename__ = "agents"

    agent_id = Column(
        String,
        primary_key=True,
        index=True
    )


    # ========================================================
    # ========================================================
    # PROTEÇÃO DO TOKEN DO AGENT
    # ========================================================
    #
    # O token original NÃO é persistido no banco.
    #
    # agent_token_hash:
    #     impressão digital SHA-256 utilizada para localizar
    #     e autenticar o Agent sem armazenar plaintext.
    #
    # agent_token_encrypted:
    #     versão recuperável protegida por Fernet, utilizada
    #     somente quando o Control Room precisa enviar a
    #     credencial original ao próprio Agent.
    # ========================================================

    agent_token_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    agent_token_encrypted = Column(
        Text,
        nullable=False,
    )

    name = Column(
        String,
        nullable=False
    )

    host = Column(
        String,
        nullable=True
    )

    port = Column(
        Integer,
        nullable=False
    )

    rpa_directory = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="pending"
    )

    # ========================================================
    # AMBIENTE OPERACIONAL DO AGENT
    # ========================================================
    #
    # Define em qual ambiente esta máquina pode ser utilizada.
    #
    # Valores atualmente suportados:
    #
    # development:
    #     Desenvolvimento / Homologação.
    #
    # production:
    #     Produção.
    #
    # Nesta primeira etapa o campo é apenas classificatório.
    # As regras que impedirão Robots de Produção de utilizarem
    # Agents de Desenvolvimento serão implementadas depois.
    # ========================================================

    environment = Column(
        String,
        nullable=False,
        default="development",
        index=True
    )

    last_heartbeat = Column(
    DateTime,
    nullable=True
    )
        # Status atual da sessão Windows do Agent.
    #
    # Exemplos:
    # - unknown
    # - ready
    # - error
    session_status = Column(
        String,
        nullable=False,
        default="unknown"
    )

    # Usuário atualmente associado à sessão Windows.
    #
    # Pode ser nulo quando não existe uma sessão
    # Windows identificada.
    username = Column(
    String,
    nullable=True
    )

    # Indica se o Agent continua cadastrado e disponível
    # para utilização pelo Control Room.
    #
    # 1 = Agent ativo
    # 0 = Agent removido logicamente
    #
    # A exclusão lógica permite remover o Agent da operação
    # sem apagar seu registro do banco, preservando assim
    # o histórico das execuções associadas a ele.
    is_active = Column(
        Integer,
        nullable=False,
        default=1
    )


# ============================================================
# PASTAS DE ROBÔS
# ============================================================

class RobotFolder(Base):

    __tablename__ = "robot_folders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    parent_id = Column(
        Integer,
        ForeignKey("robot_folders.id"),
        nullable=True
    )


# ============================================================
# PASTAS DE DESENVOLVIMENTO
# ============================================================

class DevelopmentFolder(Base):
    """
    Representa uma pasta utilizada para organizar os projetos
    dentro da área de Desenvolvimento do DUET CORE.

    Esta estrutura é separada de RobotFolder porque:

    - DevelopmentFolder organiza workspaces editáveis;
    - RobotFolder organiza robôs publicados / produção.

    Uma pasta pode possuir outra pasta como pai, permitindo
    uma árvore com quantidade ilimitada de níveis.

    Exemplo:

    Financeiro
    ├── Faturamento
    │   ├── Primeiro Faturamento
    │   └── Correção de Valores
    └── Cobrança
    """

    __tablename__ = "development_folders"

    # Identificador único da pasta.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome exibido na árvore de Desenvolvimento.
    name = Column(
        String,
        nullable=False
    )

    # Pasta pai.
    #
    # NULL significa que esta pasta está na raiz.
    parent_id = Column(
        Integer,
        ForeignKey("development_folders.id"),
        nullable=True,
        index=True
    )

    # Usuário do Control Room que criou a pasta.
    #
    # Mantemos esta informação para auditoria.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Data de criação.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Data da última alteração.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Exclusão lógica.
    #
    # 1 = pasta ativa
    # 0 = pasta removida
    #
    # Não apagamos fisicamente de imediato para preservar
    # rastreabilidade e referências futuras.
    is_active = Column(
        Integer,
        nullable=False,
        default=1
    )

# ============================================================
# ESTÁGIOS DO WORKFLOW - DESENVOLVIMENTO
# ============================================================

class DevelopmentStage(Base):
    """
    Representa uma coluna/etapa do Workflow de Desenvolvimento.

    O code é o identificador técnico estável utilizado pelo backend.

    Exemplos:
        BACKLOG
        IN_DEVELOPMENT
        READY_FOR_TEST
        IN_TEST
        HOMOLOGATION
        APPROVED
        PUBLISHED

    O name é somente o nome amigável exibido no Kanban.
    """

    __tablename__ = "development_stages"

    # Identificador interno do estágio.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Identificador técnico estável.
    #
    # Regras de negócio devem utilizar code e nunca depender
    # diretamente do ID numérico do estágio.
    code = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    # Nome amigável exibido no Kanban.
    name = Column(
        String,
        nullable=False
    )

    # Ordem visual da coluna no quadro.
    position = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True
    )

    # Permite futuramente desativar um estágio sem remover
    # registros históricos associados a ele.
    is_active = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )

    # Data de criação do estágio.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
# ============================================================
# PROJETOS DE AUTOMAÇÃO - DESENVOLVIMENTO
# ============================================================

class AutomationProject(Base):
    """
    Representa um projeto editável dentro da área
    Desenvolvimento do DUET CORE.

    AutomationProject NÃO é o mesmo que Robot.

    AutomationProject:
        - código-fonte editável;
        - workspace;
        - desenvolvimento;
        - testes;
        - futuras alterações de uma automação existente.

    Robot:
        - automação publicada;
        - versão disponível para execução;
        - utilizada por Agent, schedules e executions.

    Um projeto pode nascer de duas maneiras:

    1. Automação nova:
       base_robot_id = NULL
       base_version = NULL

    2. Alteração de automação já publicada:
       base_robot_id = ID do Robot
       base_version = versão utilizada como base
    """

    __tablename__ = "automation_projects"

    # Identificador único do projeto.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome do projeto exibido na área de Desenvolvimento
    # e no DUET Studio.
    name = Column(
        String,
        nullable=False,
        index=True
    )

    # Descrição opcional da automação.
    description = Column(
        Text,
        nullable=True
    )

    # Pasta de Desenvolvimento onde o projeto está localizado.
    #
    # NULL permite que um projeto fique diretamente
    # na raiz da área Desenvolvimento.
    folder_id = Column(
        Integer,
        ForeignKey("development_folders.id"),
        nullable=True,
        index=True
    )

    # ========================================================
    # STATUS TÉCNICO DO PROJETO
    # ========================================================
    #
    # IMPORTANTE:
    #
    # Este campo NÃO representa a coluna do Kanban.
    #
    # Ele continua preservado porque já é utilizado pelo
    # Desenvolvimento para representar o estado técnico do
    # projeto, por exemplo:
    #
    # draft
    # modified
    # published
    #
    # O Workflow/Kanban utiliza current_stage_id.
    # ========================================================

    status = Column(
        String,
        nullable=False,
        default="draft",
        index=True
    )


    # ========================================================
    # WORKFLOW / KANBAN
    # ========================================================
    #
    # Identifica o estágio atual do projeto.
    #
    # Exemplos:
    #
    # BACKLOG
    # EM DESENVOLVIMENTO
    # PRONTO PARA TESTE
    # ...
    #
    # O vínculo é feito pela tabela development_stages.
    #
    # Nesta primeira migration permanece nullable=True porque
    # ainda vamos adaptar a criação de projetos no backend.
    #
    # Depois que development.py estiver utilizando o Workflow,
    # tornaremos esta coluna obrigatória no PostgreSQL.
    # ========================================================

    current_stage_id = Column(
        Integer,
        ForeignKey("development_stages.id"),
        nullable=True,
        index=True
    )

    # Robô publicado utilizado como origem deste projeto.
    #
    # NULL:
    #     automação completamente nova.
    #
    # Preenchido:
    #     projeto criado para alterar uma automação
    #     que já possui versão publicada.
    base_robot_id = Column(
        Integer,
        ForeignKey("robots.id"),
        nullable=True,
        index=True
    )

    # ========================================================
    # NOME HISTÓRICO DO ROBOT DE ORIGEM
    # ========================================================
    #
    # Guarda o nome do Robot exatamente quando ele é utilizado
    # como origem de um projeto de Desenvolvimento.
    #
    # Diferentemente de base_robot_id, este campo é um snapshot
    # histórico e NÃO depende da existência futura do Robot.
    #
    # Isso permite preservar:
    #
    #     Robô de origem
    #     FaturamentoNovo.zip
    #
    # mesmo que posteriormente o Robot seja excluído.
    #
    # NULL:
    #     projeto criado do zero ou registro legado cuja origem
    #     não pôde ser recuperada.
    # ========================================================

    base_robot_name = Column(
        String,
        nullable=True
    )


    # Versão publicada que originou o workspace atual.
    #
    # Exemplo:
    #
    # Robot:
    #     Primeiro Faturamento
    #     versão 4
    #
    # Projeto criado para alteração:
    #     base_robot_id = 12
    #     base_version = 4
    #
    # Quando uma nova versão for publicada futuramente,
    # poderemos atualizar esta referência.
    base_version = Column(
        Integer,
        nullable=True
    )


    # ========================================================
    # PLANEJAMENTO DO CARD / KANBAN
    # ========================================================
    #
    # Estes dados pertencem individualmente a este
    # AutomationProject.
    #
    # Portanto cada card do Kanban possui seus próprios:
    #
    # - responsáveis;
    # - datas;
    # - horas de esforço.
    #
    # Todos permanecem opcionais para não afetar projetos
    # antigos nem obrigar seu preenchimento na criação.
    # ========================================================


    # --------------------------------------------------------
    # RESPONSÁVEL FUNCIONAL
    # --------------------------------------------------------
    #
    # Usuário do DUET responsável pela parte funcional
    # da demanda.
    #
    # NULL significa que ainda não foi definido.
    #
    # ON DELETE SET NULL preserva o projeto caso futuramente
    # o usuário associado seja removido fisicamente.
    # --------------------------------------------------------

    functional_responsible_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )


    # --------------------------------------------------------
    # RESPONSÁVEL TÉCNICO
    # --------------------------------------------------------
    #
    # Usuário do DUET responsável pelo desenvolvimento
    # técnico da demanda.
    #
    # Este campo é independente do Checkout.
    #
    # Responsável técnico:
    #     quem responde pelo desenvolvimento.
    #
    # Checkout:
    #     quem possui o bloqueio de edição neste momento.
    # --------------------------------------------------------

    technical_responsible_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )


    # --------------------------------------------------------
    # DATA DE INÍCIO
    # --------------------------------------------------------
    #
    # Data planejada/registrada para início da demanda.
    #
    # Armazenamos somente a data, sem horário.
    # --------------------------------------------------------

    start_date = Column(
        Date,
        nullable=True
    )


    # --------------------------------------------------------
    # PREVISÃO DE CONCLUSÃO
    # --------------------------------------------------------
    #
    # Data prevista para conclusão da demanda.
    #
    # Não representa a data real de publicação.
    # --------------------------------------------------------

    due_date = Column(
        Date,
        nullable=True
    )


    # --------------------------------------------------------
    # HORAS DE ESFORÇO DO CARD
    # --------------------------------------------------------
    #
    # Valor informado manualmente para ESTE projeto/card.
    #
    # Exemplos:
    #
    #     8
    #     16
    #     7.5
    #
    # Não existe cronômetro ou contabilização automática.
    # --------------------------------------------------------

    effort_hours = Column(
        Numeric(
            8,
            2
        ),
        nullable=True
    )
    # Usuário responsável pela criação do projeto.
    #
    # O frontend NÃO envia este valor arbitrariamente.
    # O backend deverá obter o usuário através da sessão
    # autenticada do Control Room.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Data de criação do projeto.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Última alteração do projeto.
    #
    # O SQLAlchemy atualizará automaticamente este campo
    # quando o registro for modificado pela aplicação.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ========================================================
    # LIXEIRA / EXCLUSÃO LÓGICA
    # ========================================================
    #
    # deleted_at:
    #     Registra quando o projeto foi enviado para a Lixeira.
    #
    #     NULL:
    #         projeto não está atualmente excluído.
    #
    # deleted_by:
    #     Usuário que enviou o projeto para a Lixeira.
    #
    #     É nullable porque os projetos já existentes foram
    #     criados antes da implementação da Lixeira.
    #
    # Esses campos representam a exclusão ATUAL do projeto.
    #
    # Quando o projeto for restaurado, futuramente o backend
    # limpará deleted_at/deleted_by e registrará a restauração
    # separadamente nos logs/auditoria.
    # ========================================================

    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    deleted_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )


    # ========================================================
    # ESTADO ATIVO
    # ========================================================
    #
    # 1 = projeto ativo
    # 0 = projeto na Lixeira
    #
    # A exclusão permanente será uma operação diferente:
    #
    #     - remove o workspace físico;
    #     - remove definitivamente o registro do projeto.
    #
    # Portanto is_active = 0 NÃO significa que o projeto foi
    # apagado permanentemente.
    # ========================================================

    is_active = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )



# ============================================================
# HISTÓRICO DE MOVIMENTAÇÃO DO WORKFLOW
# ============================================================

class ProjectStageHistory(Base):
    """
    Registra cada movimentação real de um AutomationProject
    entre estágios do Workflow.

    Exemplo:

        EM DESENVOLVIMENTO
            ->
        PRONTO PARA TESTE

    O histórico informa:
        - qual projeto foi movimentado;
        - estágio anterior;
        - novo estágio;
        - usuário responsável;
        - momento da alteração.
    """

    __tablename__ = "project_stage_history"

    # Identificador interno do evento.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Projeto que foi movimentado.
    #
    # ondelete="CASCADE" é importante porque o DUET já possui
    # exclusão permanente de AutomationProject.
    #
    # Se o projeto for realmente apagado de forma permanente,
    # seus registros internos de workflow também são removidos.
    project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Estágio anterior.
    #
    # Pode ser NULL para situações em que ainda não exista
    # estágio anterior conhecido.
    from_stage_id = Column(
        Integer,
        ForeignKey("development_stages.id"),
        nullable=True,
        index=True
    )

    # Novo estágio do projeto.
    to_stage_id = Column(
        Integer,
        ForeignKey("development_stages.id"),
        nullable=False,
        index=True
    )

    # Usuário do DUET que realizou a movimentação.
    changed_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Momento da movimentação.
    changed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
# ============================================================
# ============================================================
# CHECKOUT DE PROJETOS - DESENVOLVIMENTO
# ============================================================

class ProjectCheckout(Base):
    """
    Representa o Checkout exclusivo de um projeto.

    Um projeto pode possuir apenas um Checkout ativo por vez.
    O Checkout pertence ao usuário e permanece ativo até
    Checkin ou Force Release.
    """

    __tablename__ = "project_checkouts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # UNIQUE garante somente um Checkout ativo por projeto.
    project_id = Column(
        Integer,
        ForeignKey("automation_projects.id"),
        nullable=False,
        unique=True
    )

    # Usuário proprietário do Checkout.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Momento em que o Checkout foi realizado.
    # Não existe expiração automática.
    checked_out_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )





# ============================================================
# COMENTÁRIOS DOS PROJETOS - KANBAN
# ============================================================

class ProjectComment(Base):
    """
    Representa um comentário livre associado a um
    AutomationProject.

    Um projeto pode possuir qualquer quantidade de comentários.

    Cada comentário registra:

    - projeto;
    - autor;
    - conteúdo;
    - criação;
    - última alteração.
    """

    __tablename__ = "project_comments"


    # Identificador único do comentário.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    # Projeto/card ao qual o comentário pertence.
    #
    # ON DELETE CASCADE:
    #     se o projeto for realmente excluído de forma
    #     permanente, seus comentários também são removidos.
    project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )


    # Usuário do DUET que escreveu o comentário.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )


    # Texto livre do comentário.
    content = Column(
        Text,
        nullable=False
    )


    # Momento original da criação.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )


    # Momento da última alteração.
    #
    # Inicialmente será igual ao momento de criação e será
    # atualizado automaticamente caso futuramente permitamos
    # edição do comentário.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
# ============================================================
# BIBLIOTECAS REUTILIZÁVEIS
# ============================================================

class LibraryFolder(Base):
    """
    Representa uma pasta organizacional do catálogo global
    de Bibliotecas do DUET CORE.

    Esta árvore é independente da estrutura Python existente
    DENTRO de cada biblioteca.

    Exemplo de catálogo:

        Bibliotecas
        └── Corporativo
            └── Financeiro
                └── Financeiro Core

    parent_id:
        NULL -> pasta na raiz do módulo Bibliotecas.

        ID preenchido -> subpasta de outra LibraryFolder.

    A autorreferência permite quantidade ilimitada de níveis.
    """

    __tablename__ = "library_folders"

    # Identificador único da pasta.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome amigável exibido na árvore global de Bibliotecas.
    name = Column(
        String,
        nullable=False,
        index=True
    )

    # Pasta pai.
    #
    # ON DELETE SET NULL evita apagar bibliotecas/pastas filhas
    # caso futuramente uma pasta seja removida fisicamente.
    parent_id = Column(
        Integer,
        ForeignKey(
            "library_folders.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # Usuário que criou a pasta.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Data de criação.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Data da última alteração.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Exclusão lógica.
    #
    # 1 = pasta disponível na árvore.
    # 0 = pasta desativada/oculta.
    is_active = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )


class Library(Base):
    """
    Representa uma biblioteca reutilizável gerenciada pelo DUET CORE.

    A biblioteca possui uma identidade estável, enquanto cada publicação
    de código gera um registro imutável em LibraryVersion.

    Exemplos:

        name = "Financeiro"
        import_name = "financeiro"

        Uso dentro de uma automação:

            from financeiro.pagamentos import gerar_pagamento

    O código editável de uma biblioteca independente poderá utilizar um
    workspace próprio do módulo Bibliotecas. As versões publicadas nunca
    dependem diretamente desse workspace.
    """

    __tablename__ = "libraries"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome amigável exibido na interface.
    name = Column(
        String,
        nullable=False,
        index=True
    )

    # Nome técnico utilizado nos imports Python.
    #
    # Deve ser único no DUET para impedir duas bibliotecas diferentes
    # de disputarem o mesmo namespace de importação.
    #
    # Exemplo:
    #     Financeiro -> financeiro
    import_name = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    description = Column(
        Text,
        nullable=True
    )

    # Pasta ORGANIZACIONAL do catálogo global de Bibliotecas.
    #
    # IMPORTANTE:
    # Isto NÃO representa uma pasta interna do pacote Python.
    #
    # Exemplo:
    #
    #     Catálogo:
    #         Corporativo / Financeiro / Financeiro Core
    #
    #     Código da biblioteca:
    #         financeiro/
    #             __init__.py
    #             pagamentos/
    #                 pix.py
    #
    # São duas estruturas diferentes.
    #
    # NULL mantém compatibilidade com bibliotecas já existentes,
    # que passam a aparecer na raiz do módulo Bibliotecas.
    folder_id = Column(
        Integer,
        ForeignKey(
            "library_folders.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # ========================================================
    # VERSÃO VIGENTE EM PRODUÇÃO
    # ========================================================
    #
    # Aponta explicitamente para a LibraryVersion que está vigente
    # em Produção para esta biblioteca.
    #
    # NULL:
    #     biblioteca ainda não possui nenhuma versão publicada.
    #
    # Preenchido:
    #     identifica a versão atual de Produção. Versões anteriores
    #     permanecem imutáveis em library_versions para histórico e
    #     para Releases antigos que ainda dependam delas.
    #
    # A publicação de uma nova versão atualiza SOMENTE este ponteiro;
    # nunca altera nem apaga a LibraryVersion anterior.
    # ========================================================
    production_version_id = Column(
        Integer,
        ForeignKey(
            "library_versions.id",
            name=(
                "fk_libraries_production_version_id_"
                "library_versions"
            ),
            ondelete="SET NULL",
            # Quebra explicitamente o ciclo de criação entre
            # libraries e library_versions em bancos novos.
            use_alter=True
        ),
        nullable=True,
        index=True
    )

    # Usuário que cadastrou a biblioteca no DUET.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Exclusão/desativação lógica.
    #
    # Uma biblioteca desativada deixa de ficar disponível para novos
    # vínculos, mas suas versões continuam preservadas para projetos
    # e Releases que já dependam delas.
    is_active = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )


class LibraryVersion(Base):
    """
    Representa uma versão publicada e imutável de uma Library.

    Uma versão pode ter duas origens:

    1. standalone
       A biblioteca foi desenvolvida diretamente no módulo Bibliotecas.

    2. robot
       O código existia dentro de uma automação publicada e foi
       publicado pelo DUET como uma biblioteca reutilizável.

    IMPORTANTE:
    Quando a origem for um Robot, a versão da biblioteca recebe seu
    próprio artefato/snapshot. Outros projetos nunca importam código
    diretamente da pasta física do Robot de origem.
    """

    __tablename__ = "library_versions"

    __table_args__ = (
        UniqueConstraint(
            "library_id",
            "version",
            name="uq_library_versions_library_version"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    library_id = Column(
        Integer,
        ForeignKey("libraries.id"),
        nullable=False,
        index=True
    )

    # Versão da biblioteca.
    #
    # Mantemos como String para suportar versionamento semântico:
    # 1.0.0, 1.1.0, 2.0.0 etc.
    version = Column(
        String,
        nullable=False,
        index=True
    )

    # Origem técnica desta versão.
    #
    # Valores previstos inicialmente:
    # - standalone
    # - robot
    source_type = Column(
        String,
        nullable=False,
        default="standalone",
        index=True
    )

    # Preenchido somente quando source_type = "robot".
    source_robot_id = Column(
        Integer,
        ForeignKey("robots.id"),
        nullable=True,
        index=True
    )

    # Versão do Robot que serviu de origem para o snapshot.
    source_robot_version = Column(
        Integer,
        nullable=True
    )

    # Caminho interno que foi publicado como biblioteca quando a origem
    # for uma automação.
    #
    # Exemplo:
    #     libs/kenan
    source_path = Column(
        String,
        nullable=True
    )

    # Caminho do artefato imutável da biblioteca.
    #
    # Exemplo:
    #     storage/libraries/12/2.0.0/library.zip
    artifact_path = Column(
        String,
        nullable=False
    )

    # Hash do artefato utilizado para garantir integridade e permitir
    # validação antes da execução.
    file_hash = Column(
        String,
        nullable=False
    )

    published_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    published_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Permite retirar uma versão da seleção para novos projetos sem
    # apagar o snapshot necessário aos projetos existentes.
    is_active = Column(
        Integer,
        nullable=False,
        default=1,
        index=True
    )


class ProjectLibraryDependency(Base):
    """
    Liga um AutomationProject a uma versão EXATA de uma biblioteca.

    Exemplo:

        Projeto A
            Financeiro -> 2.0.0

        Projeto B
            Financeiro -> 3.0.0

    O projeto não acompanha automaticamente a versão mais recente.

    Se o desenvolvedor editar a biblioteca dentro do projeto,
    ProjectLibraryDraft guarda a cópia de trabalho sem modificar
    esta LibraryVersion publicada.
    """

    __tablename__ = "project_library_dependencies"

    __table_args__ = (
        # Garante no banco que um projeto possua somente uma versão
        # publicada selecionada de cada biblioteca por vez.
        UniqueConstraint(
            "project_id",
            "library_id",
            name="uq_project_library_dependencies_project_library"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Mantemos library_id explicitamente para permitir a constraint
    # projeto + biblioteca e impedir duas versões da mesma biblioteca
    # simultaneamente no mesmo projeto.
    library_id = Column(
        Integer,
        ForeignKey("libraries.id"),
        nullable=False,
        index=True
    )

    # Versão PUBLICADA utilizada como base pelo projeto.
    #
    # Exemplo:
    #
    #     Financeiro 2.0.0
    #
    # Se existir ProjectLibraryDraft, o draft poderá conter mudanças
    # locais ainda não publicadas, mas esta referência continua apontando
    # para a última versão publicada conhecida pelo projeto.
    library_version_id = Column(
        Integer,
        ForeignKey("library_versions.id"),
        nullable=False,
        index=True
    )

    # Usuário que adicionou ou atualizou a dependência.
    added_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class ProjectLibraryDraft(Base):
    """
    Representa a cópia EDITÁVEL de uma biblioteca dentro de um
    AutomationProject.

    Exemplo:

        Financeiro 2.0.0 está publicada.

        Projeto A:
            usa Financeiro 2.0.0
            edita pagamentos.py
            -> ProjectLibraryDraft do Projeto A

        Projeto B:
            usa Financeiro 2.0.0
            edita outro arquivo
            -> outro ProjectLibraryDraft independente

    Assim uma automação nunca altera a versão 2.0.0 publicada
    nem interfere no draft de outra automação.

    Quando o projeto for publicado:

    - sem alterações:
        continua utilizando a LibraryVersion atual;

    - com alterações:
        o draft gera uma NOVA LibraryVersion;
        a versão antiga permanece intacta.
    """

    __tablename__ = "project_library_drafts"

    __table_args__ = (
        # Um projeto só pode possuir um draft ativo por biblioteca.
        UniqueConstraint(
            "project_id",
            "library_id",
            name="uq_project_library_drafts_project_library"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Projeto proprietário exclusivo desta cópia de trabalho.
    project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Biblioteca à qual o draft pertence.
    library_id = Column(
        Integer,
        ForeignKey("libraries.id"),
        nullable=False,
        index=True
    )

    # Versão publicada utilizada para criar esta cópia de trabalho.
    #
    # Biblioteca EXISTENTE:
    #     base_library_version_id -> Financeiro 2.0.0
    #
    # Biblioteca NOVA criada dentro de Desenvolvimento:
    #     base_library_version_id = NULL
    #
    # O NULL é necessário porque uma biblioteca nova ainda não possui
    # LibraryVersion até sua primeira publicação. Após a primeira
    # publicação, o projeto passa a apontar para a versão criada através
    # de ProjectLibraryDependency.
    #
    # Quando existir uma versão base, esta referência nunca muda
    # silenciosamente enquanto houver alterações pendentes no draft.
    base_library_version_id = Column(
        Integer,
        ForeignKey("library_versions.id"),
        nullable=True,
        index=True
    )

    # Caminho INTERNO do Control Room onde a cópia editável está salva.
    #
    # O frontend nunca deve escolher este caminho.
    #
    # Exemplo:
    #     workspaces/10/.duet/libraries/5/
    workspace_path = Column(
        String,
        nullable=False
    )

    # Indica se a cópia de trabalho possui diferença em relação
    # à LibraryVersion de origem.
    #
    # 0 = nenhuma alteração pendente.
    # 1 = biblioteca modificada dentro do projeto.
    is_modified = Column(
        Integer,
        nullable=False,
        default=0,
        index=True
    )

    # Usuário que criou a cópia de trabalho.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Último usuário que modificou o draft.
    #
    # Pode ficar NULL imediatamente após a criação.
    updated_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class RobotVersionLibraryDependency(Base):
    """
    Snapshot IMUTÁVEL das bibliotecas utilizadas por uma versão
    publicada de um Robot.

    O model Robot atual guarda a versão corrente como inteiro e ainda
    não possui uma tabela RobotVersion separada.

    Por isso o snapshot é identificado por:

        robot_id + robot_version + library_id

    Exemplo:

        Robot Primeiro Faturamento
        versão 7
            Financeiro 2.0.0

        Robot Primeiro Faturamento
        versão 8
            Financeiro 3.0.0

    Publicar a versão 8 NÃO altera o snapshot da versão 7.
    """

    __tablename__ = "robot_version_library_dependencies"

    __table_args__ = (
        UniqueConstraint(
            "robot_id",
            "robot_version",
            "library_id",
            name=(
                "uq_robot_version_library_dependencies_"
                "robot_version_library"
            )
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Robot publicado.
    robot_id = Column(
        Integer,
        ForeignKey("robots.id"),
        nullable=False,
        index=True
    )

    # Versão do Robot no momento da publicação.
    robot_version = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Biblioteca usada por esta versão do Robot.
    library_id = Column(
        Integer,
        ForeignKey("libraries.id"),
        nullable=False,
        index=True
    )

    # Versão EXATA e imutável da biblioteca.
    library_version_id = Column(
        Integer,
        ForeignKey("library_versions.id"),
        nullable=False,
        index=True
    )

    # Projeto que originou a Release.
    #
    # SET NULL preserva o snapshot histórico mesmo se o projeto
    # de Desenvolvimento for apagado permanentemente.
    source_project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # Usuário responsável pela publicação da Release.
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )



# ============================================================
# ROBOTS
# ============================================================

class Robot(Base):

    __tablename__ = "robots"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    filename = Column(
        String,
        nullable=False
    )

    version = Column(
        Integer,
        nullable=False,
        default=1
    )

    file_hash = Column(
        String,
        nullable=False
    )

    file_path = Column(
        String,
        nullable=False
    )

    folder_id = Column(
        Integer,
        ForeignKey("robot_folders.id"),
        nullable=True
    )


# ============================================================
# VERSÕES PUBLICADAS DE ROBOTS
# ============================================================

class RobotVersion(Base):
    """
    Representa uma versão PUBLICADA e IMUTÁVEL de um Robot.

    Robot continua sendo a identidade operacional da automação
    e mantém, por compatibilidade, o ponteiro para a versão atual.

    RobotVersion preserva cada Release individualmente:

        Robot 25
            v1 -> artefato + hash
            v2 -> artefato + hash
            v3 -> artefato + hash

    Depois de criada, uma RobotVersion não deve ser alterada
    silenciosamente pela aplicação.
    """

    __tablename__ = "robot_versions"

    # Um Robot só pode possuir uma ocorrência de cada versão.
    __table_args__ = (
        UniqueConstraint(
            "robot_id",
            "version",
            name="uq_robot_versions_robot_version"
        ),
    )

    # Identificador interno da versão publicada.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Robot ao qual esta versão pertence.
    #
    # ON DELETE CASCADE acompanha o hard delete do próprio Robot.
    # A limpeza física dos artefatos será tratada separadamente
    # pelo backend antes/depois da confirmação da operação.
    robot_id = Column(
        Integer,
        ForeignKey(
            "robots.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Número imutável da versão.
    #
    # Exemplo:
    #     1
    #     2
    #     3
    version = Column(
        Integer,
        nullable=False,
        index=True
    )

    # Nome físico do pacote publicado.
    filename = Column(
        String,
        nullable=False
    )

    # Caminho do artefato imutável desta versão.
    #
    # Releases novos utilizarão caminho relativo à raiz do
    # Control Room. Registros legados poderão temporariamente
    # manter caminho absoluto durante a migração.
    artifact_path = Column(
        String,
        nullable=False
    )

    # SHA-256 do artefato físico desta versão.
    #
    # O backend sempre deverá validar este hash antes de utilizar
    # o pacote para restauração/desenvolvimento.
    file_hash = Column(
        String,
        nullable=False
    )

    # Projeto de Desenvolvimento que originou o Release.
    #
    # Pode ser NULL para versões antigas/importadas que não tenham
    # origem conhecida.
    source_project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # Usuário responsável pela publicação.
    #
    # Nullable permite registrar versões legadas cujo autor
    # original não possa ser determinado com segurança.
    published_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # Data original da publicação quando conhecida.
    published_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    # Momento em que este registro entrou no catálogo
    # de RobotVersions do DUET.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

# ============================================================
# EXECUÇÕES
# ============================================================
class Execution(Base):

    __tablename__ = "executions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # ORIGEM DA EXECUÇÃO
    # ========================================================
    #
    # Identifica de onde esta execução foi iniciada.
    #
    # Valores atuais:
    #
    # robot
    #     Execução normal de um Robot publicado.
    #
    # development
    #     Execução temporária de um AutomationProject
    #     diretamente pela área de Desenvolvimento.
    #
    # As execuções já existentes continuam sendo "robot".
    # ========================================================

    source_type = Column(
        String,
        nullable=False,
        default="robot",
        index=True
    )

    # ========================================================
    # ROBOT PUBLICADO
    # ========================================================
    #
    # Continua preenchido normalmente para todas as execuções
    # atuais de Robots, Scheduler e fila.
    #
    # Agora é nullable porque uma execução de Desenvolvimento
    # ainda pode não possuir nenhum Robot publicado.
    # ========================================================

    robot_id = Column(
        Integer,
        ForeignKey("robots.id"),
        nullable=True
    )



     # ========================================================
    # VERSÃO EXATA DO ROBOT EXECUTADO
    # ========================================================
    #
    # Para source_type="robot", registra a versão publicada
    # exata associada a esta Execution.
    #
    # Isso é importante principalmente para Queue e Scheduler:
    # uma nova publicação do Robot não pode alterar a versão
    # que uma Execution já criada deverá executar.
    #
    # Para source_type="development", permanece NULL.
    # ========================================================

    robot_version = Column(
        Integer,
        nullable=True,
        index=True
    )
    # ========================================================
    # PROJETO DE DESENVOLVIMENTO
    # ========================================================
    #
    # Preenchido quando source_type = "development".
    #
    # Em uma execução normal de Robot permanece NULL.
    #
    # ON DELETE SET NULL permite preservar o histórico da
    # execução mesmo se o projeto for apagado permanentemente.
    # ========================================================

    project_id = Column(
        Integer,
        ForeignKey(
            "automation_projects.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    robot_name = Column(
        String,
        nullable=False
    )

    robot_filename = Column(
        String,
        nullable=False
    )

    agent_id = Column(
    String,
    ForeignKey("agents.agent_id"),
    nullable=False
)

    # Usuário do Control Room que iniciou esta execução.
    #
    # Não é enviado para o Agent.
    # Serve para manter o contexto de autorização da execução,
    # principalmente quando o RPA solicitar uma credencial do Vault.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # Identifica o agendamento que originou esta execução.
    #
    # Pode ser nulo quando a execução foi iniciada
    # manualmente pelo usuário.
    # ========================================================
    # AGENDAMENTO DE ORIGEM
    # ========================================================
    #
    # Identifica o Schedule que originou esta execução.
    #
    # A Execution é o histórico permanente da execução.
    # O Schedule é apenas a configuração responsável por
    # gerar execuções futuras.
    #
    # Portanto, excluir um Schedule NÃO pode excluir nem
    # impedir a preservação das Executions já realizadas.
    #
    # ON DELETE SET NULL garante no próprio PostgreSQL que,
    # quando o Schedule for removido, somente a referência
    # histórica schedule_id será limpa.
    #
    # schedule_run_id continua preservado para identificar
    # a ocorrência originalmente criada pelo Scheduler.
    # ========================================================

    schedule_id = Column(
        Integer,
        ForeignKey(
            "schedules.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    # Identifica de forma única uma ocorrência específica
    # de um agendamento.
    #
    # Exemplo:
    # O mesmo Schedule pode executar às 08:00, 09:00 e 10:00.
    # Cada uma dessas ocorrências terá um schedule_run_id diferente.
    #
    # Isso também permite impedir que uma mesma ocorrência
    # seja criada duas vezes pelo scheduler.
    schedule_run_id = Column(
        String,
        nullable=True,
        unique=True,
        index=True
    )


    # PID do processo Python do robô no Agent.
    # Permite identificar o processo específico
    # responsável por esta execução.
    pid = Column(
        Integer,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="running"
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    finished_at = Column(
        DateTime,
        nullable=True
    )

    error_message = Column(
        String,
        nullable=True
    )

# ============================================================
# AGENDAMENTOS
# ============================================================

class Schedule(Base):

    __tablename__ = "schedules"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    robot_id = Column(
        Integer,
        ForeignKey("robots.id"),
        nullable=False
    )

    # Usuário do Control Room que criou o agendamento.
    # O Scheduler usará esse ID quando criar a Execution.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    agent_id = Column(
        String,
        ForeignKey("agents.agent_id"),
        nullable=True
    )

    tipo = Column(
        String,
        nullable=False
    )

    data_inicio = Column(
        DateTime,
        nullable=False
    )

    horario = Column(
        String,
        nullable=False
    )

    dias_semana = Column(
        String,
        nullable=True
    )

    # Intervalo é opcional.
    # Quando desativado, o agendamento ocorre uma vez
    # no horário definido.
    intervalo_ativo = Column(
        Integer,
        nullable=False,
        default=0
    )

    intervalo_valor = Column(
        Integer,
        nullable=True
    )

    intervalo_unidade = Column(
        String,
        nullable=True
    )

    horario_fim = Column(
        String,
        nullable=True
    )

    ativo = Column(
        Integer,
        nullable=False,
        default=1
    )

    proxima_execucao = Column(
        DateTime,
        nullable=True
    )

    ultima_execucao = Column(
        DateTime,
        nullable=True
    )

    
# ============================================================
# USUÁRIOS
# ============================================================

class User(Base):
    # Define o nome da tabela que será criada no SQLite.
    __tablename__ = "users"

    # Identificador único do usuário.
    # É a chave primária da tabela.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome utilizado pelo usuário para fazer login.
    # unique=True impede dois usuários com o mesmo username.
    # nullable=False significa que esse campo é obrigatório.
    username = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # Guarda a senha de forma segura através de um hash.
    # A senha original NÃO será armazenada aqui.
    password_hash = Column(
        String,
        nullable=False
    )

    # Nome de identificação do usuário no sistema.
    # Pode ser diferente do username utilizado no login.
    name = Column(
        String,
        nullable=False
    )

    # Indica se o usuário está ativo.
    # 1 = ativo
    # 0 = desativado
    is_active = Column(
        Integer,
        nullable=False,
        default=1
    )

    # Guarda automaticamente a data e hora
    # em que o usuário foi criado.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )


# ============================================================
# ROLES
# ============================================================

class Role(Base):
    """
    Representa um perfil de acesso do Control Room.

    Uma Role agrupa permissões que poderão ser atribuídas
    a vários usuários.

    Um usuário também poderá possuir várias Roles.
    """

    __tablename__ = "roles"

    # Identificador único da Role.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Nome da Role.
    #
    # Exemplos:
    # - Administrador
    # - Operador
    # - Analista
    name = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # Descrição opcional da Role.
    description = Column(
        String,
        nullable=True
    )

    # Data e hora de criação da Role.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )


# ============================================================
# RELAÇÃO USUÁRIO ↔ ROLE
# ============================================================

class UserRole(Base):
    """
    Tabela intermediária da relação muitos-para-muitos
    entre usuários e Roles.

    Um usuário pode possuir várias Roles.

    Uma Role pode pertencer a vários usuários.
    """

    __tablename__ = "user_roles"


    # ========================================================
    # INTEGRIDADE DA ASSOCIAÇÃO USUÁRIO ↔ ROLE
    # ========================================================
    #
    # Um usuário pode possuir várias Roles, porém a mesma Role
    # não pode ser associada duas vezes ao mesmo usuário.
    #
    # Esta constraint é necessária no banco de dados porque
    # somente verificar a existência da associação no Python
    # não protege contra duas requisições concorrentes.
    # ========================================================

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            name="uq_user_roles_user_role",
        ),
    )

    # Identificador interno do relacionamento.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Usuário associado à Role.
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Role associada ao usuário.
    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=False,
        index=True
    )




    # ============================================================
# PERMISSÕES GENÉRICAS DO CONTROL ROOM
# ============================================================

class Permission(Base):
    """
    Representa uma permissão disponível no Control Room.

    A permissão é composta por:
    - resource: recurso/módulo do sistema.
    - action: ação permitida nesse recurso.

    Exemplos:
        Agents + view
        Agents + create
        Executions + cancel
        Vault + use

    As permissões são armazenadas como dados no banco.
    Isso permite que as Roles sejam totalmente customizáveis,
    sem precisar criar uma Role específica no código.
    """

    __tablename__ = "permissions"

    # Identificador único da permissão.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Recurso do Control Room ao qual a permissão pertence.
    #
    # Exemplos:
    # - agents
    # - executions
    # - schedules
    # - vault
    resource = Column(
        String,
        nullable=False,
        index=True
    )

    # Ação permitida sobre o recurso.
    #
    # Exemplos:
    # - view
    # - create
    # - edit
    # - delete
    # - execute
    # - cancel
    # - use
    action = Column(
        String,
        nullable=False,
        index=True
    )


class RolePermission(Base):
    """
    Relaciona uma Role às permissões que ela possui.

    Uma Role pode possuir várias permissões.
    Uma mesma permissão pode ser utilizada por várias Roles.
    """

    __tablename__ = "role_permissions"

    # ========================================================
    # INTEGRIDADE DA ASSOCIAÇÃO ROLE ↔ PERMISSION
    # ========================================================
    #
    # Uma Role pode possuir várias permissões, mas a mesma
    # Permission não pode aparecer duas vezes na mesma Role.
    #
    # A garantia precisa existir no PostgreSQL para também
    # proteger operações concorrentes.
    # ========================================================

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permissions_role_permission",
        ),
    )

    # Identificador interno do relacionamento.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Role que receberá a permissão.
    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=False,
        index=True
    )

    # Permissão concedida à Role.
    permission_id = Column(
        Integer,
        ForeignKey("permissions.id"),
        nullable=False,
        index=True
    )



# ============================================================
# RATE LIMIT DE AUTENTICAÇÃO
# ============================================================

class AuthRateLimit(Base):
    """
    Armazena o estado persistente do rate limit utilizado
    pelos endpoints públicos de autenticação.

    A chave lógica do controle é:

        username + ip_address

    Isso permite compartilhar o estado entre diferentes
    processos ou instâncias do Control Room que utilizem
    o mesmo PostgreSQL.

    O registro NÃO armazena senha, token ou session_id.
    """

    __tablename__ = "auth_rate_limits"

    __table_args__ = (
        UniqueConstraint(
            "username",
            "ip_address",
            name="uq_auth_rate_limits_username_ip",
        ),
    )

    # Identificador interno do registro.
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Username normalizado utilizado na tentativa.
    #
    # Não existe ForeignKey para users porque também precisamos
    # contabilizar tentativas contra usernames inexistentes.
    username = Column(
        String,
        nullable=False,
        index=True,
    )

    # Endereço IP de origem da tentativa.
    ip_address = Column(
        String,
        nullable=False,
        index=True,
    )

    # Quantidade de falhas consecutivas registradas para
    # esta combinação username + IP.
    failed_attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # Momento da falha de autenticação mais recente.
    last_failed_at = Column(
        DateTime,
        nullable=True,
    )

    # Enquanto este campo estiver no futuro, novas tentativas
    # para a combinação username + IP deverão receber HTTP 429.
    blocked_until = Column(
        DateTime,
        nullable=True,
        index=True,
    )

    # Data de criação do registro de controle.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Última alteração do estado do rate limit.
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
# ============================================================
# SESSÕES DOS USUÁRIOS
# ============================================================

class UserSession(Base):
    # Define a tabela que armazenará as sessões
    # dos usuários autenticados.
    __tablename__ = "user_sessions"

    # Identificador interno da sessão no banco.
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Identificador aleatório da sessão do navegador.
    #
    # Esse valor será enviado através do cookie HttpOnly
    # utilizado pelo Frontend.
    session_id = Column(
        String,
        unique=True,
        nullable=True,
        index=True
    )

    # Token independente utilizado para autenticação
    # através de Authorization: Bearer <token>.
    #
    # Esse token NÃO é o mesmo session_id.
    #
    # Ele será utilizado pelo Swagger e por clientes
    # de API que precisarem autenticar diretamente.
    access_token = Column(
        String,
        unique=True,
        nullable=True,
        index=True
    )

    # Identifica o usuário dono da sessão.
    #
    # Esse campo referencia o usuário cadastrado
    # na tabela "users".
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Data e hora em que a sessão foi criada.
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Data e hora em que a sessão irá expirar.
    expires_at = Column(
        DateTime,
        nullable=False
    )

    # Indica se a sessão foi revogada.
    #
    # 0 = sessão válida
    # 1 = sessão revogada
    revoked = Column(
        Integer,
        nullable=False,
        default=0
    )



# ============================================================
# VAULT
# ============================================================

class VaultFolder(Base):
    """
    Representa uma pasta dentro do Vault.

    Permite criar uma estrutura hierárquica, por exemplo:

    Credenciais
    └── Empresa 1
        ├── Financeiro
        └── RH
    """

    __tablename__ = "vault_folders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    # Permite uma pasta ficar dentro de outra pasta.
    # NULL significa que é uma pasta raiz.
    parent_id = Column(
        Integer,
        ForeignKey("vault_folders.id"),
        nullable=True
    )


class VaultCredential(Base):
    """
    Representa uma credencial cadastrada dentro
    de uma pasta do Vault.

    Exemplo:

    Empresa 1
    └── Financeiro
        └── usuario_1
    """

    __tablename__ = "vault_credentials"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    # Pasta onde esta credencial está armazenada.
    folder_id = Column(
        Integer,
        ForeignKey("vault_folders.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        nullable=False
    )


class VaultField(Base):
    """
    Representa um campo pertencente a uma credencial.

    Exemplo:

    usuario_1
    ├── Username
    ├── Password
    ├── Host
    └── Token

    Cada campo decide individualmente se é secreto.
    """

    __tablename__ = "vault_fields"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Credencial à qual este campo pertence.
    credential_id = Column(
        Integer,
        ForeignKey("vault_credentials.id"),
        nullable=False
    )

    # Nome do campo.
    # Exemplo: Username, Password, Host, Token.
    name = Column(
        String,
        nullable=False
    )

    # Valor armazenado.
    #
    # Se is_secret = False:
    #     valor normal.
    #
    # Se is_secret = True:
    #     valor criptografado com AES-256-GCM.
    value = Column(
        Text,
        nullable=False
    )

    # Define se este campo deve ser tratado como secreto.
    is_secret = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Versão da criptografia utilizada.
    # Começaremos com a versão 1.
    encryption_version = Column(
        Integer,
        nullable=False,
        default=1
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        nullable=False
    )