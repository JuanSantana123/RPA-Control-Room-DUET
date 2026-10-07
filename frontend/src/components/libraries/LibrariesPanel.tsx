import {
    useEffect,
    useState,
} from "react";

// Componentes visuais do módulo.
import LibraryFolderPicker from "./LibraryFolderPicker";
import ImportLibraryModal from "./ImportLibraryModal";
import LibraryCatalogHeader from "./catalog/LibraryCatalogHeader";
import LibraryCatalogExplorer from "./catalog/LibraryCatalogExplorer";
import LibraryDetailsPanel from "./details/LibraryDetailsPanel";
import LibraryFolderEditorModal from "./modals/LibraryFolderEditorModal";
import LibraryEditorModal from "./modals/LibraryEditorModal";
import LibraryConfirmationModal from "./modals/LibraryConfirmationModal";

// Hooks separados por responsabilidade.
import useLibrariesCatalog from "./hooks/useLibrariesCatalog";
import useLibraryFolderEditor from "./hooks/useLibraryFolderEditor";
import useLibraryEditor from "./hooks/useLibraryEditor";
import useLibraryImport from "./hooks/useLibraryImport";
import useLibraryFolderPicker from "./hooks/useLibraryFolderPicker";
import useLibraryDestructiveActions from "./hooks/useLibraryDestructiveActions";
import useLibraryReactivate from "./hooks/useLibraryReactivate";

import type {
    LibraryCatalogItem,
    LibraryFolderTreeNode,
} from "./types/libraries";

import "./LibrariesPanel.css";


// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

function LibrariesPanel() {
    // ========================================================
    // CATÁLOGO
    // ========================================================

    const {
        libraryTree,
        catalogView,
        libraryFolderCount,
        libraryCount,
        loadingLibraries,
        libraryError,
        librarySuccess,
        librarySearch,
        expandedFolders,
        selectedFolder,
        selectedLibrary,
        versions,
        loadingVersions,
        folderOptions,
        visibleTree,
        selectedFolderPath,
        selectedLibraryPath,

        setLibraryError,
        setLibrarySuccess,
        setLibrarySearch,
        setExpandedFolders,
        setSelectedFolder,
        setSelectedLibrary,
        setVersions,

        carregarBibliotecas,
        carregarVersoes,
        alterarCatalogView,
        selecionarPasta:
            selecionarPastaCatalogo,

        selecionarLibrary:
            selecionarLibraryCatalogo,

        alternarPasta,
        obterPastasBloqueadas,
    } = useLibrariesCatalog();


    // ========================================================
    // MENUS CONTEXTUAIS
    // ========================================================

    const [
        openFolderMenu,
        setOpenFolderMenu,
    ] = useState<
        number | null
    >(null);

    const [
        openLibraryMenu,
        setOpenLibraryMenu,
    ] = useState<
        number | null
    >(null);


    const closeFolderMenu = () => {
        setOpenFolderMenu(null);
    };


    const closeLibraryMenu = () => {
        setOpenLibraryMenu(null);
    };


    // ========================================================
    // EDITOR DE PASTA
    // ========================================================

    const folderEditor =
        useLibraryFolderEditor({
            libraryTree,
            setLibraryError,
            setLibrarySuccess,
            setExpandedFolders,
            carregarBibliotecas,
            closeFolderMenu,
        });


    // ========================================================
    // EDITOR DE LIBRARY
    // ========================================================

    const libraryEditor =
        useLibraryEditor({
            libraryTree,
            setLibraryError,
            setLibrarySuccess,
            setExpandedFolders,
            setSelectedFolder,
            setSelectedLibrary,
            carregarBibliotecas,
            closeFolderMenu,
            closeLibraryMenu,
        });


    // ========================================================
    // IMPORTAÇÃO STANDALONE
    // ========================================================

    const libraryImport =
        useLibraryImport({
            setLibraryError,
            setLibrarySuccess,
            setExpandedFolders,
            setSelectedFolder,
            setSelectedLibrary,
            carregarBibliotecas,
            carregarVersoes,
            closeFolderMenu,
            closeLibraryMenu,
        });


    // ========================================================
    // SELETOR / MOVIMENTAÇÃO
    // ========================================================

    const folderPicker =
        useLibraryFolderPicker({
            folderDestinationId:
                folderEditor.destinationId,

            setFolderDestinationId:
                folderEditor.setDestinationId,

            libraryDestinationId:
                libraryEditor.destinationId,

            setLibraryDestinationId:
                libraryEditor.setDestinationId,

            setLibraryError,
            setLibrarySuccess,
            setExpandedFolders,
            carregarBibliotecas,
            obterPastasBloqueadas,
            closeFolderMenu,
            closeLibraryMenu,
        });


    // ========================================================
    // AÇÕES DESTRUTIVAS
    // ========================================================

    const destructiveActions =
        useLibraryDestructiveActions({
            selectedFolder,
            selectedLibrary,
            setSelectedFolder,
            setSelectedLibrary,
            setVersions,
            setLibraryError,
            setLibrarySuccess,
            carregarBibliotecas,
            closeFolderMenu,
            closeLibraryMenu,
        });
    
    

    // ========================================================
    // REATIVAÇÃO DE LIBRARY
    // ========================================================

    const libraryReactivate =
        useLibraryReactivate({
            setSelectedFolder,
            setSelectedLibrary,
            setLibraryError,
            setLibrarySuccess,
            carregarBibliotecas,
            carregarVersoes,
            closeLibraryMenu,
        });

    // ========================================================
    // PRIMEIRO CARREGAMENTO
    // ========================================================

    useEffect(() => {
        void carregarBibliotecas();
    }, [
        carregarBibliotecas,
    ]);


    // ========================================================
    // SELEÇÃO
    // ========================================================

    const selecionarPasta = (
        folder:
            LibraryFolderTreeNode
    ) => {
        selecionarPastaCatalogo(
            folder
        );

        closeFolderMenu();
        closeLibraryMenu();
    };


    const selecionarLibrary =
        async (
            library:
                LibraryCatalogItem
        ) => {
            closeFolderMenu();
            closeLibraryMenu();

            await selecionarLibraryCatalogo(
                library
            );
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div
            className="libraries-module"
            onClick={() => {
                closeFolderMenu();
                closeLibraryMenu();
            }}
        >
            <section className="content-panel libraries-catalog-panel">
                <LibraryCatalogHeader
                    loading={
                        loadingLibraries
                    }
                    error={
                        libraryError
                    }
                    success={
                        librarySuccess
                    }

                    catalogView={
                        catalogView
                    }

                    onCatalogViewChange={
                        alterarCatalogView
                    }
                    onRefresh={
                        carregarBibliotecas
                    }
                    onCreateFolder={() =>
                        folderEditor.openCreate(
                            null
                        )
                    }
                    onImportLibrary={() =>
                        libraryImport.openImport(
                            null
                        )
                    }
                    onCreateLibrary={() =>
                        libraryEditor.openCreate(
                            null
                        )
                    }
                    onClearError={() =>
                        setLibraryError("")
                    }
                    onClearSuccess={() =>
                        setLibrarySuccess("")
                    }
                />

                <div className="libraries-workspace">
                    <LibraryCatalogExplorer
                        searchValue={
                            librarySearch
                        }
                        folderCount={
                            libraryFolderCount
                        }
                        libraryCount={
                            libraryCount
                        }
                        loading={
                            loadingLibraries
                        }
                        nodes={
                            visibleTree
                        }
                        expandedFolders={
                            expandedFolders
                        }
                        selectedFolderId={
                            selectedFolder?.id ??
                            null
                        }
                        selectedLibraryId={
                            selectedLibrary?.id ??
                            null
                        }
                        openFolderMenu={
                            openFolderMenu
                        }
                        openLibraryMenu={
                            openLibraryMenu
                        }
                        onSearchChange={
                            setLibrarySearch
                        }
                        onToggleFolder={
                            alternarPasta
                        }
                        onSelectFolder={
                            selecionarPasta
                        }
                        onSelectLibrary={
                            selecionarLibrary
                        }
                        onOpenFolderMenu={
                            setOpenFolderMenu
                        }
                        onOpenLibraryMenu={
                            setOpenLibraryMenu
                        }
                        onCreateFolder={
                            folderEditor.openCreate
                        }
                        onCreateLibrary={
                            libraryEditor.openCreate
                        }
                        onRenameFolder={
                            folderEditor.openRename
                        }
                        onMoveFolder={
                            folderPicker.openFolderMove
                        }
                        onEditLibrary={
                            libraryEditor.openEdit
                        }
                        onMoveLibrary={
                            folderPicker.openLibraryMove
                        }
                        onDeleteFolder={
                            destructiveActions.requestDeleteFolder
                        }
                        onDeactivateLibrary={
                            destructiveActions.requestDeactivateLibrary
                        }

                        onReactivateLibrary={
                            libraryReactivate.reactivate
                        }
                    />

                    <LibraryDetailsPanel
                        selectedLibrary={
                            selectedLibrary
                        }
                        selectedFolder={
                            selectedFolder
                        }
                        selectedLibraryPath={
                            selectedLibraryPath
                        }
                        selectedFolderPath={
                            selectedFolderPath
                        }
                        versions={
                            versions
                        }
                        loadingVersions={
                            loadingVersions
                        }
                        onMoveLibrary={
                            folderPicker.openLibraryMove
                        }
                        onEditLibrary={
                            libraryEditor.openEdit
                        }
                        onCreateFolder={
                            folderEditor.openCreate
                        }
                        onImportLibrary={
                            libraryImport.openImport
                        }
                        onCreateLibrary={
                            libraryEditor.openCreate
                        }
                    />
                </div>
            </section>


            <LibraryFolderEditorModal
                mode={
                    folderEditor.mode
                }
                name={
                    folderEditor.name
                }
                destinationLabel={
                    folderEditor.destinationLabel
                }
                busy={
                    folderEditor.saving
                }
                onNameChange={
                    folderEditor.setName
                }
                onChangeLocation={
                    folderPicker.openFolderCreateLocation
                }
                onCancel={
                    folderEditor.close
                }
                onSave={
                    folderEditor.save
                }
            />


            <LibraryEditorModal
                mode={
                    libraryEditor.mode
                }
                name={
                    libraryEditor.name
                }
                importName={
                    libraryEditor.importName
                }
                description={
                    libraryEditor.description
                }
                destinationLabel={
                    libraryEditor.destinationLabel
                }
                busy={
                    libraryEditor.saving
                }
                onNameChange={
                    libraryEditor.setName
                }
                onImportNameChange={
                    libraryEditor.setImportName
                }
                onDescriptionChange={
                    libraryEditor.setDescription
                }
                onChangeLocation={
                    folderPicker.openLibraryCreateLocation
                }
                onCancel={
                    libraryEditor.close
                }
                onSave={
                    libraryEditor.save
                }
            />


            <ImportLibraryModal
                open={
                    libraryImport.open
                }
                folders={
                    folderOptions
                }
                initialFolderId={
                    libraryImport.destinationId
                }
                busy={
                    libraryImport.importing
                }
                error={
                    libraryImport.open
                        ? libraryError
                        : ""
                }
                onCancel={
                    libraryImport.closeImport
                }
                onImport={
                    libraryImport.importLibrary
                }
            />


            <LibraryFolderPicker
                open={
                    folderPicker.mode !==
                    null
                }
                title={
                    folderPicker.title
                }
                description={
                    folderPicker.description
                }
                folders={
                    folderOptions
                }
                selectedFolderId={
                    folderPicker.selectedFolderId
                }
                disabledFolderIds={
                    folderPicker.blockedFolderIds
                }
                busy={
                    folderPicker.saving
                }
                confirmLabel={
                    folderPicker.confirmLabel
                }
                onChange={
                    folderPicker.setSelectedFolderId
                }
                onCancel={
                    folderPicker.close
                }
                onConfirm={() =>
                    void folderPicker.confirm()
                }
            />


            <LibraryConfirmationModal
                confirmation={
                    destructiveActions.confirmation
                }
                busy={
                    destructiveActions.confirming
                }
                onCancel={
                    destructiveActions.cancel
                }
                onConfirm={
                    destructiveActions.confirm
                }
            />
        </div>
    );
}


export default LibrariesPanel;
