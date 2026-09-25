// ============================================================
// DUET CORE - DEVICE CREDENTIAL FORM
// ============================================================
//
// Formulário visual reutilizado para:
//
// - criar uma Credencial de Dispositivo;
// - editar uma Credencial de Dispositivo.
//
// RESPONSABILIDADE:
//
// - renderizar os campos da identidade Windows;
// - encaminhar alterações dos campos para o componente pai;
// - disparar salvar/cancelar;
// - apresentar a orientação correta sobre a senha.
//
// ESTE COMPONENTE NÃO:
//
// - chama API;
// - acessa o Vault diretamente;
// - criptografa/descriptografa senha;
// - mantém senha em storage;
// - conhece Agents/Devices associados;
// - conhece permissões/RBAC;
// - conhece pastas das Credenciais de Automação.
//
// SEGURANÇA:
//
// A senha digitada existe somente no estado controlado pelo
// componente pai enquanto o formulário estiver aberto.
//
// Não existe ação "mostrar senha".
// ============================================================


import type {
    FormEvent,
} from "react";


import type {
    DeviceCredentialFormData,
} from "../../../types/deviceCredentials";


// ============================================================
// MODO DO FORMULÁRIO
// ============================================================

export type DeviceCredentialFormMode =
    | "create"
    | "edit";


// ============================================================
// PROPS
// ============================================================

interface DeviceCredentialFormProps {

    // Define se o formulário está criando ou editando.
    mode:
        DeviceCredentialFormMode;

    // Valores atuais do formulário.
    formData:
        DeviceCredentialFormData;

    // Informa se a credencial em edição já possui senha
    // armazenada no Vault.
    //
    // É relevante somente no modo "edit".
    hasExistingPassword?:
        boolean;

    // Bloqueia os controles enquanto a operação está sendo
    // persistida no backend.
    saving:
        boolean;

    // Atualiza somente o campo informado.
    onChange:
        (
            field: keyof DeviceCredentialFormData,
            value: string
        ) => void;

    // Salva os dados atuais.
    // O componente visual não utiliza o valor retornado pelo callback.
    //
    // O workflow pode retornar, por exemplo, Promise<boolean> para
    // informar internamente se a operação foi concluída com sucesso.
    // Para o formulário, esse retorno é irrelevante.
    onSubmit:
        () => void | Promise<unknown>;

    // Fecha o formulário sem salvar.
    onCancel:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function DeviceCredentialForm({
    mode,
    formData,
    hasExistingPassword = false,
    saving,
    onChange,
    onSubmit,
    onCancel,
}: DeviceCredentialFormProps) {

    // ========================================================
    // TEXTO CONTEXTUAL
    // ========================================================

    const isEditing =
        mode === "edit";


    const title =
        isEditing
            ? "Editar credencial de dispositivo"
            : "Nova credencial de dispositivo";


    const submitLabel =
        saving
            ? (
                isEditing
                    ? "Salvando..."
                    : "Criando..."
            )
            : (
                isEditing
                    ? "Salvar alterações"
                    : "Criar credencial"
            );


    // ========================================================
    // SUBMIT
    // ========================================================
    //
    // O form impede o reload nativo do navegador e delega a
    // operação para o componente pai.
    // ========================================================

    const handleSubmit =
        (
            event: FormEvent<HTMLFormElement>
        ) => {

            event.preventDefault();

            void onSubmit();
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <form
            className="vault-form-panel device-credential-form"
            onSubmit={
                handleSubmit
            }
        >

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="device-credential-form-heading">

                <div>

                    <h3>
                        {title}
                    </h3>

                    <p>
                        Identidade Windows utilizada para execução
                        controlada em Devices.
                    </p>

                </div>

            </div>


            {/* ==================================================
                NOME
                ================================================== */}

            <div className="vault-form-group">

                <label
                    htmlFor="device-credential-name"
                >
                    Nome da credencial
                </label>

                <input
                    id="device-credential-name"
                    className="form-input"
                    type="text"
                    value={
                        formData.name
                    }
                    disabled={
                        saving ||
                        isEditing
                    }
                    autoComplete="off"
                    placeholder="Ex.: Windows - Pilucos"
                    onChange={
                        (event) => onChange(
                            "name",
                            event.target.value
                        )
                    }
                />

                {isEditing && (

                    <small className="device-credential-field-help">
                        O nome permanece fixo durante a edição.
                    </small>

                )}

            </div>


            {/* ==================================================
                IDENTIDADE WINDOWS
                ================================================== */}

            <div className="device-credential-form-grid">

                {/* ----------------------------------------------
                    DOMÍNIO
                    ---------------------------------------------- */}

                <div className="vault-form-group">

                    <label
                        htmlFor="device-credential-domain"
                    >
                        Domínio
                    </label>

                    <input
                        id="device-credential-domain"
                        className="form-input"
                        type="text"
                        value={
                            formData.domain
                        }
                        disabled={
                            saving
                        }
                        autoComplete="off"
                        placeholder="Ex.: DESKTOP-7T4IJEQ"
                        onChange={
                            (event) => onChange(
                                "domain",
                                event.target.value
                            )
                        }
                    />

                </div>


                {/* ----------------------------------------------
                    USUÁRIO
                    ---------------------------------------------- */}

                <div className="vault-form-group">

                    <label
                        htmlFor="device-credential-username"
                    >
                        Usuário
                    </label>

                    <input
                        id="device-credential-username"
                        className="form-input"
                        type="text"
                        value={
                            formData.username
                        }
                        disabled={
                            saving
                        }
                        autoComplete="off"
                        placeholder="Ex.: Pilucos"
                        onChange={
                            (event) => onChange(
                                "username",
                                event.target.value
                            )
                        }
                    />

                </div>

            </div>


            {/* ==================================================
                SENHA
                ==================================================

                IMPORTANTE:

                No modo de edição o campo nunca é preenchido
                automaticamente com "********".

                Campo vazio significa:
                    manter a senha existente.

                Campo preenchido significa:
                    substituir a senha existente.
                ================================================== */}

            <div className="vault-form-group">

                <label
                    htmlFor="device-credential-password"
                >
                    Senha
                </label>

                <input
                    id="device-credential-password"
                    className="form-input"
                    type="password"
                    value={
                        formData.password
                    }
                    disabled={
                        saving
                    }
                    autoComplete="new-password"
                    placeholder={
                        isEditing
                            ? (
                                hasExistingPassword
                                    ? "Deixe em branco para manter a senha atual"
                                    : "Informe uma senha"
                            )
                            : "Informe a senha da conta Windows"
                    }
                    onChange={
                        (event) => onChange(
                            "password",
                            event.target.value
                        )
                    }
                />


                {isEditing && hasExistingPassword && (

                    <small className="device-credential-field-help">
                        A senha atual permanece protegida no Vault.
                        Preencha este campo somente para substituí-la.
                    </small>

                )}

            </div>


            {/* ==================================================
                INFORMAÇÃO DE SEGURANÇA
                ================================================== */}

            <div
                className="device-credential-security-note"
                role="note"
            >

                <strong>
                    Segurança
                </strong>

                <span>
                    A senha não poderá ser visualizada novamente
                    depois que a credencial for salva.
                </span>

            </div>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <div className="vault-form-actions">

                <button
                    type="button"
                    className="secondary-button"
                    disabled={
                        saving
                    }
                    onClick={
                        onCancel
                    }
                >
                    Cancelar
                </button>


                <button
                    type="submit"
                    className="primary-button"
                    disabled={
                        saving
                    }
                >
                    {submitLabel}
                </button>

            </div>

        </form>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DeviceCredentialForm;
