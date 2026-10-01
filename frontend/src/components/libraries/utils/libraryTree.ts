/**
 * UTILITÁRIOS DA ÁRVORE DE BIBLIOTECAS
 * =====================================
 *
 * Funções puras utilizadas para navegar, filtrar e transformar
 * a árvore do catálogo.
 *
 * Este arquivo não conhece React e não realiza chamadas HTTP.
 */

import type {
    LibraryCatalogItem,
    LibraryFolderOption,
    LibraryFolderTreeNode,
    LibraryTreeNode,
} from "../types/libraries";


/**
 * Retorna somente as pastas existentes em determinado nível.
 */
export function obterPastasDoNivel(
    nodes: LibraryTreeNode[]
): LibraryFolderTreeNode[] {
    return nodes.filter(
        (
            node
        ): node is LibraryFolderTreeNode =>
            node.type === "folder"
    );
}

/**
 * Converte a árvore para o formato simplificado utilizado
 * pelos seletores de pasta.
 *
 * Somente pastas ativas podem ser utilizadas como destino
 * para criar ou mover Libraries.
 *
 * Mesmo que uma árvore carregada com include_inactive=true
 * contenha pastas históricas/desativadas, elas nunca serão
 * oferecidas como destino operacional.
 */
export function converterParaFolderOptions(
    nodes: LibraryTreeNode[]
): LibraryFolderOption[] {
    return obterPastasDoNivel(nodes)
        .filter(
            (folder) =>
                folder.is_active
        )
        .map(
            (folder) => ({
                id: folder.id,
                name: folder.name,
                parent_id: folder.parent_id,
                children:
                    converterParaFolderOptions(
                        folder.children
                    ),
            })
        );
}


/**
 * Localiza uma pasta em qualquer profundidade.
 */
export function encontrarPasta(
    nodes: LibraryTreeNode[],
    folderId: number
): LibraryFolderTreeNode | null {
    for (const node of nodes) {
        if (node.type !== "folder") {
            continue;
        }

        if (node.id === folderId) {
            return node;
        }

        const encontrada = encontrarPasta(
            node.children,
            folderId
        );

        if (encontrada) {
            return encontrada;
        }
    }

    return null;
}


/**
 * Localiza uma Library em qualquer profundidade.
 */
export function encontrarLibrary(
    nodes: LibraryTreeNode[],
    libraryId: number
): LibraryCatalogItem | null {
    for (const node of nodes) {
        if (
            node.type === "library" &&
            node.id === libraryId
        ) {
            return node;
        }

        if (node.type === "folder") {
            const encontrada =
                encontrarLibrary(
                    node.children,
                    libraryId
                );

            if (encontrada) {
                return encontrada;
            }
        }
    }

    return null;
}


/**
 * Monta o caminho organizacional de uma pasta.
 *
 * Exemplo:
 *
 *     Corporativo / Financeiro / Cobrança
 */
export function encontrarCaminhoPasta(
    nodes: LibraryTreeNode[],
    folderId: number,
    caminhoAtual: string[] = []
): string[] | null {
    for (const node of nodes) {
        if (node.type !== "folder") {
            continue;
        }

        const caminho = [
            ...caminhoAtual,
            node.name,
        ];

        if (node.id === folderId) {
            return caminho;
        }

        const encontrado =
            encontrarCaminhoPasta(
                node.children,
                folderId,
                caminho
            );

        if (encontrado) {
            return encontrado;
        }
    }

    return null;
}


/**
 * Resolve o caminho usando a estrutura simplificada
 * LibraryFolderOption.
 *
 * É utilizado pelos modais e seletores que não precisam
 * conhecer o restante do catálogo.
 */
export function encontrarCaminhoFolderOption(
    folders: LibraryFolderOption[],
    folderId: number,
    caminhoAtual: string[] = []
): string[] | null {
    for (const folder of folders) {
        const caminho = [
            ...caminhoAtual,
            folder.name,
        ];

        if (folder.id === folderId) {
            return caminho;
        }

        const encontrado =
            encontrarCaminhoFolderOption(
                folder.children,
                folderId,
                caminho
            );

        if (encontrado) {
            return encontrado;
        }
    }

    return null;
}


/**
 * Obtém a própria pasta e todas as descendentes.
 *
 * Esses IDs são utilizados para impedir ciclos ao mover pastas.
 */
export function obterIdsDescendentes(
    folder: LibraryFolderTreeNode | null
): Set<number> {
    const ids = new Set<number>();

    const visitar = (
        atual: LibraryFolderTreeNode
    ) => {
        ids.add(atual.id);

        obterPastasDoNivel(
            atual.children
        ).forEach(visitar);
    };

    if (folder) {
        visitar(folder);
    }

    return ids;
}


/**
 * Filtra a árvore preservando os ancestrais dos resultados.
 */
export function filtrarArvore(
    nodes: LibraryTreeNode[],
    searchValue: string
): LibraryTreeNode[] {
    const termo = searchValue
        .trim()
        .toLocaleLowerCase("pt-BR");

    if (!termo) {
        return nodes;
    }

    const resultado: LibraryTreeNode[] = [];

    for (const node of nodes) {
        if (node.type === "library") {
            const combina =
                node.name
                    .toLocaleLowerCase(
                        "pt-BR"
                    )
                    .includes(termo) ||
                node.import_name
                    .toLocaleLowerCase(
                        "pt-BR"
                    )
                    .includes(termo);

            if (combina) {
                resultado.push(node);
            }

            continue;
        }

        const filhosFiltrados =
            filtrarArvore(
                node.children,
                searchValue
            );

        const pastaCombina = node.name
            .toLocaleLowerCase("pt-BR")
            .includes(termo);

        if (
            pastaCombina ||
            filhosFiltrados.length > 0
        ) {
            resultado.push({
                ...node,
                children: pastaCombina
                    ? node.children
                    : filhosFiltrados,
            });
        }
    }

    return resultado;
}
