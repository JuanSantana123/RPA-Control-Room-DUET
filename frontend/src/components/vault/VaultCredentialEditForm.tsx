// ============================================================
// DUET CORE - VAULT - CREDENTIAL EDIT FORM
// ============================================================
//
// Formulário visual para edição dos campos de uma credencial.
//
// Responsabilidade:
// - exibir o nome imutável;
// - apresentar campos editáveis;
// - representar campos secretos existentes sem expor valor;
// - encaminhar alterações;
// - adicionar/remover campos;
// - salvar ou cancelar.
//
// REGRA CRÍTICA:
// O placeholder de um segredo com keep_existing=true informa
// que o campo pode permanecer vazio para preservar o segredo.
//
// Este componente NÃO:
// - conhece o valor real de um segredo;
// - executa PUT;
// - altera o nome da credencial.
// ============================================================

import type {
    EditCredentialField,
    VaultCredential,
} from "../../types/vault";
import { Plus } from "lucide-react";
import { Button } from "../ui/Button";
import { Switch } from "../ui/Switch";


// ============================================================
// PROPS
// ============================================================

interface VaultCredentialEditFormProps {
    credential:
        VaultCredential;

    fields:
        EditCredentialField[];

    updating:
        boolean;

    onUpdateField:
        (
            index: number,
            property:
                keyof EditCredentialField,
            value:
                string | boolean
        ) => void;

    onAddField:
        () => void;

    onRemoveField:
        (index: number) => void;

    onSave:
        () => void | Promise<void>;

    onCancel:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultCredentialEditForm({
    credential,
    fields,
    updating,
    onUpdateField,
    onAddField,
    onRemoveField,
    onSave,
    onCancel,
}: VaultCredentialEditFormProps) {

    return (
        <section className="content-panel vault-form-panel">

            <h3>
                Editar credencial
            </h3>


            {/* ==================================================
                NOME IMUTÁVEL
                ================================================== */}

            <div className="vault-form-group">

                <label htmlFor="vault-edit-credential-name">
                    Nome da credencial
                </label>

                <br />

                <input
                    id="vault-edit-credential-name"
                    type="text"
                    className="form-input"
                    value={
                        credential.name
                    }
                    disabled
                />

            </div>


            <h4>
                Campos
            </h4>


            {fields.map(
                (field, index) => (

                    <div
                        key={
                            field.id ??
                            `novo-${index}`
                        }
                        className="vault-field-row"
                    >

                        <input
                            type="text"
                            aria-label={`Nome do campo ${index + 1}`}
                            className="form-input"
                            placeholder="Nome do campo"
                            value={field.name}
                            disabled={updating}
                            onChange={(event) =>
                                onUpdateField(
                                    index,
                                    "name",
                                    event.target.value
                                )
                            }
                        />


                        <input
                            type={
                                field.is_secret
                                    ? "password"
                                    : "text"
                            }
                            aria-label={`Valor do campo ${index + 1}`}
                            className="form-input"
                            placeholder={
                                field.is_secret &&
                                field.keep_existing
                                    ? "Deixe vazio para manter o atual"
                                    : "Valor"
                            }
                            value={field.value}
                            disabled={updating}
                            onChange={(event) =>
                                onUpdateField(
                                    index,
                                    "value",
                                    event.target.value
                                )
                            }
                        />


                        <Switch
                            compact
                            className="vault-secret-label"
                            label="Secreto"
                            checked={field.is_secret}
                            disabled={updating}
                            onChange={(event) =>
                                onUpdateField(index, "is_secret", event.target.checked)
                            }
                        />


                        <Button
                            variant="danger"
                            size="sm"
                            onClick={() =>
                                onRemoveField(
                                    index
                                )
                            }
                            disabled={
                                updating ||
                                fields.length === 1
                            }
                        >
                            Remover
                        </Button>

                    </div>

                )
            )}


            <Button
                variant="secondary"
                size="sm"
                onClick={onAddField}
            >
                <Plus size={15} strokeWidth={2} aria-hidden="true" />
                Adicionar campo
            </Button>


            <div className="vault-form-actions">

                <Button
                    onClick={onSave}
                    busy={updating}
                    loadingLabel="Salvando alterações"
                >
                    Salvar alterações
                </Button>


                <Button
                    variant="secondary"
                    onClick={onCancel}
                    disabled={updating}
                >
                    Cancelar
                </Button>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultCredentialEditForm;
