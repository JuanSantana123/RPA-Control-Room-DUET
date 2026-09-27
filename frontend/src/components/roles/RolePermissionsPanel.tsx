// ============================================================
// DUET CORE - ROLES - PERMISSIONS PANEL
// ============================================================
//
// Painel visual de configuração das permissões de uma Role.
//
// Responsabilidade:
// - apresentar a Role selecionada;
// - apresentar catálogo agrupado por recurso;
// - marcar permissões selecionadas;
// - encaminhar alterações de checkbox;
// - encaminhar solicitação de salvamento;
// - apresentar loading e estados vazios;
// - apresentar orientação quando nenhuma Role estiver selecionada.
//
// Este componente NÃO:
// - busca permissões;
// - persiste permissões;
// - executa chamadas HTTP;
// - altera diretamente regras de autorização.
//
// Toda operação é recebida através de props/callbacks.
// ============================================================

import type {
    Permission,
    Role,
} from "../../types/roles";

import { PanelSkeleton }
    from "../ui/Skeletons";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import AccessModeBadge from "../ui/AccessModeBadge";
import { Switch } from "../ui/Switch";


// ============================================================
// PROPS
// ============================================================

interface RolePermissionsPanelProps {
    canEdit: boolean;

    selectedRole:
        Role | null;

    permissions:
        Permission[];

    permissionsByResource:
        Record<
            string,
            Permission[]
        >;

    selectedPermissions:
        number[];

    loadingPermissions:
        boolean;

    savingPermissions:
        boolean;

    onTogglePermission:
        (permissionId: number) => void;

    onSave:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function RolePermissionsPanel({
    canEdit,
    selectedRole,
    permissions,
    permissionsByResource,
    selectedPermissions,
    loadingPermissions,
    savingPermissions,
    onTogglePermission,
    onSave,
}: RolePermissionsPanelProps) {

    // ========================================================
    // NENHUMA ROLE SELECIONADA
    // ========================================================

    if (!selectedRole) {

        return (
            <section className="roles-panel permissions-panel">

                <EmptyState
                    icon={<ShieldCheck />}
                    title="Selecione um perfil"
                    description="Escolha um perfil para consultar e configurar suas permissões."
                />

            </section>
        );
    }


    // ========================================================
    // ROLE SELECIONADA
    // ========================================================

    return (
        <section className="roles-panel permissions-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="permissions-panel-header">

                <div className="permissions-panel-heading">

                    <div className="permissions-panel-icon">
                        <ShieldCheck size={18} strokeWidth={1.8} aria-hidden="true" />
                    </div>


                    <div>

                        <h2>
                            {selectedRole.name}
                        </h2>

                        <p>
                            {canEdit
                                ? "Configure as permissões deste perfil"
                                : "Consulte as permissões efetivas deste perfil"}
                        </p>

                    </div>

                </div>


                {!canEdit && <AccessModeBadge />}

                {canEdit && permissions.length > 0 && (

                    <Button
                        variant="primary"
                        busy={savingPermissions}
                        loadingLabel="Salvando permissões"
                        onClick={onSave}
                    >
                        Salvar permissões
                    </Button>

                )}

            </div>


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            {loadingPermissions ? (
                <PanelSkeleton lines={5} />

            ) : permissions.length === 0 ? (

                <EmptyState
                    icon={<LockKeyhole />}
                    title="Nenhuma permissão disponível"
                    description="O Control Room não retornou permissões configuráveis para este perfil."
                />

            ) : (

                <div className="permissions-content">

                    {Object.entries(
                        permissionsByResource
                    ).map(
                        ([
                            resource,
                            resourcePermissions,
                        ]) => (

                            <div
                                key={resource}
                                className="permission-resource-group"
                            >

                                {/* ==============================
                                    RECURSO
                                    ============================== */}

                                <div className="permission-resource-header">

                                    <h3>
                                        {resource}
                                    </h3>

                                    <span className="permission-resource-count">
                                        {resourcePermissions.length} permissões
                                    </span>

                                </div>


                                {/* ==============================
                                    PERMISSÕES
                                    ============================== */}

                                <div className="permission-list">

                                    {resourcePermissions.map(
                                        (permission) => (

                                            <div
                                                key={
                                                    permission.id
                                                }
                                                className="permission-item"
                                            >

                                                <Switch
                                                    compact
                                                    label={permission.action}
                                                    checked={selectedPermissions.includes(permission.id)}
                                                    disabled={!canEdit}
                                                    onChange={() => onTogglePermission(permission.id)}
                                                />

                                            </div>

                                        )
                                    )}

                                </div>

                            </div>

                        )
                    )}

                </div>

            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RolePermissionsPanel;
