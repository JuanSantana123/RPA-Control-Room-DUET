import secrets

from pathlib import Path

from database import SessionLocal

from models import (
    User,
    Role,
    UserRole,
    Permission,
    RolePermission
)

from auth.security import gerar_hash_senha

# ============================================================
# CATÁLOGO DE PERMISSÕES
# ============================================================

# Cada tupla representa:
#
#     (resource, action)
#
# O catálogo define apenas quais ações existem no sistema.
#
# IMPORTANTE:
# Isso NÃO cria Roles.
#
# As Roles continuarão sendo criadas/configuradas pelo usuário
# posteriormente, podendo receber qualquer combinação dessas
# permissões.
#
# Exemplos:
#
#     Desenvolvedor:
#         Agents -> view
#         Executions -> view
#
#     Operador:
#         Agents -> view
#         Executions -> view
#         Executions -> execute
#
#     Administrador:
#         Agents -> view/create/edit/delete
#         Executions -> view/execute/cancel
#         Vault -> view/create/edit/delete/use
#
PERMISSOES_INICIAIS = [

    # ========================================================
    # AGENTS
    # ========================================================

    ("Agents", "view"),
    ("Agents", "create"),
    ("Agents", "edit"),
    ("Agents", "delete"),

    # Permite obter artefatos de instalação/bootstrap que contêm
    # material de autenticação do Agent, incluindo agent_token.
    #
    # Essa ação é separada de "view" porque visualizar um Agent
    # não deve conceder acesso às suas credenciais.
    #
    # Também é separada de "create" porque criar um cadastro de
    # Agent e obter seu material de autenticação são capacidades
    # de segurança distintas.
    ("Agents", "bootstrap"),

    # ========================================================
    # EXECUTIONS
    # ========================================================

    ("Executions", "view"),
    ("Executions", "execute"),
    ("Executions", "stop"),
    ("Executions", "cancel"),
    # ========================================================
    # ROBOTS
    # ========================================================

    ("Robots", "view"),
    ("Robots", "create"),
    ("Robots", "edit"),
    ("Robots", "delete"),


    # ========================================================
    # DASHBOARD
    # ========================================================
    #
    # Controla o acesso à visão principal e aos indicadores
    # apresentados no Dashboard do Control Room.
    # ========================================================

    ("Dashboard", "view"),

    # ========================================================
    # LOGS
    # ========================================================
    #
    # Controla o acesso à visão de Logs do Control Room.
    # ========================================================

    ("Logs", "view"),


    # ========================================================
    # SCHEDULES
    # ========================================================

    ("Schedules", "view"),
    ("Schedules", "create"),
    ("Schedules", "edit"),
    ("Schedules", "delete"),

    # ========================================================
    # USERS
    # ========================================================

    ("Users", "view"),
    ("Users", "create"),
    ("Users", "edit"),
    ("Users", "delete"),

    # ========================================================
    # ROLES
    # ========================================================

    ("Roles", "view"),
    ("Roles", "create"),
    ("Roles", "edit"),
    ("Roles", "delete"),

      # ========================================================
    # VAULT
    # ========================================================

    ("Vault", "view"),
    ("Vault", "create"),
    ("Vault", "edit"),
    ("Vault", "delete"),
    ("Vault", "use"),

    # ========================================================
    # VAULT - CONTROL ROOM
    # ========================================================
    #
    # Permissões administrativas relacionadas à infraestrutura
    # criptográfica do Vault.
    #
    # Essas permissões são separadas das operações normais de
    # credenciais porque permitem exportar ou importar a
    # Master Key utilizada pelo Control Room.
    #
    # export_master_key:
    #     Permite gerar um vault-backup.key protegido por
    #     senha de recuperação.
    #
    # import_master_key:
    #     Permite recuperar uma Master Key a partir de um
    #     vault-backup.key.
    # ========================================================

    ("Vault - Control Room", "export_master_key"),
    ("Vault - Control Room", "import_master_key"),



    # ========================================================
    # DEVELOPMENT
    # ========================================================
    #
    # Permissões utilizadas pela área de Desenvolvimento,
    # DUET Studio, Checkout, Lixeira e Workflow/Kanban.
    # ========================================================

    ("Development", "view"),
    ("Development", "create"),
    ("Development", "edit"),
    ("Development", "delete"),

    # Lixeira de projetos.
    ("Development", "trash_view"),
    ("Development", "restore"),
    ("Development", "permanent_delete"),

    # Checkout exclusivo dos projetos.
    ("Development", "checkout"),
    ("Development", "force_checkout_release"),

    # Workflow / Kanban.
    ("Development", "move_stage"),

    # Publicação protegida do Workflow.
    ("Development", "publish"),


    # ========================================================
    # LIBRARIES
    # ========================================================
    #
    # Bibliotecas reutilizáveis e versionadas do DUET CORE.
    #
    # view:
    #     Visualizar bibliotecas, versões e dependências.
    #
    # create:
    #     Criar uma nova biblioteca.
    #
    # edit:
    #     Alterar os metadados da biblioteca.
    #
    # publish:
    #     Publicar novas versões imutáveis.
    #
    # delete:
    #     Desativar bibliotecas ou versões.
    #
    # use:
    #     Adicionar, trocar ou remover bibliotecas utilizadas
    #     por um AutomationProject.
    # ========================================================

    ("Libraries", "view"),
    ("Libraries", "create"),
    ("Libraries", "edit"),
    ("Libraries", "publish"),
    ("Libraries", "delete"),
    ("Libraries", "use"),
    # ========================================================
    # API SWAGGER
    # ========================================================
    # Permite que o usuário utilize a API do Control Room
    # para obter um access_token Bearer.
    ("API", "access"),
]


# ============================================================
# INICIALIZAÇÃO DO CATÁLOGO
# ============================================================

def criar_permissoes_iniciais():
    """
    Garante que todas as permissões básicas existam no banco.

    A função é idempotente:
    se uma permissão já existir, ela não será duplicada.
    """

    db = SessionLocal()

    try:

        for resource, action in PERMISSOES_INICIAIS:

            permissao_existente = (
                db.query(Permission)
                .filter(
                    Permission.resource == resource,
                    Permission.action == action
                )
                .first()
            )

            if permissao_existente:
                continue

            permissao = Permission(
                resource=resource,
                action=action
            )

            db.add(permissao)

        db.commit()

    finally:
        db.close()





# ============================================================
# SINCRONIZAÇÃO DA ROLE ADMINISTRADOR
# ============================================================

def sincronizar_permissoes_administrador():
    """
    Garante que a Role Administrador possua todas as Permissions
    atualmente cadastradas no Control Room.

    Finalidade:
        preservar o acesso administrativo quando uma atualização
        do DUET introduzir novas Permissions.

    Exemplo:
        uma versão antiga pode não possuir Dashboard:view.
        Após uma atualização, criar_permissoes_iniciais() cria
        essa Permission e esta função a associa à Role
        Administrador existente.

    IMPORTANTE:
        - não cria a Role Administrador;
        - não cria usuários;
        - não remove permissões existentes;
        - somente adiciona associações que estiverem faltando;
        - é idempotente.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # LOCALIZA A ROLE ADMINISTRADOR
        # ----------------------------------------------------
        #
        # Em uma instalação ainda não inicializada ela pode não
        # existir. Nesse caso não existe nada para sincronizar.
        # ----------------------------------------------------

        role_admin = (
            db.query(Role)
            .filter(
                Role.name == "Administrador"
            )
            .first()
        )

        if not role_admin:
            return

        # ----------------------------------------------------
        # PERMISSIONS JÁ ASSOCIADAS
        # ----------------------------------------------------

        permission_ids_existentes = {
            permission_id
            for (permission_id,) in (
                db.query(
                    RolePermission.permission_id
                )
                .filter(
                    RolePermission.role_id == role_admin.id
                )
                .all()
            )
        }

        # ----------------------------------------------------
        # TODAS AS PERMISSIONS ATUAIS DO SISTEMA
        # ----------------------------------------------------

        permissoes = (
            db.query(Permission)
            .all()
        )

        # ----------------------------------------------------
        # ADICIONA SOMENTE AS QUE ESTÃO FALTANDO
        # ----------------------------------------------------

        for permissao in permissoes:

            if permissao.id in permission_ids_existentes:
                continue

            db.add(
                RolePermission(
                    role_id=role_admin.id,
                    permission_id=permissao.id,
                )
            )

        db.commit()

    except Exception:

        # A sincronização é transacional.
        # Nenhuma associação parcial deve permanecer em caso
        # de erro.
        db.rollback()

        raise

    finally:

        db.close()

# ============================================================
# CRIAÇÃO DO ADMINISTRADOR INICIAL
# ============================================================



def criar_admin_inicial():
    """
        Cria o usuário administrador inicial do Control Room.

        O bootstrap acontece somente quando o banco ainda não
        possui nenhum usuário.

        Usuário inicial:
            username: admin

        A senha é gerada aleatoriamente e NÃO é definida
        manualmente no código.

        A senha inicial é exibida no terminal somente durante
        a criação do primeiro administrador.

        A senha em texto puro NÃO é gravada em arquivo e NÃO é
        armazenada no banco de dados. Somente o hash bcrypt é
        persistido.

        A função é idempotente:
        depois que existir qualquer usuário no banco,
        nenhuma conta será criada ou alterada.
    """

    db = SessionLocal()

    try:

        # ====================================================
        # VERIFICA SE JÁ EXISTE ALGUM USUÁRIO
        # ====================================================

        usuario_existente = (
            db.query(User)
            .first()
        )

        # ====================================================
        # Se já existe pelo menos um usuário, significa que
        # o sistema já foi inicializado.
        #
        # Nesse caso não criamos nem alteramos o admin.
        # ====================================================

        if usuario_existente:
            return

        # ====================================================
        # GERA A SENHA INICIAL ALEATÓRIA
        # ====================================================

        senha_inicial = secrets.token_urlsafe(16)

        # ====================================================
        # CRIA OU LOCALIZA A ROLE ADMINISTRADOR
        # ====================================================

        role_admin = (
            db.query(Role)
            .filter(
                Role.name == "Administrador"
            )
            .first()
        )

        if not role_admin:

            role_admin = Role(
                name="Administrador",
                description=(
                    "Administrador do Control Room "
                    "com acesso a todas as permissões."
                )
            )

            db.add(role_admin)

            # Garante que o banco gere o ID da Role
            # antes de criarmos os relacionamentos.
            db.flush()

        # ====================================================
        # CRIA O USUÁRIO ADMIN
        # ====================================================

        admin = User(
            username="admin",

            # A senha original nunca é armazenada.
            # Apenas o hash bcrypt é salvo no banco.
            password_hash=gerar_hash_senha(
                senha_inicial
            ),

            name="Administrador",

            is_active=1
        )

        db.add(admin)

        # Garante que admin.id esteja disponível.
        db.flush()

        # ====================================================
        # ASSOCIA O ADMIN À ROLE ADMINISTRADOR
        # ====================================================

        usuario_role = UserRole(
            user_id=admin.id,
            role_id=role_admin.id
        )

        db.add(usuario_role)

        # ====================================================
        # CONCEDE TODAS AS PERMISSÕES À ROLE
        # ====================================================

        permissoes = (
            db.query(Permission)
            .all()
        )

        for permissao in permissoes:

            role_permissao = RolePermission(
                role_id=role_admin.id,
                permission_id=permissao.id
            )

            db.add(role_permissao)

        # ====================================================
        # CONFIRMA A CRIAÇÃO NO BANCO
        # ====================================================

        db.commit()

        # ====================================================
        # EXIBE A CREDENCIAL INICIAL NO TERMINAL
        # ====================================================

        # A senha inicial é exibida somente durante a criação
        # do primeiro administrador.
        #
        # Ela NÃO é gravada em arquivo e NÃO é armazenada em
        # texto puro no banco.
        print()
        print("=" * 60)
        print("RPA CONTROL ROOM - ADMINISTRADOR INICIAL")
        print("=" * 60)
        print("Usuário: admin")
        print(f"Senha inicial: {senha_inicial}")
        print()
        print("IMPORTANTE: guarde esta senha.")
        print("=" * 60)
        print()

    except Exception:

        # Se ocorrer qualquer erro durante o bootstrap,
        # desfazemos toda a transação.
        db.rollback()

        raise

    finally:

        db.close()