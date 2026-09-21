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

                <label>
                    Nome da credencial
                </label>

                <br />

                <input
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


                        <label className="vault-secret-label">

                            <input
                                type="checkbox"
                                checked={
                                    field.is_secret
                                }
                                disabled={updating}
                                onChange={(event) =>
                                    onUpdateField(
                                        index,
                                        "is_secret",
                                        event.target.checked
                                    )
                                }
                            />

                            {" "}
                            Secreto

                        </label>


                        <button
                            type="button"
                            className="secondary-button"
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
                        </button>

                    </div>

                )
            )}


            <button
                type="button"
                className="secondary-button"
                onClick={onAddField}
            >
                + Adicionar campo
            </button>


            <div className="vault-form-actions">

                <button
                    type="button"
                    className="primary-button"
                    onClick={onSave}
                >
                    {updating
                        ? "Salvando..."
                        : "Salvar alterações"
                    }
                </button>


                <button
                    type="button"
                    className="secondary-button"
                    onClick={onCancel}
                    disabled={updating}
                >
                    Cancelar
                </button>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultCredentialEditForm;