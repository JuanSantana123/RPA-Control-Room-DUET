import type {
    LibraryCatalogItem,
    LibraryTreeNode,
    LibraryFolderTreeNode,
} from "../types/libraries";

import type {
    LibraryCatalogView,
} from "../types/libraries";


/**
 * Filtra a árvore do catálogo conforme a visão selecionada.
 *
 * active:
 *     exibe somente Libraries ativas.
 *
 * archived:
 *     exibe somente Libraries arquivadas.
 *
 * Pastas são preservadas apenas quando possuem algum conteúdo
 * compatível com a visão atual.
 */
export function filtrarArvorePorVisao(
    nodes: LibraryTreeNode[],
    view: LibraryCatalogView
): LibraryTreeNode[] {
    const resultado: LibraryTreeNode[] = [];

    for (const node of nodes) {
        if (node.type === "library") {
            const library =
                node as LibraryCatalogItem;

            const deveExibir =
                view === "active"
                    ? library.is_active
                    : !library.is_active;

            if (deveExibir) {
                resultado.push(
                    library
                );
            }

            continue;
        }

        const folder =
            node as LibraryFolderTreeNode;

        const children =
            filtrarArvorePorVisao(
                folder.children,
                view
            );

        /*
         * Na visão Ativas, a pasta continua visível mesmo vazia.
         *
         * Isso é importante porque LibraryFolder é uma estrutura
         * organizacional independente e também pode ser utilizada
         * como destino para mover/criar Libraries.
         *
         * Na visão Arquivadas, mostramos somente os caminhos que
         * efetivamente possuem alguma Library arquivada.
         */
        if (
            view === "archived" &&
            children.length === 0
        ) {
            continue;
        }

        resultado.push({
            ...folder,
            children,
        });
    }
        

    return resultado;
}


/**
 * Conta folders e Libraries existentes na árvore já filtrada.
 */
export function contarItensArvore(
    nodes: LibraryTreeNode[]
): {
    folders: number;
    libraries: number;
} {
    let folders = 0;
    let libraries = 0;

    const visitar = (
        items: LibraryTreeNode[]
    ) => {
        for (const item of items) {
            if (item.type === "library") {
                libraries += 1;
                continue;
            }

            folders += 1;

            visitar(
                item.children
            );
        }
    };

    visitar(nodes);

    return {
        folders,
        libraries,
    };
}