// ============================================================
// DUET CORE - VAULT - CREDENTIAL CARD
// ============================================================
//
// Card de uma credencial armazenada no Vault.
//
// Responsabilidade:
// - apresentar nome;
// - apresentar campos;
// - mascarar campos secretos;
// - disponibilizar editar/excluir.
//
// SEGURANÇA:
// Campos com is_secret=true são sempre apresentados como
// "********". O valor recebido nunca é colocado em texto aberto
// por este componente.
// ============================================================

import type {
    VaultCredential,
} from "../../types/vault";
import { Clock3, Copy, EyeOff, LockKeyhole } from "lucide-react";
import { Button, IconButton } from "../ui/Button";
import { useInteraction } from "../../context/useInteraction";
import { parseApiDateTime } from "../../utils/dateTime";


// ============================================================
// PROPS
// ============================================================

interface VaultCredentialCardProps {
    credential:
        VaultCredential;

    canEdit: boolean;
    canDelete: boolean;

    onEdit:
        (credential: VaultCredential) =>
            void;

    onDelete:
        (credential: VaultCredential) =>
            void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultCredentialCard({
    credential,
    canEdit,
    canDelete,
    onEdit,
    onDelete,
}: VaultCredentialCardProps) {

    const { notify } = useInteraction();
    const secretCount = credential.fields.filter((field) => field.is_secret).length;
    const updatedAt = parseApiDateTime(credential.updated_at);

    const copyPublicValue = async (fieldName: string, value: string) => {
        try {
            await navigator.clipboard.writeText(value);
            notify({
                tone: "success",
                title: "Valor copiado",
                message: `O campo não secreto “${fieldName}” foi copiado.`,
            });
        } catch {
            notify({
                tone: "danger",
                title: "Não foi possível copiar",
                message: "O navegador bloqueou o acesso à área de transferência.",
            });
        }
    };

    return (
        <article className="vault-credential-card">

            <div className="vault-credential-header">

                <h3>
                    <span className="vault-credential-title-icon">
                        <LockKeyhole size={16} strokeWidth={1.8} aria-hidden="true" />
                    </span>
                    {credential.name}
                </h3>


                {(canEdit || canDelete) && <div className="vault-credential-actions">

                    {canEdit && <Button
                        variant="secondary"
                        size="sm"
                        onClick={() =>
                            onEdit(
                                credential
                            )
                        }
                    >
                        Editar
                    </Button>}


                    {canDelete && <Button
                        variant="danger"
                        size="sm"
                        onClick={() =>
                            onDelete(
                                credential
                            )
                        }
                    >
                        Excluir
                    </Button>}

                </div>}

            </div>


            <div className="vault-credential-security-summary">
                <span>
                    <EyeOff size={14} aria-hidden="true" />
                    {secretCount} {secretCount === 1 ? "campo protegido" : "campos protegidos"}
                </span>
                <span title={updatedAt?.toLocaleString("pt-BR") || "Data não registrada"}>
                    <Clock3 size={14} aria-hidden="true" />
                    {updatedAt ? `Atualizada em ${updatedAt.toLocaleDateString("pt-BR")}` : "Atualização não registrada"}
                </span>
            </div>

            <dl className="vault-credential-fields">
                {credential.fields.map((field) => (
                    <div key={field.id ?? field.name} className="vault-credential-field">
                        <dt>{field.name}</dt>
                        <dd className={field.is_secret ? "vault-credential-secret-value" : undefined}>
                            <span title={field.is_secret ? "Valor protegido" : field.value}>
                                {field.is_secret ? "••••••••" : field.value || "—"}
                            </span>
                            {!field.is_secret && field.value && (
                                <IconButton
                                    size="sm"
                                    label={`Copiar ${field.name}`}
                                    tooltip={`Copiar valor não secreto de ${field.name}`}
                                    icon={<Copy size={14} aria-hidden="true" />}
                                    onClick={() => void copyPublicValue(field.name, field.value)}
                                />
                            )}
                        </dd>
                    </div>
                ))}
            </dl>

        </article>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultCredentialCard;
