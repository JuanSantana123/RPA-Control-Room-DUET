// ============================================================
// UTILITÁRIOS - DATA E HORA
// ============================================================
//
// Responsabilidade:
//     Centraliza regras de interpretação e formatação de datas
//     utilizadas pelo frontend do DUET CORE.
//
// Principais cuidados:
//     - alguns DateTime do backend representam UTC, mas chegam
//       atualmente sem "Z" ou offset explícito;
//     - datas de planejamento no formato YYYY-MM-DD NÃO devem
//       sofrer conversão de timezone.
//
// Este arquivo não depende de React.
//
// Não deve:
//     - realizar chamadas HTTP;
//     - possuir estado;
//     - conhecer componentes visuais;
//     - implementar regras de negócio do Workflow.
// ============================================================


// ============================================================
// INTERPRETAR DATETIME DA API
// ============================================================
//
// Exemplo recebido atualmente:
//
//     2026-09-16T16:55:00.000000
//
// Como não possui timezone explícito, tratamos como UTC.
// ============================================================

export const parseApiDateTime = (
    value: string | null
): Date | null => {

    if (!value) {
        return null;
    }


    // Detecta timezone já fornecido pela API:
    //
    // Z
    // +00:00
    // -03:00
    const hasTimezone =
        /(?:Z|[+-]\d{2}:\d{2})$/i.test(
            value
        );


    // Se o backend não informar timezone,
    // o timestamp atual é considerado UTC.
    const normalizedValue =
        hasTimezone
            ? value
            : `${value}Z`;


    const date =
        new Date(
            normalizedValue
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return null;
    }


    return date;
};


// ============================================================
// FORMATAR DATA PURA DO CARD
// ============================================================
//
// O backend envia:
//
//     YYYY-MM-DD
//
// Não usamos new Date() para evitar que timezone provoque
// alteração involuntária do dia.
// ============================================================

export const formatCardDate = (
    value: string | null
): string => {

    if (!value) {
        return "—";
    }


    const parts =
        value.split("-");


    if (parts.length !== 3) {
        return value;
    }


    const [
        year,
        month,
        day,
    ] = parts;


    if (
        !year ||
        !month ||
        !day
    ) {
        return value;
    }


    return `${day}/${month}`;
};


// ============================================================
// FORMATAR DATETIME DA LIXEIRA
// ============================================================

export const formatDeletedAt = (
    value: string | null
): string => {

    if (!value) {
        return "Data não registrada";
    }


    const date =
        parseApiDateTime(
            value
        );


    if (!date) {
        return "Data não registrada";
    }


    return date.toLocaleString(
        "pt-BR"
    );
};