// ============================================================
// DUET CORE - ROLES PAGE
// ============================================================
//
// Página principal da área de controle de acesso por Roles.
//
// Responsabilidade:
// - compor a interface da área de Roles;
// - conectar os hooks de dados aos componentes visuais;
// - coordenar criação, seleção, exclusão e permissões;
// - apresentar mensagens globais da operação.
//
// Arquitetura:
//
// Roles
//   │
//   ├── useRolesData
//   │     ├── listagem
//   │     ├── criação
//   │     └── exclusão
//   │
//   ├── useRolePermissions
//   │     ├── catálogo de permissões
//   │     ├── Role selecionada
//   │     ├── seleção de permissões
//   │     └── persistência das permissões
//   │
//   ├── RolesHeader
//   ├── RoleCreatePanel
//   ├── RolesList
//   └── RolePermissionsPanel
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - concentra regras de CRUD;
// - persiste permissões;
// - implementa individualmente os cards;
// - implementa individualmente os checkboxes.
//
// A página funciona somente como camada de composição entre
// comportamento e apresentação.
// ============================================================

import RolesHeader
    from "../components/roles/RolesHeader";

import RoleCreatePanel
    from "../components/roles/RoleCreatePanel";

import RolesList
    from "../components/roles/RolesList";

import RolePermissionsPanel
    from "../components/roles/RolePermissionsPanel";

import {
    useRolesData,
} from "../hooks/roles/useRolesData";

import {
    useRolePermissions,
} from "../hooks/roles/useRolePermissions";

import {
    groupPermissionsByResource,
} from "../utils/rolePermissions";


// ============================================================
// PÁGINA DE ROLES
// ============================================================

function Roles() {

    // ========================================================
    // ROLES
    // ========================================================
    //
    // Responsável pela coleção principal, criação,
    // exclusão e mensagens da página.
    // ========================================================

    const {
        roles,
        loadingRoles,

        showCreateForm,

        roleName,
        setRoleName,

        roleDescription,
        setRoleDescription,

        creatingRole,

        error,
        success,

        setError,
        setSuccess,

        abrirFormulario,
        cancelarCriacao,
        criarRole,
        excluirRole,
    } = useRolesData();


    // ========================================================
    // PERMISSÕES
    // ========================================================
    //
    // Compartilha os setters de mensagem com useRolesData
    // para preservar a área única de mensagens existente
    // na página original.
    // ========================================================

    const {
        selectedRole,

        permissions,
        selectedPermissions,

        loadingPermissions,
        savingPermissions,

        selecionarRole,
        alternarPermissao,
        salvarPermissoes,

        handleRoleDeleted,
    } = useRolePermissions({
        setError,
        setSuccess,
    });


    // ========================================================
    // AGRUPAMENTO DE PERMISSÕES
    // ========================================================
    //
    // Mantém a transformação anteriormente executada
    // diretamente dentro de Roles.tsx.
    // ========================================================

    const permissionsByResource =
        groupPermissionsByResource(
            permissions
        );


    // ========================================================
    // EXCLUSÃO DE ROLE
    // ========================================================
    //
    // useRolesData executa a exclusão.
    //
    // useRolePermissions recebe a notificação da exclusão
    // para limpar o painel caso a Role removida seja justamente
    // a Role que estava selecionada.
    //
    // Isso preserva o comportamento existente sem acoplar
    // os dois hooks diretamente.
    // ========================================================

    const handleDeleteRole =
        async (
            roleId: number
        ) => {

            await excluirRole(
                roleId,
                handleRoleDeleted
            );
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="roles-page">

            {/* ==================================================
                CABEÇALHO PRINCIPAL
                ================================================== */}

            <RolesHeader
                showCreateForm={
                    showCreateForm
                }
                onCreate={
                    abrirFormulario
                }
            />


            {/* ==================================================
                CRIAÇÃO DE ROLE
                ================================================== */}

            {showCreateForm && (

                <RoleCreatePanel
                    roleName={
                        roleName
                    }
                    setRoleName={
                        setRoleName
                    }
                    roleDescription={
                        roleDescription
                    }
                    setRoleDescription={
                        setRoleDescription
                    }
                    creatingRole={
                        creatingRole
                    }
                    onCancel={
                        cancelarCriacao
                    }
                    onCreate={
                        criarRole
                    }
                />

            )}


            {/* ==================================================
                MENSAGENS
                ================================================== */}

            {error && (

                <div className="roles-alert roles-alert-error">

                    <span>
                        ⚠
                    </span>

                    <span>
                        {error}
                    </span>

                </div>

            )}


            {success && (

                <div className="roles-alert roles-alert-success">

                    <span>
                        ✓
                    </span>

                    <span>
                        {success}
                    </span>

                </div>

            )}


            {/* ==================================================
                WORKSPACE
                ================================================== */}

            <div className="roles-workspace">

                {/* ==============================================
                    LISTA DE ROLES
                    ============================================== */}

                <RolesList
                    roles={
                        roles
                    }
                    selectedRole={
                        selectedRole
                    }
                    loadingRoles={
                        loadingRoles
                    }
                    onConfigure={
                        selecionarRole
                    }
                    onDelete={
                        handleDeleteRole
                    }
                />


                {/* ==============================================
                    CONFIGURAÇÃO DE PERMISSÕES
                    ============================================== */}

                <RolePermissionsPanel
                    selectedRole={
                        selectedRole
                    }
                    permissions={
                        permissions
                    }
                    permissionsByResource={
                        permissionsByResource
                    }
                    selectedPermissions={
                        selectedPermissions
                    }
                    loadingPermissions={
                        loadingPermissions
                    }
                    savingPermissions={
                        savingPermissions
                    }
                    onTogglePermission={
                        alternarPermissao
                    }
                    onSave={
                        salvarPermissoes
                    }
                />

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Roles;