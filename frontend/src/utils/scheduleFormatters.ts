// ============================================================
// DUET CORE - SCHEDULES - FORMATTERS
// ============================================================
//
// Funções puras de apresentação utilizadas pela área
// de Agendamentos.
//
// Responsabilidade:
// - converter o tipo técnico do Schedule para o texto da UI;
// - formatar datas retornadas pela API.
//
// Este módulo NÃO:
// - altera um Schedule;
// - executa chamadas HTTP;
// - possui estado;
// - calcula a próxima execução;
// - interfere na lógica do Scheduler.
//
// O comportamento foi extraído de pages/Schedules.tsx
// sem alteração das regras existentes.
// ============================================================


// ============================================================
// FORMATAR TIPO
// ============================================================

export function formatarTipo(
    tipoAgendamento: string
) {

    const tipos: Record<string, string> = {
        once: "Uma vez",
        daily: "Diário",
        weekly: "Semanal",
        monthly: "Mensal",
    };


    return (
        tipos[tipoAgendamento] ||
        tipoAgendamento
    );
}


// ============================================================
// FORMATAR DATA
// ============================================================

export function formatarData(
    data: string | null
) {

    if (!data) {
        return "-";
    }


    return new Date(
        data
    ).toLocaleString(
        "pt-BR"
    );
}