// ============================================================
// DUET CORE - EXECUTIONS - STATUS BADGE
// ============================================================
//
// Componente visual responsável por representar o status
// atual de uma execução.
//
// Responsabilidade:
// - escolher label;
// - escolher classe CSS;
// - escolher ícone correspondente ao status.
//
// Origem dos dados:
// - recebe somente o status através de props.
//
// Dependências:
// - lucide-react para os ícones;
// - executionFormatters para fallback de status desconhecido.
//
// Este componente NÃO:
// - consulta API;
// - altera uma execução;
// - possui regras de polling;
// - gerencia filtros;
// - controla estado da página.
//
// Ele é intencionalmente visual e reutilizável.
// ============================================================

import {
    AlertCircle,
    CheckCircle2,
    CircleStop,
    Clock3,
    Loader2,
    XCircle,
} from "lucide-react";

import type {
    ReactNode,
} from "react";

import {
    formatarStatus,
} from "../../utils/executionFormatters";


// ============================================================
// PROPS
// ============================================================

interface ExecutionStatusBadgeProps {

    // Status técnico retornado pelo Control Room.
    status: string;
}


// ============================================================
// CONFIGURAÇÃO VISUAL
// ============================================================

interface StatusConfiguration {

    // Texto apresentado ao usuário.
    label: string;

    // Classe CSS já utilizada pela tela atual.
    className: string;

    // Ícone correspondente ao status.
    icon: ReactNode;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionStatusBadge({
    status,
}: ExecutionStatusBadgeProps) {

    const configuracoes: Record<
        string,
        StatusConfiguration
    > = {

        success: {
            label: "Sucesso",
            className:
                "execution-status success",
            icon: (
                <CheckCircle2 size={14} />
            ),
        },


        error: {
            label: "Erro",
            className:
                "execution-status error",
            icon: (
                <XCircle size={14} />
            ),
        },


        stopped: {
            label: "Parado",
            className:
                "execution-status stopped",
            icon: (
                <CircleStop size={14} />
            ),
        },


        running: {
            label: "Executando",
            className:
                "execution-status running",
            icon: (
                <Loader2 size={14} />
            ),
        },


        queued: {
            label: "Na fila",
            className:
                "execution-status queued",
            icon: (
                <Clock3 size={14} />
            ),
        },


        cancelled: {
            label: "Cancelado",
            className:
                "execution-status cancelled",
            icon: (
                <XCircle size={14} />
            ),
        },
    };


    // Status ainda desconhecidos pelo frontend continuam
    // aparecendo com o mesmo fallback utilizado anteriormente.
    const config =
        configuracoes[status] ?? {
            label:
                formatarStatus(status),

            className:
                "execution-status",

            icon: (
                <AlertCircle size={14} />
            ),
        };


    return (
        <span
            className={
                config.className
            }
        >
            {config.icon}

            {config.label}
        </span>
    );
}


export default ExecutionStatusBadge;