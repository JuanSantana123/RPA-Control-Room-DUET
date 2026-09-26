type UnknownRecord = Record<string, unknown>;

export interface ApiErrorDetails {
    message: string;
    status?: number;
    requestId?: string;
    retryable: boolean;
}

function asRecord(value: unknown): UnknownRecord | undefined {
    return typeof value === "object" && value !== null
        ? value as UnknownRecord
        : undefined;
}

function readApiResponse(error: unknown) {
    const errorRecord = asRecord(error);
    const response = asRecord(errorRecord?.response);
    const data = asRecord(response?.data);

    const headers = asRecord(response?.headers);
    const requestId = [
        headers?.["x-request-id"],
        headers?.["x-correlation-id"],
        data?.request_id,
    ].find((value): value is string => typeof value === "string" && Boolean(value.trim()));

    return {
        data,
        errorRecord,
        requestId,
        status: typeof response?.status === "number"
            ? response.status
            : undefined,
    };
}

function formatValidationDetail(detail: unknown): string | undefined {
    if (!Array.isArray(detail)) {
        return undefined;
    }

    const messages = detail
        .map((item) => {
            const itemRecord = asRecord(item);
            const location = itemRecord?.loc;
            const field = Array.isArray(location)
                ? location
                    .filter((part): part is string | number => (
                        (typeof part === "string" || typeof part === "number") &&
                        part !== "body"
                    ))
                    .join(".")
                : "";
            const message = typeof itemRecord?.msg === "string"
                ? itemRecord.msg
                : "Valor inválido";

            return field ? `${field}: ${message}` : message;
        })
        .filter(Boolean);

    return messages.length > 0
        ? `Revise os dados informados: ${messages.join("; ")}.`
        : undefined;
}

export const getApiErrorStatus = (error: unknown): number | undefined => (
    readApiResponse(error).status
);

export const getApiErrorMessage = (
    error: unknown,
    fallback: string
): string => {
    const { data, errorRecord, status } = readApiResponse(error);
    const detail = data?.detail;
    const validationMessage = formatValidationDetail(detail);

    if (validationMessage) {
        return validationMessage;
    }

    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    const detailRecord = asRecord(detail);
    if (typeof detailRecord?.message === "string") {
        return detailRecord.message;
    }

    if (typeof data?.message === "string") {
        return data.message;
    }

    if (status === 401) {
        return "Sua sessão expirou. Entre novamente para continuar.";
    }
    if (status === 403) {
        return "Seu perfil não possui permissão para realizar esta operação.";
    }
    if (status === 404) {
        return "O recurso solicitado não foi encontrado ou deixou de existir.";
    }
    if (status === 409) {
        return "A operação entra em conflito com um registro existente.";
    }
    if (status === 408) {
        return "A operação excedeu o tempo disponível. Confirme o estado atual antes de tentar novamente.";
    }
    if (status === 413) {
        return "O arquivo enviado excede o tamanho permitido pelo servidor.";
    }
    if (status === 429) {
        return "Há muitas solicitações em andamento. Aguarde alguns instantes e tente novamente.";
    }
    if (status === 422) {
        return "Os dados enviados não foram aceitos. Revise os campos e tente novamente.";
    }
    if (status === 502 || status === 503 || status === 504) {
        return "O serviço está temporariamente indisponível. Aguarde alguns instantes e tente novamente.";
    }
    if (typeof status === "number" && status >= 500) {
        return "O servidor encontrou uma falha interna. Tente novamente e consulte os logs se o problema persistir.";
    }

    if (errorRecord?.code === "ECONNABORTED" || errorRecord?.code === "ETIMEDOUT") {
        return "O Control Room demorou mais do que o esperado para responder. Confirme o estado da operação antes de tentar novamente.";
    }

    if (errorRecord?.code === "ERR_CANCELED") {
        return "A operação foi cancelada antes de ser concluída.";
    }

    if (typeof errorRecord?.message === "string" && errorRecord.message.trim()) {
        return status === undefined
            ? "O Control Room não respondeu. Verifique a conexão e tente novamente."
            : errorRecord.message;
    }

    return fallback;
};

export const getApiErrorDetails = (
    error: unknown,
    fallback: string,
): ApiErrorDetails => {
    const { requestId, status } = readApiResponse(error);

    return {
        message: getApiErrorMessage(error, fallback),
        status,
        requestId,
        retryable:
            status === undefined ||
            status === 408 ||
            status === 429 ||
            (status >= 500 && status <= 599),
    };
};
