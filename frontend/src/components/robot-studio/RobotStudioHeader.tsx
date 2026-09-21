// ============================================================
// DUET CORE - ROBOT STUDIO - HEADER
// ============================================================
//
// Responsabilidade:
// - representar visualmente o cabeçalho superior do Robot
//   Studio;
// - apresentar nome do projeto;
// - apresentar estado do Checkout;
// - apresentar ações atuais de Checkout, Checkin,
//   Force Release e Salvar.
//
// IMPORTANTE:
// Este componente NÃO implementa nenhuma dessas operações.
// Ele preserva a interface atual e delega as ações através
// de callbacks.
//
// Este componente NÃO deve:
// - executar chamadas HTTP;
// - adquirir ou liberar Checkout diretamente;
// - salvar workspace diretamente;
// - alterar permissões;
// - implementar regras de negócio.
//
// Todos os estados e permissões continuam sendo calculados
// pelo Robot Studio.
// ============================================================

import type {
    CSSProperties,
} from "react";

import {
    ArrowLeft,
    Save,
} from "lucide-react";

import type {
    ProjectCheckoutState,
} from "../../types/robotStudio";


interface RobotStudioHeaderStyles {
    topbar: CSSProperties;
    topbarLeft: CSSProperties;
    iconButton: CSSProperties;
    eyebrow: CSSProperties;
    robotTitle: CSSProperties;
    topbarRight: CSSProperties;
    checkoutState: CSSProperties;
    checkoutButton: CSSProperties;
    checkinButton: CSSProperties;
    forceReleaseButton: CSSProperties;
    saveState: CSSProperties;
    primaryButton: CSSProperties;
}


interface RobotStudioHeaderProps {
    projectName: string;

    loadingCheckout: boolean;
    checkoutActionLoading: boolean;

    checkoutState: ProjectCheckoutState;

    ownsCheckout: boolean;

    canCheckout: boolean;
    canForceCheckoutRelease: boolean;
    canWriteWorkspace: boolean;

    dirty: boolean;
    hasActiveFile: boolean;

    styles: RobotStudioHeaderStyles;

    onBack: () => void;
    onCheckout: () => void;
    onCheckin: () => void;
    onForceRelease: () => void;
    onSave: () => void;
}


function RobotStudioHeader({
    projectName,
    loadingCheckout,
    checkoutActionLoading,
    checkoutState,
    ownsCheckout,
    canCheckout,
    canForceCheckoutRelease,
    canWriteWorkspace,
    dirty,
    hasActiveFile,
    styles,
    onBack,
    onCheckout,
    onCheckin,
    onForceRelease,
    onSave,
}: RobotStudioHeaderProps) {

    return (
        <header style={styles.topbar}>

            <div style={styles.topbarLeft}>

                <button
                    type="button"
                    onClick={onBack}
                    style={styles.iconButton}
                    title="Voltar para Robôs"
                    aria-label="Voltar para Robôs"
                >
                    <ArrowLeft size={18} />
                </button>


                <div>
                    <div style={styles.eyebrow}>
                        DUET STUDIO
                    </div>

                    <div style={styles.robotTitle}>
                        {projectName}
                    </div>
                </div>

            </div>


            <div style={styles.topbarRight}>

                {/* Mostra o estado atual do Checkout. */}
                <span style={styles.checkoutState}>

                    {loadingCheckout
                        ? "Verificando Checkout..."

                        : ownsCheckout
                            ? "Checkout: você"

                            : checkoutState.checked_out
                                ? `Checkout: ${
                                    checkoutState.checkout?.user_name ||
                                    "outro usuário"
                                }`

                                : "Somente leitura"}

                </span>


                {/* Se o projeto estiver livre, mostra Checkout. */}
                {canCheckout &&
                    !loadingCheckout &&
                    !checkoutState.checked_out && (

                    <button
                        type="button"
                        onClick={onCheckout}
                        disabled={checkoutActionLoading}
                        style={{
                            ...styles.checkoutButton,

                            opacity:
                                checkoutActionLoading
                                    ? 0.6
                                    : 1,

                            cursor:
                                checkoutActionLoading
                                    ? "not-allowed"
                                    : "pointer",
                        }}
                    >
                        {checkoutActionLoading
                            ? "Aguarde..."
                            : "Checkout"}
                    </button>
                )}


                {/* Se EU possuir Checkout, mostra Checkin. */}
                {canCheckout &&
                    !loadingCheckout &&
                    ownsCheckout && (

                    <button
                        type="button"
                        onClick={onCheckin}
                        disabled={
                            checkoutActionLoading ||
                            dirty
                        }
                        title={
                            dirty
                                ? "Salve as alterações antes do Checkin."
                                : "Liberar Checkout"
                        }
                        style={{
                            ...styles.checkinButton,

                            opacity:
                                checkoutActionLoading ||
                                dirty
                                    ? 0.55
                                    : 1,

                            cursor:
                                checkoutActionLoading ||
                                dirty
                                    ? "not-allowed"
                                    : "pointer",
                        }}
                    >
                        {checkoutActionLoading
                            ? "Aguarde..."
                            : "Checkin"}
                    </button>
                )}


                {/* Force Release aparece somente para usuários autorizados. */}
                {canForceCheckoutRelease &&
                    !loadingCheckout &&
                    checkoutState.checked_out &&
                    !ownsCheckout && (

                    <button
                        type="button"
                        onClick={onForceRelease}
                        disabled={checkoutActionLoading}
                        style={{
                            ...styles.forceReleaseButton,

                            opacity:
                                checkoutActionLoading
                                    ? 0.6
                                    : 1,

                            cursor:
                                checkoutActionLoading
                                    ? "not-allowed"
                                    : "pointer",
                        }}
                        title="Forçar liberação do Checkout"
                    >
                        {checkoutActionLoading
                            ? "Aguarde..."
                            : "Force Release"}
                    </button>
                )}


                {/* Estado dos arquivos. */}
                <span
                    style={{
                        ...styles.saveState,

                        color:
                            dirty
                                ? "#e2c08d"
                                : "#9aa0a6",
                    }}
                >
                    {dirty
                        ? "Alterações não salvas"
                        : "Salvo"}
                </span>


                {/* Salvar só funciona com Checkout e alteração. */}
                <button
                    type="button"
                    onClick={onSave}
                    disabled={
                        !canWriteWorkspace ||
                        !dirty ||
                        !hasActiveFile
                    }
                    style={{
                        ...styles.primaryButton,

                        opacity:
                            !canWriteWorkspace ||
                            !dirty ||
                            !hasActiveFile
                                ? 0.5
                                : 1,

                        cursor:
                            !canWriteWorkspace ||
                            !dirty ||
                            !hasActiveFile
                                ? "not-allowed"
                                : "pointer",
                    }}
                >
                    <Save
                        size={15}
                        strokeWidth={1.9}
                    />

                    Salvar
                </button>

            </div>

        </header>
    );
}


export default RobotStudioHeader;