# ============================================================
# SERVICE - AUTENTICAÇÃO
# ============================================================
#
# Responsabilidade:
#     Concentrar as regras de autenticação do Control Room:
#
#         - geração de Bearer Token;
#         - login e criação da sessão do Frontend;
#         - consulta do usuário autenticado (/me);
#         - logout e revogação da credencial atual.
#
# Este módulo NÃO registra endpoints FastAPI.
#
# A camada HTTP continuará em:
#
#     api/auth.py
#
# ============================================================

import secrets

from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import (
    User,
    UserSession,
    UserRole,
    RolePermission,
    Permission,
)

# ============================================================
# SEGURANÇA E AUTORIZAÇÃO
# ============================================================
#
# verificar_senha:
#     valida a senha recebida contra o hash armazenado.
#
# usuario_tem_permissao:
#     verifica as permissões efetivas do usuário autenticado.
# ============================================================
from auth.security import (
    executar_verificacao_senha_dummy,
    senha_compativel_com_bcrypt,
    verificar_senha,
)
from auth.permissions import usuario_tem_permissao
# ============================================================
# RATE LIMIT DE AUTENTICAÇÃO
# ============================================================
#
# O controle de tentativas permanece isolado em rate_limit.py.
# Este service apenas informa sucesso ou falha de autenticação.
# ============================================================
from auth.rate_limit import (
    calcular_retry_after_segundos,
    obter_bloqueio_ativo,
    registrar_falha_autenticacao,
    resetar_rate_limit_autenticacao,
)

from schemas.auth import UserLogin


# ============================================================
# GERAR TOKEN BEARER DA API
# ============================================================

def gerar_token_api_service(
    request: UserLogin,
    db: Session,
    ip_origem: str | None,
):
    """
    Autentica o usuário por username/senha e cria um
    access_token Bearer para utilização da API.

    O ip_origem é utilizado exclusivamente pelo mecanismo
    de rate limit. A camada HTTP continua responsável por
    determinar o endereço da conexão.

    Regras:

        - máximo de 5 falhas consecutivas por username + IP;
        - bloqueio temporário de 15 minutos;
        - usuário precisa existir e estar ativo;
        - senha precisa ser válida;
        - usuário autenticado precisa possuir API:access;
        - tokens Bearer anteriores são revogados;
        - novo token possui validade de 1 hora.
    """

    # VERIFICAR RATE LIMIT
    # --------------------------------------------------------
    #
    # Enquanto a combinação username + IP estiver bloqueada,
    # não executamos consulta de usuário nem validação de senha.
    #
    # obter_bloqueio_ativo() também informa quando o bloqueio
    # termina, permitindo devolver Retry-After ao cliente.
    # --------------------------------------------------------

    bloqueado_ate = obter_bloqueio_ativo(
        db=db,
        username=request.username,
        ip_origem=ip_origem,
    )

    if bloqueado_ate is not None:

        retry_after = calcular_retry_after_segundos(
            bloqueado_ate=bloqueado_ate,
        )

        raise HTTPException(
            status_code=429,
            detail=(
                "Muitas tentativas de autenticação. "
                "Tente novamente mais tarde."
            ),
            headers={
                "Retry-After": str(retry_after),
            },
        )

    # --------------------------------------------------------
    # VALIDAR TAMANHO DA SENHA RECEBIDA
    # --------------------------------------------------------
    #
    # O bcrypt possui limite de 72 bytes.
    #
    # Uma entrada acima desse limite é tratada como falha de
    # autenticação e recebe a mesma resposta genérica utilizada
    # para username inexistente ou senha incorreta.
    # --------------------------------------------------------

    if not senha_compativel_com_bcrypt(
        request.password,
    ):

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }
    # --------------------------------------------------------
    # BUSCAR USUÁRIO
    # --------------------------------------------------------

    usuario = (
        db.query(User)
        .filter(
            User.username == request.username
        )
        .first()
    )

    if not usuario:

        # ----------------------------------------------------
        # NORMALIZAR CUSTO DA VERIFICAÇÃO DE SENHA
        # ----------------------------------------------------
        #
        # Mesmo sem um usuário correspondente, executamos uma
        # verificação bcrypt utilizando um hash dummy.
        #
        # Isso reduz a diferença de tempo observável entre um
        # username inexistente e uma senha incorreta para um
        # username existente.
        # ----------------------------------------------------

        executar_verificacao_senha_dummy(
            request.password,
        )

        # Username inexistente também conta como falha.
        #
        # Isso impede que usernames inválidos sejam utilizados
        # para contornar o controle de tentativas.
        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }

    # --------------------------------------------------------
    # VALIDAR USUÁRIO ATIVO
    # --------------------------------------------------------

    if usuario.is_active != 1:

        # ----------------------------------------------------
        # NORMALIZAR CUSTO PARA USUÁRIO INATIVO
        # ----------------------------------------------------
        #
        # Não utilizamos o password_hash real porque uma conta
        # inativa não deve prosseguir para autenticação.
        #
        # Executamos o mesmo bcrypt dummy utilizado para um
        # username inexistente, reduzindo a diferença de tempo
        # que poderia revelar a existência/status da conta.
        # ----------------------------------------------------

        executar_verificacao_senha_dummy(
            request.password,
        )

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }

    # --------------------------------------------------------
    # VALIDAR SENHA
    # --------------------------------------------------------
    #
    # A identidade do usuário deve ser comprovada antes de
    # consultar permissões específicas da conta.
    #
    # Isso evita revelar informações de autorização para uma
    # requisição que ainda não apresentou uma senha válida.
    # --------------------------------------------------------

    senha_valida = verificar_senha(
        request.password,
        usuario.password_hash,
    )

    if not senha_valida:

        # A senha incorreta incrementa o contador persistente
        # da combinação username + IP.
        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }


   
    # --------------------------------------------------------
    # VALIDAR PERMISSÃO API:access
    # --------------------------------------------------------
    #
    # Neste ponto o username, o status do usuário e a senha
    # já foram validados.
    #
    # Agora verificamos a autorização necessária para que o
    # usuário autenticado possa gerar um Bearer Token.
    # --------------------------------------------------------

    possui_acesso_api = usuario_tem_permissao(
        usuario=usuario,
        db=db,
        resource="API",
        action="access",
    )

    if not possui_acesso_api:
        raise HTTPException(
            status_code=403,
            detail=(
                "Usuário não possui permissão "
                "'API:access'."
            ),
        )



    # --------------------------------------------------------
    # AUTENTICAÇÃO VÁLIDA
    # --------------------------------------------------------
    #
    # Username, status e senha já foram validados.
    #
    # A ausência de API:access é uma falha de autorização,
    # não uma falha de autenticação, portanto não incrementa
    # o rate limit.
    # --------------------------------------------------------

    resetar_rate_limit_autenticacao(
        db=db,
        username=request.username,
        ip_origem=ip_origem,
    )
    # --------------------------------------------------------
    # GERAR ACCESS TOKEN
    # --------------------------------------------------------

    access_token = secrets.token_urlsafe(32)

    expires_at = (
        datetime.utcnow()
        + timedelta(hours=1)
    )

    # --------------------------------------------------------
    # REVOGAR TOKENS BEARER ANTERIORES
    # --------------------------------------------------------

    db.query(UserSession).filter(
        UserSession.user_id == usuario.id,
        UserSession.access_token.isnot(None),
        UserSession.revoked == 0,
    ).update(
        {
            UserSession.revoked: 1,
        },
        synchronize_session=False,
    )

    # --------------------------------------------------------
    # CRIAR NOVO TOKEN
    # --------------------------------------------------------

    nova_sessao = UserSession(
        access_token=access_token,
        user_id=usuario.id,
        expires_at=expires_at,
        revoked=0,
    )

    db.add(nova_sessao)

    # Revogação dos tokens antigos e criação do novo token
    # pertencem à mesma transação.
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ============================================================
# LOGIN DO FRONTEND
# ============================================================

def fazer_login_service(
    request: UserLogin,
    db: Session,
    ip_origem: str | None,
):
    """
    Valida username/senha e cria uma sessão para o Frontend.

    IMPORTANTE:
        Este service NÃO grava o cookie HTTP.

        Ele cria a sessão no banco e devolve o session_id
        para o router.

        O router api/auth.py continuará responsável por
        chamar response.set_cookie(), pois cookie pertence
        à camada HTTP.
    """

    # --------------------------------------------------------
    # VERIFICAR RATE LIMIT
    # --------------------------------------------------------
    #
    # Consulta o instante final do bloqueio para que a camada
    # HTTP receba também o header Retry-After.
    # --------------------------------------------------------

    bloqueado_ate = obter_bloqueio_ativo(
        db=db,
        username=request.username,
        ip_origem=ip_origem,
    )

    if bloqueado_ate is not None:

        retry_after = calcular_retry_after_segundos(
            bloqueado_ate=bloqueado_ate,
        )

        raise HTTPException(
            status_code=429,
            detail=(
                "Muitas tentativas de autenticação. "
                "Tente novamente mais tarde."
            ),
            headers={
                "Retry-After": str(retry_after),
            },
        )

    # --------------------------------------------------------
    # VALIDAR TAMANHO DA SENHA RECEBIDA
    # --------------------------------------------------------
    #
    # Impede que entradas incompatíveis com o limite do bcrypt
    # alcancem diretamente a função de verificação.
    #
    # O cliente continua recebendo a mesma resposta genérica
    # utilizada pelas demais falhas de autenticação.
    # --------------------------------------------------------

    if not senha_compativel_com_bcrypt(
        request.password,
    ):

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }
    # --------------------------------------------------------
    # BUSCAR USUÁRIO
    # --------------------------------------------------------

    usuario = (
        db.query(User)
        .filter(
            User.username == request.username
        )
        .first()
    )

    if not usuario:

        # ----------------------------------------------------
        # NORMALIZAR CUSTO DA VERIFICAÇÃO DE SENHA
        # ----------------------------------------------------
        #
        # Mantemos o caminho de username inexistente mais
        # próximo do custo computacional de uma autenticação
        # com username existente e senha incorreta.
        # ----------------------------------------------------

        executar_verificacao_senha_dummy(
            request.password,
        )

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }

    # --------------------------------------------------------
    # VALIDAR STATUS
    # --------------------------------------------------------

    if usuario.is_active != 1:

        # Executa bcrypt dummy para que o caminho de uma conta
        # inativa não seja significativamente mais barato que
        # os demais caminhos de falha de autenticação.
        executar_verificacao_senha_dummy(
            request.password,
        )

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }

    # --------------------------------------------------------
    # VALIDAR SENHA
    # --------------------------------------------------------

    senha_valida = verificar_senha(
        request.password,
        usuario.password_hash,
    )

    if not senha_valida:

        registrar_falha_autenticacao(
            db=db,
            username=request.username,
            ip_origem=ip_origem,
        )

        return {
            "status": "error",
            "message": "Usuário ou senha inválidos.",
        }

    # --------------------------------------------------------
    # AUTENTICAÇÃO VÁLIDA
    # --------------------------------------------------------
    #
    # A autenticação foi concluída corretamente.
    # Removemos o histórico de falhas desta combinação.
    # --------------------------------------------------------

    resetar_rate_limit_autenticacao(
        db=db,
        username=request.username,
        ip_origem=ip_origem,
    )
    # --------------------------------------------------------
    # CRIAR SESSÃO
    # --------------------------------------------------------

    session_id = secrets.token_urlsafe(32)

    expires_at = (
        datetime.utcnow()
        + timedelta(hours=8)
    )

    nova_sessao = UserSession(
        session_id=session_id,
        user_id=usuario.id,
        expires_at=expires_at,
        revoked=0,
    )

    db.add(nova_sessao)
    db.commit()
    db.refresh(nova_sessao)

    # --------------------------------------------------------
    # RETORNO INTERNO
    # --------------------------------------------------------
    #
    # O session_id é necessário para que api/auth.py consiga
    # criar o cookie.
    #
    # Ele NÃO deverá ser devolvido no JSON da API.
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": "Login realizado com sucesso.",
        "session_id": session_id,
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "name": usuario.name,
            "is_active": usuario.is_active,
        },
    }


# ============================================================
# USUÁRIO ATUAL (/ME)
# ============================================================

def usuario_atual_service(
    usuario: User,
    db: Session,
):
    """
    Retorna os dados do usuário autenticado juntamente com
    suas permissões efetivas.

    As permissões são obtidas através da cadeia:

        User
          -> UserRole
          -> RolePermission
          -> Permission
    """

    permissoes = (
        db.query(Permission)
        .join(
            RolePermission,
            RolePermission.permission_id
            == Permission.id,
        )
        .join(
            UserRole,
            UserRole.role_id
            == RolePermission.role_id,
        )
        .filter(
            UserRole.user_id == usuario.id
        )
        .all()
    )

    permissoes_usuario = [
        f"{permissao.resource}:{permissao.action}"
        for permissao in permissoes
    ]

    return {
        "status": "success",
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "name": usuario.name,
            "is_active": usuario.is_active,
            "permissions": permissoes_usuario,
        },
    }


# ============================================================
# LOGOUT
# ============================================================

def fazer_logout_service(
    usuario: User,
    db: Session,
    session_id: str | None = None,
    access_token: str | None = None,
):
    """
    Revoga a sessão do Frontend e/ou o Bearer Token enviado
    na requisição.

    Parâmetros:

        usuario:
            Usuário já autenticado pela dependency do router.

        db:
            Sessão SQLAlchemy utilizada pela operação.

        session_id:
            Identificador recebido através do cookie.

        access_token:
            Bearer Token recebido no Header Authorization.

    A remoção física do cookie continua sendo feita pelo
    router, pois é responsabilidade HTTP.
    """

    # --------------------------------------------------------
    # REVOGAR SESSÃO DO FRONTEND
    # --------------------------------------------------------

    if session_id:

        sessao_cookie = (
            db.query(UserSession)
            .filter(
                UserSession.session_id
                == session_id,

                UserSession.user_id
                == usuario.id,
            )
            .first()
        )

        if sessao_cookie:
            sessao_cookie.revoked = 1

    # --------------------------------------------------------
    # REVOGAR BEARER TOKEN
    # --------------------------------------------------------

    if access_token:

        sessao_token = (
            db.query(UserSession)
            .filter(
                UserSession.access_token
                == access_token,

                UserSession.user_id
                == usuario.id,
            )
            .first()
        )

        if sessao_token:
            sessao_token.revoked = 1

    # --------------------------------------------------------
    # PERSISTIR REVOGAÇÕES
    # --------------------------------------------------------

    db.commit()

    return {
        "status": "success",
        "message": "Logout realizado com sucesso.",
    }