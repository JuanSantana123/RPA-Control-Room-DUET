// ============================================================
// DUET CORE - BROWSER DOWNLOAD
// ============================================================
//
// Responsabilidade:
// - iniciar, no navegador, o download de um Blob já recebido;
// - liberar imediatamente a URL temporária criada para o arquivo.
//
// Este utilitário evita repetir a mesma sequência DOM em hooks
// diferentes do frontend.
// ============================================================

export function downloadBlob(
    blob: Blob,
    filename: string,
): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;

    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(url);
}
