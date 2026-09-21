// ============================================================
// DUET CORE - EXECUTIONS - FORMATTERS
// ============================================================
//
// Funções puras de apresentação utilizadas pelo domínio
// de Execuções.
//
// Responsabilidade:
// - calcular a duração apresentada de uma execução;
// - formatar datas para pt-BR;
// - converter status técnicos para labels da interface.
//
// Este módulo NÃO:
// - acessa API;
// - possui estado React;
// - executa ações;
// - renderiza componentes.
//
// As regras abaixo foram extraídas de Executions.tsx sem
// alteração de comportamento.
// ============================================================


/**
 * Calcula a duração entre o início e o fim de uma execução.
 *
 * Quando a execução ainda não terminou, utiliza o horário
 * atual, preservando o comportamento existente da página.
 *
 * @param inicio Data/hora inicial recebida da API.
 * @param fim Data/hora final ou null para execução em andamento.
 */
export function calcularDuracao(
    inicio: string | null,
    fim: string | null
): string {

    if (!inicio) {
        return "-";
    }


    const dataInicio =
        new Date(inicio);


    const dataFim =
        fim
            ? new Date(fim)
            : new Date();


    const diferenca =
        Math.floor(
            (
                dataFim.getTime() -
                dataInicio.getTime()
            ) / 1000
        );


    if (diferenca < 0) {
        return "-";
    }


    const horas =
        Math.floor(
            diferenca / 3600
        );


    const minutos =
        Math.floor(
            (diferenca % 3600) / 60
        );


    const segundos =
        diferenca % 60;


    if (horas > 0) {

        return (
            `${horas}h ${minutos}m ${segundos}s`
        );
    }


    if (minutos > 0) {

        return (
            `${minutos}m ${segundos}s`
        );
    }


    return `${segundos}s`;
}


/**
 * Formata uma data da API usando o locale pt-BR.
 *
 * @param data Data/hora recebida da API.
 */
export function formatarData(
    data: string | null
): string {

    if (!data) {
        return "-";
    }


    return new Date(
        data
    ).toLocaleString(
        "pt-BR"
    );
}


/**
 * Converte o status técnico da execução para o texto
 * apresentado na interface.
 *
 * Status desconhecidos continuam sendo apresentados
 * literalmente, preservando o fallback atual.
 *
 * @param status Status retornado pelo backend.
 */
export function formatarStatus(
    status: string
): string {

    switch (status) {

        case "success":
            return "Sucesso";


        case "error":
            return "Erro";


        case "stopped":
            return "Parado";


        case "running":
            return "Executando";


        case "queued":
            return "Na fila";


        case "cancelled":
            return "Cancelado";


        default:
            return (
                status ||
                "Desconhecido"
            );
    }
}