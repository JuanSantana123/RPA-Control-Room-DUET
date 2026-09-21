// ============================================================
// UTILITÁRIOS - ERROS DA API
// ============================================================
//
// Responsabilidade:
//     Normaliza respostas de erro recebidas pelo frontend.
//
// O FastAPI do DUET CORE pode devolver mensagens em formatos
// diferentes, por exemplo:
//
//     detail: "Mensagem"
//
// ou:
//
//     detail: {
//         message: "Mensagem"
//     }
//
// Esta função centraliza essa interpretação para impedir que
// cada página implemente sua própria regra.
//
// Este arquivo não depende de React e não realiza chamadas HTTP.
// ============================================================


// ============================================================
// OBTER MENSAGEM AMIGÁVEL DA API
// ============================================================

export const getApiErrorMessage = (
    err: any,
    fallback: string
): string => {

    const detail =
        err?.response?.data?.detail;


    // FastAPI retornando:
    //
    // detail: "Mensagem"
    if (
        typeof detail ===
        "string"
    ) {
        return detail;
    }


    // Algumas regras protegidas do DUET retornam:
    //
    // detail: {
    //     message: "Mensagem"
    // }
    if (
        detail &&
        typeof detail === "object" &&
        typeof detail.message === "string"
    ) {
        return detail.message;
    }


    const message =
        err?.response?.data?.message;


    if (
        typeof message ===
        "string"
    ) {
        return message;
    }


    // Erros lançados localmente pelo próprio frontend.
    if (
        typeof err?.message === "string" &&
        err.message.trim()
    ) {
        return err.message;
    }


    return fallback;
};