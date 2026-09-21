# ============================================================
# ROLES
# ============================================================
#
# Domínio responsável pelo gerenciamento de Roles e suas
# associações com o catálogo de permissões do Control Room.
#
# Camadas:
#
#     api/roles.py
#         HTTP e autorização.
#
#     roles/service.py
#         Regras de negócio e transações.
#
#     roles/repository.py
#         Acesso aos dados.
#
#     roles/serializers.py
#         Transformação dos modelos para contratos de saída.
#
# ============================================================