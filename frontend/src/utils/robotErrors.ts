// ============================================================
// DUET CORE - ROBOTS - API ERROR UTILITIES
// ============================================================
//
// Responsabilidade:
// - interpretar mensagens de erro retornadas pelos endpoints
//   utilizados pela área de Robots;
// - preservar mensagens específicas enviadas pelo backend.
//
// O FastAPI pode retornar:
//
// detail: "mensagem"
//
// ou:
//
// detail: {
//     code: "...",
//     message: "mensagem"
// }
//
// Algumas APIs também podem retornar:
//
// message: "mensagem"
//
// Este módulo NÃO:
// - altera estado React;
// - exibe alertas;
// - realiza requisições HTTP;
// - decide regras de negócio.
//
// A decisão de onde apresentar a mensagem continua pertencendo
// ao fluxo que realizou a operação.
// ============================================================


// ============================================================
// OBTER MENSAGEM DE ERRO
// ============================================================
//
// Parâmetros:
//
// error:
//     erro recebido pela operação HTTP.
//
// fallback:
//     mensagem utilizada quando a resposta não contém uma
//     mensagem reconhecida.
//
// Retorno:
//     mensagem que deverá ser apresentada ao usuário.
//
// IMPORTANTE:
// A ordem de leitura abaixo preserva exatamente o comportamento
// existente no Robots.tsx antes da modularização.
// ============================================================

export function obterMensagemErro(
    error: unknown,
    fallback: string
): string {

    const candidate = error as {
        response?: {
            data?: {
                detail?: unknown;
                message?: unknown;
            };
        };
    };


    const detail =
        candidate.response?.data?.detail;


    // --------------------------------------------------------
    // FastAPI retornou detail diretamente como string.
    // --------------------------------------------------------

    if (
        typeof detail === "string"
    ) {
        return detail;
    }


    // --------------------------------------------------------
    // FastAPI retornou detail estruturado.
    //
    // Exemplo:
    //
    // {
    //     detail: {
    //         code: "ROBOT_HAS_LIBRARIES",
    //         message: "..."
    //     }
    // }
    // --------------------------------------------------------

    if (
        detail &&
        typeof detail === "object" &&
        "message" in detail
    ) {

        const detailMessage = (
            detail as {
                message?: unknown;
            }
        ).message;


        if (
            typeof detailMessage === "string"
        ) {
            return detailMessage;
        }
    }


    // --------------------------------------------------------
    // Algumas APIs do projeto retornam message diretamente.
    // --------------------------------------------------------

    const message =
        candidate.response?.data?.message;


    if (
        typeof message === "string"
    ) {
        return message;
    }


    // --------------------------------------------------------
    // Nenhuma mensagem conhecida foi encontrada.
    // --------------------------------------------------------

    return fallback;
}