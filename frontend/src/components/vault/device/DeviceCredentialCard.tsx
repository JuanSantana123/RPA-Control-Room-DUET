// ============================================================
// DUET CORE - DEVICE CREDENTIAL CARD
// ============================================================
//
// Card visual de uma Credencial de Dispositivo.
//
// RESPONSABILIDADE:
//
// - apresentar a identificação lógica da credencial;
// - apresentar a conta Windows no formato domínio\usuário;
// - informar se existe senha protegida no Vault;
// - apresentar data da última atualização;
// - disponibilizar ações de editar e excluir.
//
// ESTE COMPONENTE NÃO:
//
// - chama API;
// - altera estado global;
// - abre formulário;
// - executa confirmação de exclusão;
// - manipula senha;
// - descriptografa segredo;
// - conhece Agents/Devices associados;
// - conhece pastas das Credenciais de Automação.
//
// As ações são encaminhadas ao componente pai através de
// callbacks explícitos.
// ============================================================


import {
    KeyRound,
    Monitor,
    Pencil,
    ShieldCheck,
    Trash2,
} from "lucide-react";


import type {
    DeviceCredential,
} from "../../../types/deviceCredentials";


// ============================================================
// PROPS
// ============================================================

interface DeviceCredentialCardProps {

    // Credencial segura recebida do backend.
    credential:
        DeviceCredential;

    // Indica se esta credencial está sendo excluída.
    deleting:
        boolean;

    // Solicita abertura do fluxo de edição.
    onEdit:
        (
            credential: DeviceCredential
        ) => void;

    // Solicita exclusão.
    //
    // A confirmação da intenção pertence ao componente pai.
    onDelete:
        (
            credential: DeviceCredential
        ) => void;
}


// ============================================================
// FORMATAR CONTA WINDOWS
// ============================================================
//
// Exemplo:
//
//     DESKTOP-7T4IJEQ\Pilucos
//
// Caso o domínio esteja vazio por algum dado legado, exibimos
// somente o usuário para não criar uma barra invertida inválida.
// ============================================================

const formatWindowsAccount =
    (
        credential: DeviceCredential
    ): string => {

        const domain =
            credential.domain?.trim() || "";

        const username =
            credential.username?.trim() || "";


        if (
            domain &&
            username
        ) {

            return `${domain}\\${username}`;
        }


        return (
            username ||
            domain ||
            "-"
        );
    };


// ============================================================
// FORMATAR DATA
// ============================================================
//
// As datas chegam da API em formato serializável.
//
// Se o backend não possuir data, exibimos "-".
// ============================================================

const formatDate =
    (
        value:
            string | null
    ): string => {

        if (
            !value
        ) {

            return "-";
        }


        const date =
            new Date(
                value
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {

            return "-";
        }


        return date.toLocaleString(
            "pt-BR"
        );
    };


// ============================================================
// COMPONENTE
// ============================================================

function DeviceCredentialCard({
    credential,
    deleting,
    onEdit,
    onDelete,
}: DeviceCredentialCardProps) {

    const windowsAccount =
        formatWindowsAccount(
            credential
        );


    return (

        <article className="device-credential-card">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="device-credential-card-header">

                <div className="device-credential-card-identity">

                    <div
                        className="device-credential-card-icon"
                        aria-hidden="true"
                    >

                        <Monitor
                            size={18}
                        />

                    </div>


                    <div className="device-credential-card-title">

                        <h3>
                            {credential.name}
                        </h3>

                        <span>
                            Credencial Windows
                        </span>

                    </div>

                </div>


                {/* ==============================================
                    AÇÕES
                    ============================================== */}

                <div className="device-credential-card-actions">

                    <button
                        type="button"
                        className="secondary-button device-credential-action-button"
                        disabled={
                            deleting
                        }
                        title={`Editar ${credential.name}`}
                        onClick={
                            () => onEdit(
                                credential
                            )
                        }
                    >

                        <Pencil
                            size={14}
                        />

                        Editar

                    </button>


                    <button
                        type="button"
                        className="device-credential-delete-button"
                        disabled={
                            deleting
                        }
                        title={`Excluir ${credential.name}`}
                        onClick={
                            () => onDelete(
                                credential
                            )
                        }
                    >

                        <Trash2
                            size={14}
                        />

                        {
                            deleting
                                ? "Excluindo..."
                                : "Excluir"
                        }

                    </button>

                </div>

            </div>


            {/* ==================================================
                CONTA WINDOWS
                ================================================== */}

            <div className="device-credential-card-account">

                <span className="device-credential-card-label">
                    Conta Windows
                </span>

                <strong>
                    {windowsAccount}
                </strong>

            </div>


            {/* ==================================================
                METADADOS
                ================================================== */}

            <div className="device-credential-card-meta">

                {/* ----------------------------------------------
                    SENHA
                    ---------------------------------------------- */}

                <div className="device-credential-card-meta-item">

                    <div
                        className="device-credential-card-meta-icon"
                        aria-hidden="true"
                    >

                        {
                            credential.has_password
                                ? (
                                    <ShieldCheck
                                        size={16}
                                    />
                                )
                                : (
                                    <KeyRound
                                        size={16}
                                    />
                                )
                        }

                    </div>


                    <div>

                        <span>
                            Senha
                        </span>

                        <strong>
                            {
                                credential.has_password
                                    ? "Protegida no Vault"
                                    : "Não configurada"
                            }
                        </strong>

                    </div>

                </div>


                {/* ----------------------------------------------
                    ÚLTIMA ATUALIZAÇÃO
                    ---------------------------------------------- */}

                <div className="device-credential-card-meta-item">

                    <div>

                        <span>
                            Última atualização
                        </span>

                        <strong>
                            {
                                formatDate(
                                    credential.updated_at
                                )
                            }
                        </strong>

                    </div>

                </div>

            </div>

        </article>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DeviceCredentialCard;
