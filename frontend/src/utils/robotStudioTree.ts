// ============================================================
// DUET CORE - ROBOT STUDIO - HELPERS DA ÁRVORE
// ============================================================
//
// Responsabilidade:
// - concentrar as operações puras utilizadas para consultar
//   e transformar a árvore do workspace do Robot Studio;
// - manipular StudioNode sem acessar React, API ou estado
//   externo;
// - preservar exatamente o comportamento atualmente existente
//   em RobotStudio.tsx.
//
// IMPORTANTE:
// Este arquivo faz parte de uma refatoração estrutural.
// As funções abaixo foram separadas por responsabilidade,
// sem alteração intencional de lógica ou comportamento.
//
// Este módulo NÃO deve:
// - executar chamadas HTTP;
// - possuir estado React;
// - acessar Checkout;
// - controlar Monaco;
// - implementar operações de Library;
// - renderizar componentes.
//
// Dependência:
// - StudioNode, definido em types/robotStudio.ts.
// ============================================================

import type {
    StudioNode,
} from "../types/robotStudio";


// ============================================================
// LOCALIZAR NÓ
// ============================================================

export const findNodeById = (
    nodes: StudioNode[],
    nodeId: string
): StudioNode | null => {
    for (const node of nodes) {
        if (node.id === nodeId) {
            return node;
        }

        if (node.type === "folder" && node.children) {
            const found = findNodeById(
                node.children,
                nodeId
            );

            if (found) {
                return found;
            }
        }
    }

    return null;
};


// ============================================================
// ATUALIZAR CONTEÚDO DE ARQUIVO
// ============================================================

export const updateFileContent = (
    nodes: StudioNode[],
    nodeId: string,
    content: string
): StudioNode[] => {
    return nodes.map((node) => {
        if (
            node.id === nodeId &&
            node.type === "file"
        ) {
            return {
                ...node,
                content,
            };
        }

        if (
            node.type === "folder" &&
            node.children
        ) {
            return {
                ...node,
                children: updateFileContent(
                    node.children,
                    nodeId,
                    content
                ),
            };
        }

        return node;
    });
};


// ============================================================
// ADICIONAR NÓ EM UMA PASTA
// ============================================================

export const addNodeToFolder = (
    nodes: StudioNode[],
    parentId: string | null,
    newNode: StudioNode
): StudioNode[] => {
    if (parentId === null) {
        return [
            ...nodes,
            newNode,
        ];
    }

    return nodes.map((node) => {
        if (
            node.id === parentId &&
            node.type === "folder"
        ) {
            return {
                ...node,
                children: [
                    ...(node.children || []),
                    newNode,
                ],
            };
        }

        if (
            node.type === "folder" &&
            node.children
        ) {
            return {
                ...node,
                children: addNodeToFolder(
                    node.children,
                    parentId,
                    newNode
                ),
            };
        }

        return node;
    });
};


// ============================================================
// PRESERVAR CONTEÚDOS JÁ CARREGADOS
// ============================================================

export const preserveLoadedFileContents = (
    currentWorkspace: StudioNode[],
    newWorkspace: StudioNode[]
): StudioNode[] => {
    /**
     * A árvore retornada pelo backend contém somente metadados.
     *
     * Portanto, depois de adicionar Bibliotecas e recarregar
     * o Explorer, preservamos o conteúdo dos arquivos que já
     * estavam carregados no Monaco.
     *
     * O backend continua sendo a fonte oficial dos arquivos.
     */

    return newWorkspace.map((node) => {

        const currentNode =
            findNodeById(
                currentWorkspace,
                node.id
            );

        if (
            node.type === "file" &&
            currentNode?.type === "file" &&
            currentNode.content !== undefined
        ) {
            return {
                ...node,
                content: currentNode.content,
            };
        }

        if (
            node.type === "folder" &&
            node.children
        ) {
            return {
                ...node,
                children:
                    preserveLoadedFileContents(
                        currentWorkspace,
                        node.children
                    ),
            };
        }

        return node;
    });
};


// ============================================================
// HELPERS - RENOMEAR / EXCLUIR ITENS DO WORKSPACE
// ============================================================

export const remapWorkspacePath = (
    path: string,
    oldPath: string,
    newPath: string
): string => {
    /**
     * Atualiza um caminho quando um arquivo ou pasta é
     * renomeado.
     *
     * Exemplo:
     *
     * oldPath:
     *     src
     *
     * newPath:
     *     services
     *
     * path:
     *     src/sap/processar.py
     *
     * retorno:
     *     services/sap/processar.py
     *
     * Isso é necessário porque ao renomear uma pasta,
     * todos os IDs dos arquivos abaixo dela também mudam.
     */

    if (path === oldPath) {
        return newPath;
    }

    if (
        path.startsWith(
            `${oldPath}/`
        )
    ) {
        return (
            newPath +
            path.slice(
                oldPath.length
            )
        );
    }

    return path;
};


export const renameNodePath = (
    nodes: StudioNode[],
    oldPath: string,
    newPath: string,
    newName: string
): StudioNode[] => {
    /**
     * Atualiza a árvore visual depois que o backend confirma
     * o rename.
     *
     * Também atualiza os caminhos de todos os filhos caso
     * o item renomeado seja uma pasta.
     */

    return nodes.map((node) => {

        const nextId =
            remapWorkspacePath(
                node.id,
                oldPath,
                newPath
            );

        return {
            ...node,

            id: nextId,

            name:
                node.id === oldPath
                    ? newName
                    : node.name,

            children:
                node.children
                    ? renameNodePath(
                        node.children,
                        oldPath,
                        newPath,
                        newName
                    )
                    : node.children,
        };
    });
};


export const removeNodeById = (
    nodes: StudioNode[],
    nodeId: string
): StudioNode[] => {
    /**
     * Remove um arquivo ou uma pasta da árvore do Explorer.
     *
     * Se for pasta, todos os filhos desaparecem junto porque
     * pertencem ao mesmo nó removido.
     */

    return nodes
        .filter(
            (node) =>
                node.id !== nodeId
        )
        .map((node) => {

            if (
                node.type === "folder" &&
                node.children
            ) {
                return {
                    ...node,
                    children:
                        removeNodeById(
                            node.children,
                            nodeId
                        ),
                };
            }

            return node;
        });
};


export const pathBelongsToNode = (
    path: string,
    nodePath: string
): boolean => {
    /**
     * Retorna true quando:
     *
     * - path é exatamente o item;
     * - ou está dentro da pasta informada.
     *
     * Exemplos:
     *
     * utils                  -> utils
     * utils/teste.py         -> utils
     * utils/sub/teste.py     -> utils
     */

    return (
        path === nodePath ||
        path.startsWith(
            `${nodePath}/`
        )
    );
};