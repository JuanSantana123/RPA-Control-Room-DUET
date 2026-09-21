# ============================================================
# SCHEMAS - AUTENTICAÇÃO E USUÁRIOS
# ============================================================
#
# Este módulo contém exclusivamente os contratos Pydantic
# utilizados pelas APIs de autenticação e gerenciamento
# de usuários.
#
# Não existe acesso ao banco de dados neste arquivo.
# Não existe regra de negócio neste arquivo.
# Não existe registro de endpoints FastAPI neste arquivo.
# ============================================================

from pydantic import BaseModel


# ============================================================
# CRIAÇÃO DE USUÁRIO
# ============================================================

class UserCreate(BaseModel):
    """
    Dados necessários para criar um usuário no Control Room.

    role_id:
        Pode ser None quando o usuário for criado sem Role.
    """

    username: str
    password: str
    name: str
    role_id: int | None = None


# ============================================================
# ALTERAÇÃO DO STATUS DO USUÁRIO
# ============================================================

class UserStatusUpdate(BaseModel):
    """
    Define se um usuário ficará ativo ou inativo.

    is_active:
        True  -> usuário ativo.
        False -> usuário inativo.
    """

    is_active: bool


# ============================================================
# ALTERAÇÃO DE SENHA
# ============================================================

class UserPasswordUpdate(BaseModel):
    """
    Dados necessários para alterar a senha de um usuário.

    new_password:
        Nova senha que será validada e posteriormente
        transformada em hash antes de ser armazenada.
    """

    new_password: str
# ============================================================
# ATUALIZAÇÃO DAS ROLES DE UM USUÁRIO
# ============================================================

class UserRolesUpdate(BaseModel):
    """
    Lista completa das Roles que o usuário deverá possuir.

    A lista recebida substitui as associações atuais.

    Exemplo:
        role_ids = [2, 3]

    Uma lista vazia remove todas as Roles:
        role_ids = []
    """

    role_ids: list[int]


# ============================================================
# LOGIN
# ============================================================

class UserLogin(BaseModel):
    """
    Credenciais utilizadas no login do Frontend e também
    na geração do Bearer Token da API.
    """

    username: str
    password: str