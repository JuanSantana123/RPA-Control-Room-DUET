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
import { Plus } from "lucide-react";
import { Button } from "../ui/Button";
import { Switch } from "../ui/Switch";


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

                <label htmlFor="vault-new-credential-name">
                    Nome da credencial
                </label>

                <br />

                <input
                    id="vault-new-credential-name"
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
                            aria-label={`Nome do campo ${index + 1}`}
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
                            aria-label={`Valor do campo ${index + 1}`}
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


                        <Switch
                            compact
                            className="vault-secret-label"
                            label="Secreto"
                            checked={field.is_secret}
                            disabled={creating}
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
                                creating ||
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
                disabled={creating}
            >
                <Plus size={15} strokeWidth={2} aria-hidden="true" />
                Adicionar campo
            </Button>


            <div className="vault-form-actions">

                <Button
                    onClick={onSave}
                    busy={creating}
                    loadingLabel="Salvando credencial"
                >
                    Salvar credencial
                </Button>


                <Button
                    variant="secondary"
                    onClick={onCancel}
                    disabled={creating}
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

export default VaultCredentialCreateForm;
