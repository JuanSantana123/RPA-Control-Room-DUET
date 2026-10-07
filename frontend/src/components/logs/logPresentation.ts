// ============================================================
// DUET CORE - LOGS - APRESENTAÇÃO
// ============================================================
//
// Responsabilidade:
// - transformar dados técnicos de um SystemLog em informações
//   mais claras para leitura humana;
// - definir labels contextuais para ator, recurso e status;
// - manter LogsPanel livre de regras específicas de eventos.
//
// Este módulo NÃO:
// - renderiza componentes React;
// - altera o conteúdo original do log;
// - executa chamadas HTTP;
// - conhece estilos visuais.
// ============================================================

import type { SystemLog } from "../../types/logs";

export interface LogPresentation {
    headline: string;
    detail?: string;
    actorLabel: string;
    resourceLabel: string;
    statusLabel?: string;
}


/**
 * Converte os status técnicos do backend para labels legíveis.
 *
 * Valores desconhecidos são preservados para não esconder
 * informações futuras adicionadas pelo backend.
 */
function getStatusLabel(status?: string | null): string | undefined {
    if (!status) {
        return undefined;
    }

    switch (status.toLowerCase()) {
        case "success":
            return "Sucesso";

        case "error":
        case "failed":
        case "failure":
            return "Falha";

        case "warning":
            return "Atenção";

        case "ready":
            return "Pronto";

        default:
            return status;
    }
}


/**
 * Define como o recurso afetado deve ser apresentado.
 *
 * Exemplo:
 *
 * resource_type = "user"
 * resource_name = "vm1"
 *
 * Resultado:
 *
 * "usuário afetado: vm1"
 */
function getResourceLabel(resourceType?: string | null): string {
    switch (resourceType?.toLowerCase()) {
        case "user":
            return "usuário afetado";

        case "agent":
            return "Agent afetado";

        case "robot":
            return "robô afetado";

        case "library":
            return "biblioteca afetada";

        case "project":
        case "automation_project":
            return "projeto afetado";

        case "template":
            return "Template afetado";

        case "role":
            return "Role afetada";

        default:
            return "recurso afetado";
    }
}


/**
 * Extrai somente a transição de Roles da mensagem atualmente
 * emitida pelo backend.
 *
 * Entrada:
 *
 * "Roles do usuário alteradas: Desenvolvedor -> Administrador"
 *
 * Saída:
 *
 * "Desenvolvedor → Administrador"
 */
function extractRolesTransition(message: string): string | undefined {
    const transition = message.replace(
        /^Roles do usuário alteradas:\s*/i,
        "",
    );

    if (transition === message) {
        return undefined;
    }

    return transition.replace(/\s*->\s*/g, " → ");
}


/**
 * Monta a apresentação humana de um registro.
 *
 * Eventos conhecidos podem receber uma descrição contextual.
 * Eventos ainda não conhecidos continuam exibindo a mensagem
 * original do backend sem perda de informação.
 */
export function getLogPresentation(log: SystemLog): LogPresentation {
    const actor = log.actor_username;
    const resource = log.resource_name;

    const basePresentation: LogPresentation = {
        headline: log.message,
        actorLabel: "executado por",
        resourceLabel: getResourceLabel(log.resource_type),
        statusLabel: getStatusLabel(log.status),
    };

    switch (log.event) {
        case "user.roles.changed": {
            if (!actor || !resource) {
                return basePresentation;
            }

            return {
                ...basePresentation,

                headline: `${actor} alterou as Roles de ${resource}`,

                detail: extractRolesTransition(log.message),
            };
        }

        case "user.disabled": {
            if (!actor || !resource) {
                return basePresentation;
            }

            return {
                ...basePresentation,

                headline: `${actor} desativou o usuário ${resource}`,
            };
        }

        case "user.enabled": {
            if (!actor || !resource) {
                return basePresentation;
            }

            return {
                ...basePresentation,

                headline: `${actor} ativou o usuário ${resource}`,
            };
        }

        case "user.password.changed": {
            if (!actor || !resource) {
                return basePresentation;
            }

            return {
                ...basePresentation,

                headline: `${actor} alterou a senha de ${resource}`,
            };
        }

        default:
            return basePresentation;
    }
}