# ============================================================
# DUET CORE - MIGRAÇÃO DE PERMISSÕES
# CREDENCIAIS DE DISPOSITIVO
# ============================================================
#
# Objetivo:
#
# Cadastrar no catálogo de permissões do Control Room somente
# as permissões necessárias para a nova API:
#
#     DeviceCredentials:view
#     DeviceCredentials:create
#     DeviceCredentials:edit
#     DeviceCredentials:delete
#
# IMPORTANTE:
#
# - NÃO altera Roles automaticamente;
# - NÃO concede acesso a nenhum usuário;
# - NÃO remove permissões existentes;
# - NÃO altera permissões do Vault atual;
# - NÃO altera Agents, Robots, Executions ou Schedules;
# - pode ser executada novamente sem duplicar registros.
#
# A associação destas permissões às Roles continuará sendo
# feita pelo mecanismo de Roles já existente no DUET.
# ============================================================

from database import SessionLocal
from models import Permission


# ============================================================
# PERMISSÕES OFICIAIS DE CREDENCIAIS DE DEVICE
# ============================================================

DEVICE_CREDENTIAL_PERMISSIONS = [
    ("DeviceCredentials", "view"),
    ("DeviceCredentials", "create"),
    ("DeviceCredentials", "edit"),
    ("DeviceCredentials", "delete"),
]


# ============================================================
# CADASTRO
# ============================================================

def cadastrar_permissoes() -> None:
    """
    Garante que todas as permissões de Device Credentials
    existam no catálogo global de permissões.

    A verificação é feita por:

        resource + action

    Portanto a migration é idempotente e pode ser executada
    novamente sem criar permissões duplicadas.
    """

    db = SessionLocal()

    try:

        print()
        print("=" * 72)
        print("DUET CORE - PERMISSÕES DE CREDENCIAIS DE DISPOSITIVO")
        print("=" * 72)
        print()


        criadas = 0
        existentes = 0


        for resource, action in DEVICE_CREDENTIAL_PERMISSIONS:

            permission = (
                db.query(Permission)
                .filter(
                    Permission.resource == resource,
                    Permission.action == action,
                )
                .first()
            )


            if permission:

                existentes += 1

                print(
                    f"[OK] {resource}:{action} "
                    "- já existe"
                )

                continue


            permission = Permission(
                resource=resource,
                action=action,
            )


            db.add(
                permission
            )


            # Flush permite detectar erro de persistência antes
            # do commit final, sem encerrar a transação.
            db.flush()


            criadas += 1

            print(
                f"[NOVO] {resource}:{action} "
                f"- ID {permission.id}"
            )


        # ====================================================
        # COMMIT ÚNICO
        # ====================================================
        #
        # Todas as permissões são confirmadas juntas.
        #
        # Em caso de erro antes daqui, rollback preserva o
        # estado anterior do catálogo.
        # ====================================================

        db.commit()


        # ====================================================
        # VALIDAÇÃO FINAL
        # ====================================================

        faltantes = []


        for resource, action in DEVICE_CREDENTIAL_PERMISSIONS:

            permission = (
                db.query(Permission)
                .filter(
                    Permission.resource == resource,
                    Permission.action == action,
                )
                .first()
            )


            if permission is None:

                faltantes.append(
                    f"{resource}:{action}"
                )


        if faltantes:

            raise RuntimeError(
                "Permissões ausentes após a migration: "
                + ", ".join(
                    faltantes
                )
            )


        print()
        print("[OK] Catálogo validado.")
        print()
        print(f"Permissões criadas: {criadas}")
        print(f"Permissões já existentes: {existentes}")
        print()
        print(
            "Nenhuma Role foi alterada automaticamente."
        )
        print(
            "Nenhum usuário recebeu novas permissões automaticamente."
        )
        print()


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    cadastrar_permissoes()
