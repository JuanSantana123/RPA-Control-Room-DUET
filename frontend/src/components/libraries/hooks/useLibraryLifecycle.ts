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
    LibraryVersionItem,
} from "../types/libraries";


interface UseLibraryLifecycleOptions {
    selectedLibrary:
        LibraryCatalogItem | null;

    setSelectedLibrary:
        React.Dispatch<
            React.SetStateAction<
                LibraryCatalogItem | null
            >
        >;

    setVersions:
        React.Dispatch<
            React.SetStateAction<
                LibraryVersionItem[]
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

    closeLibraryMenu:
        () => void;
}


export function useLibraryLifecycle({
    selectedLibrary,
    setSelectedLibrary,
    setVersions,
    setLibraryError,
    setLibrarySuccess,
    carregarBibliotecas,
    closeLibraryMenu,
}: UseLibraryLifecycleOptions) {
    const [
        reactivating,
        setReactivating,
    ] = useState(false);


    /**
     * Reativa uma Library arquivada preservando sua identidade.
     */
    const reactivate = async (
        library: LibraryCatalogItem
    ) => {
        if (reactivating) {
            return;
        }

        try {
            setReactivating(true);

            setLibraryError("");
            setLibrarySuccess("");

            closeLibraryMenu();

            await reactivateLibrary(
                library.id
            );

            /*
             * Na visão Arquivadas ela deixará de existir após a
             * reativação, portanto limpamos a seleção atual.
             */
            if (
                selectedLibrary?.id ===
                library.id
            ) {
                setSelectedLibrary(
                    null
                );

                setVersions([]);
            }

            await carregarBibliotecas();

            setLibrarySuccess(
                `Biblioteca "${library.name}" reativada com sucesso.`
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


export default useLibraryLifecycle;