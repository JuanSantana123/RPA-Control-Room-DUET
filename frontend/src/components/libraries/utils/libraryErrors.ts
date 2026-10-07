/**
 * TRATAMENTO DE ERROS DO MÓDULO DE BIBLIOTECAS
 * =============================================
 *
 * Mantém a interpretação das respostas HTTP fora dos componentes React.
 */


/**
 * Extrai uma mensagem amigável de respostas do FastAPI/Axios.
 *
 * Não assume que response.data.detail será sempre uma string.
 */
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

    if (typeof detail === "string") {
        return detail;
    }

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

    const message =
        candidate.response?.data?.message;

    if (typeof message === "string") {
        return message;
    }

    return fallback;
}
