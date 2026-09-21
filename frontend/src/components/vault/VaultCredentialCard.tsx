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


// ============================================================
// PROPS
// ============================================================

interface VaultCredentialCardProps {
    credential:
        VaultCredential;

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
    onEdit,
    onDelete,
}: VaultCredentialCardProps) {

    return (
        <div className="vault-credential-card">

            <div className="vault-credential-header">

                <h3>
                    {credential.name}
                </h3>


                <div className="vault-credential-actions">

                    <button
                        type="button"
                        className="secondary-button"
                        onClick={() =>
                            onEdit(
                                credential
                            )
                        }
                    >
                        Editar
                    </button>


                    <button
                        type="button"
                        className="secondary-button"
                        onClick={() =>
                            onDelete(
                                credential
                            )
                        }
                    >
                        Excluir
                    </button>

                </div>

            </div>


            {credential.fields.map(
                (field) => (

                    <p key={field.id}>

                        <strong>
                            {field.name}:
                        </strong>
                        {" "}

                        {field.is_secret
                            ? "********"
                            : field.value
                        }

                    </p>

                )
            )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultCredentialCard;