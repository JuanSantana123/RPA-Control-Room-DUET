// ============================================================
// DUET CORE - HISTORY - FORMATTERS
// ============================================================
//
// Funções puras utilizadas para apresentação do histórico.
//
// Responsabilidade:
// - formatar datas;
// - calcular duração;
// - converter status interno para texto apresentado.
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - possui estado React;
// - modifica execuções;
// - renderiza componentes.
//
// A lógica foi extraída diretamente de History.tsx.
// ============================================================


// ============================================================
// FORMATAR DATA
// ============================================================

export function formatHistoryDate(
    data: string | null
): string {

    // Quando não existe data, mantém o comportamento atual.
    if (!data) {
        return "-";
    }


    // Converte para a representação local brasileira.
    return new Date(
        data
    ).toLocaleString(
        "pt-BR"
    );
}


// ============================================================
// CALCULAR DURAÇÃO
// ============================================================

export function calculateHistoryDuration(
    inicio: string | null,
    fim: string | null
): string {

    // Sem as duas datas não existe duração calculável.
    if (!inicio || !fim) {
        return "-";
    }


    const dataInicio =
        new Date(inicio);

    const dataFim =
        new Date(fim);


    // Calcula a diferença total em segundos.
    const segundos =
        Math.floor(
            (
                dataFim.getTime() -
                dataInicio.getTime()
            ) / 1000
        );


    // Mantém a proteção atual contra duração negativa.
    if (segundos < 0) {
        return "-";
    }


    // Menos de um minuto.
    if (segundos < 60) {
        return `${segundos}s`;
    }


    // Um minuto ou mais.
    const minutos =
        Math.floor(
            segundos / 60
        );

    const resto =
        segundos % 60;


    return `${minutos}m ${resto}s`;
}


// ============================================================
// FORMATAR STATUS
// ============================================================

export function formatHistoryStatus(
    status: string
): string {

    if (status === "success") {
        return "Sucesso";
    }


    if (status === "error") {
        return "Erro";
    }


    if (status === "stopped") {
        return "Parado";
    }


    // Qualquer status não conhecido permanece inalterado.
    return status;
}