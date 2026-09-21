// ============================================================
// DUET CORE - DASHBOARD - FORMATTERS
// ============================================================
//
// Funções puras de formatação utilizadas pelo Dashboard.
//
// Responsabilidade:
// - converter datas retornadas pela API para a apresentação
//   utilizada atualmente pelo Control Room.
//
// Este módulo NÃO:
// - acessa API;
// - mantém estado;
// - conhece componentes React.
// ============================================================


// ============================================================
// FORMATAR DATA
// ============================================================
//
// Mantém exatamente o comportamento do Dashboard original:
//
// - null/ausente -> "-"
// - data inválida -> "-"
// - data válida -> toLocaleString("pt-BR")
// ============================================================

export function formatarData(
    data: string | null
): string {

    if (!data) {
        return "-";
    }


    const dataObj =
        new Date(data);


    if (
        Number.isNaN(
            dataObj.getTime()
        )
    ) {
        return "-";
    }


    return dataObj.toLocaleString(
        "pt-BR"
    );
}