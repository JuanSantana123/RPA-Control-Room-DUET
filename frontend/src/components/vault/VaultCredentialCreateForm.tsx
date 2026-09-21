// ============================================================
// DUET CORE - VAULT - CREDENTIAL CREATE FORM
// ============================================================
//
// Formulário visual para criação de uma credencial.
//
// Responsabilidade:
// - receber nome;
// - apresentar campos dinâmicos;
// - alterar nome/valor/tipo secreto;
// - adicionar/remover campos;
// - encaminhar salvamento/cancelamento.
//
// Este componente NÃO:
// - valida dados;
// - executa POST;
// - define folder_id;
// - controla mensagens.
//
// Essas responsabilidades permanecem no hook
// useVaultCredentialCreation.
// ============================================================

import type {
    NewCredentialField,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface VaultCredentialCreateFormProps {
    name:
        string;

    setName:
        (value: string) => void;

    fields:
        NewCredentialField[];

    creating:
        boolean;

    onUpdateField:
        (
            index: number,
            property:
                keyof NewCredentialField,
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

function VaultCredentialCreateForm({
    name,
    setName,
    fields,
    creating,
    onUpdateField,
    onAddField,
    onRemoveField,
    onSave,
    onCancel,
}: VaultCredentialCreateFormProps) {

    return (
        <section className="content-panel vault-form-panel">

            <h3>
                Nova credencial
            </h3>


            <div className="vault-form-group">

                <label>
                    Nome da credencial
                </label>

                <br />

                <input
                    type="text"
                    className="form-input"
                    placeholder="Ex.: usuario_1"
                    value={name}
                    disabled={creating}
                    onChange={(event) =>
                        setName(
                            event.target.value
                        )
                    }
                />

            </div>


            <h4>
                Campos
            </h4>


            {fields.map(
                (field, index) => (

                    <div
                        key={index}
                        className="vault-field-row"
                    >

                        <input
                            type="text"
                            className="form-input"
                            placeholder="Nome do campo"
                            value={field.name}
                            disabled={creating}
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
                            placeholder="Valor"
                            value={field.value}
                            disabled={creating}
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
                                disabled={creating}
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
                                creating ||
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
                disabled={creating}
            >
                + Adicionar campo
            </button>


            <div className="vault-form-actions">

                <button
                    type="button"
                    className="primary-button"
                    onClick={onSave}
                    disabled={creating}
                >
                    {creating
                        ? "Salvando..."
                        : "Salvar credencial"
                    }
                </button>


                <button
                    type="button"
                    className="secondary-button"
                    onClick={onCancel}
                    disabled={creating}
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

export default VaultCredentialCreateForm;