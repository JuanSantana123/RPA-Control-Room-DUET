from database import SessionLocal
from models import User, UserSession


def obter_usuario_da_sessao(session_id: str | None):
    """
    Retorna o usuário associado à sessão.
    Retorna None caso a sessão seja inválida,
    expirada ou revogada.
    """

    if not session_id:
        return None

    db = SessionLocal()

    try:

        sessao = db.query(
            UserSession
        ).filter(
            UserSession.session_id == session_id,
            UserSession.revoked == 0
        ).first()

        if not sessao:
            return None

        # Verifica se a sessão expirou.
        from datetime import datetime

        # A sessão deixa de ser válida exatamente no instante
        # definido em expires_at.
        if sessao.expires_at <= datetime.utcnow():

            sessao.revoked = 1
            db.commit()

            return None

        # Busca o usuário associado à sessão.
        #
        # Além de verificar o ID, exige que o usuário
        # esteja ativo para continuar autenticado.
        usuario = db.query(
            User
        ).filter(
            User.id == sessao.user_id,
            User.is_active == 1
        ).first()

        return usuario

    finally:

        db.close()