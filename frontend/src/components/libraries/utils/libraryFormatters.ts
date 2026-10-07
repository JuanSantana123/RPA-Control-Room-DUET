/**
 * FORMATADORES DO MÓDULO DE BIBLIOTECAS
 * ======================================
 *
 * Mantém funções de apresentação simples fora dos componentes.
 */


/**
 * Formata a data ISO retornada pelo backend para leitura humana.
 */
export function formatarData(
    value: string | null
): string {
    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return value;
    }

    return new Intl.DateTimeFormat(
        "pt-BR",
        {
            dateStyle: "short",
            timeStyle: "short",
        }
    ).format(date);
}


/**
 * Formata o tamanho de um arquivo para apresentação compacta.
 */
export function formatarTamanhoArquivo(
    bytes: number
): string {
    if (bytes < 1024) {
        return `${bytes} B`;
    }

    const kb = bytes / 1024;

    if (kb < 1024) {
        return `${kb.toFixed(1)} KB`;
    }

    const mb = kb / 1024;

    return `${mb.toFixed(1)} MB`;
}


/**
 * Gera uma sugestão de import_name a partir do nome do ZIP.
 *
 * Exemplo:
 *
 *     logging_core.zip
 *         -> logging_core
 */
export function normalizarImportName(
    fileName: string
): string {
    let value = fileName
        .replace(/\.zip$/i, "")
        .trim()
        .replace(
            /[^A-Za-z0-9_]/g,
            "_"
        )
        .replace(/_+/g, "_");

    if (/^\d/.test(value)) {
        value = `lib_${value}`;
    }

    return value;
}


/**
 * Gera uma sugestão de nome amigável para o catálogo.
 *
 * Exemplo:
 *
 *     logging_core
 *         -> Logging Core
 */
export function nomeAmigavel(
    importName: string
): string {
    return importName
        .split("_")
        .filter(Boolean)
        .map(
            (part) =>
                part.charAt(0).toUpperCase() +
                part.slice(1)
        )
        .join(" ");
}
