from sqlalchemy import Column, String, Integer, ForeignKey, DateTime

from database import Base


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

    name = Column(
        String,
        nullable=False
    )

    host = Column(
        String,
        nullable=False
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

    last_heartbeat = Column(
    DateTime,
    nullable=True
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
# EXECUÇÕES
# ============================================================
class Execution(Base):

    __tablename__ = "executions"

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

    status = Column(
        String,
        nullable=False,
        default="running"
    )

    started_at = Column(
        DateTime,
        nullable=False
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
