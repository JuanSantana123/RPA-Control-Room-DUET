/**
 * HOOK - REATIVAÇÃO DE LIBRARY
 * ============================
 *
 * Responsável exclusivamente por reativar uma Library
 * anteriormente arquivada.
 *
 * Este hook:
 *
 * - chama a API de reativação;
 * - limpa mensagens anteriores;
 * - atualiza o catálogo;
 * - mantém a Library reativada selecionada;
 * - atualiza suas versões;
 * - informa sucesso ou erro para a interface.
 */

import {
    useState,
} from "react";

import {
    reactivateLibrary,
} from "../services/librariesApi";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    LibraryCatalogItem,
    LibraryFolderTreeNode,
} from "../types/libraries";


interface UseLibraryReactivateOptions {
    setSelectedFolder:
        React.Dispatch<
            React.SetStateAction<
                LibraryFolderTreeNode | null
            >
        >;

    setSelectedLibrary:
        React.Dispatch<
            React.SetStateAction<
                LibraryCatalogItem | null
            >
        >;

    setLibraryError:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    setLibrarySuccess:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    carregarBibliotecas:
        () => Promise<void>;

    carregarVersoes:
        (
            library:
                LibraryCatalogItem
        ) => Promise<void>;

    closeLibraryMenu:
        () => void;
}


export function useLibraryReactivate({
    setSelectedFolder,
    setSelectedLibrary,
    setLibraryError,
    setLibrarySuccess,
    carregarBibliotecas,
    carregarVersoes,
    closeLibraryMenu,
}: UseLibraryReactivateOptions) {
    const [
        reactivating,
        setReactivating,
    ] = useState(false);


    const reactivate = async (
        library:
            LibraryCatalogItem
    ) => {
        /*
         * Proteção visual adicional.
         *
         * Uma Library já ativa não precisa passar novamente
         * pelo fluxo de reativação.
         */
        if (library.is_active) {
            return;
        }

        try {
            setReactivating(true);

            setLibraryError("");
            setLibrarySuccess("");

            closeLibraryMenu();

            const response =
                await reactivateLibrary(
                    library.id
                );

            /*
             * O contrato genérico LibraryResponse permite que
             * "library" seja opcional.
             *
             * A reativação precisa obrigatoriamente devolver a
             * Library atualizada. Validamos isso antes de montar
             * o item utilizado pelo catálogo.
             */
            if (!response.library) {
                throw new Error(
                    "A API não retornou a biblioteca reativada."
                );
            }

            const reactivatedLibrary:
                LibraryCatalogItem = {
                    ...response.library,
                    type: "library",
                };
            /*
             * Atualiza primeiro a árvore.
             *
             * Como estamos na visão "Arquivadas", a Library
             * deixará de aparecer nessa lista assim que se
             * tornar ativa.
             */
            await carregarBibliotecas();

            /*
             * Mantemos a identidade reativada disponível na
             * seleção para o restante do fluxo da aplicação.
             */
            setSelectedFolder(
                null
            );

            setSelectedLibrary(
                reactivatedLibrary
            );

            await carregarVersoes(
                reactivatedLibrary
            );

            setLibrarySuccess(
                "Biblioteca reativada com sucesso."
            );

        } catch (error) {
            console.error(
                "Erro ao reativar biblioteca:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível reativar a biblioteca."
                )
            );

        } finally {
            setReactivating(false);
        }
    };


    return {
        reactivating,
        reactivate,
    };
}


export default useLibraryReactivate;