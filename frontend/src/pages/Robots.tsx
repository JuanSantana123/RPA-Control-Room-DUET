// ============================================================
// DUET CORE - ROBOTS
// ============================================================
//
// Página responsável pela composição da área de Robots.
//
// A lógica especializada está sendo distribuída entre:
// - hooks de domínio;
// - componentes visuais;
// - tipos compartilhados;
// - utilitários.
//
// Robots.tsx permanece como camada de orquestração da tela.
// ============================================================

import {
    useState,
} from "react";

import {
    Folder,
    Package,
    Plus,
} from "lucide-react";

import LibrariesPanel from "../components/libraries/LibrariesPanel";

import RobotsHeader from "../components/robots/RobotsHeader";
import RobotFolderTree from "../components/robots/RobotFolderTree";
import CreateRobotFolderForm from "../components/robots/CreateRobotFolderForm";
import RobotExecutionAgent from "../components/robots/RobotExecutionAgent";
import RobotsGrid from "../components/robots/RobotsGrid";

import {
    useRobotFolders,
} from "../hooks/robots/useRobotFolders";

import {
    useRobotsData,
} from "../hooks/robots/useRobotsData";

import {
    useRobotExecution,
} from "../hooks/robots/useRobotExecution";

import {
    useRobotLibraries,
} from "../hooks/robots/useRobotLibraries";

// ============================================================

// ============================================================
// PÁGINA DE ROBÔS
// ============================================================

function Robots() {

    // ========================================================
    // MENSAGENS DA PÁGINA
    // ========================================================
    //
    // Error e success continuam pertencendo à página porque
    // diferentes domínios precisam apresentar mensagens no
    // mesmo espaço visual.
    // ========================================================

    const [
        error,
        setError,
    ] = useState<string>("");


    const [
        success,
        setSuccess,
    ] = useState<string>("");


    // ========================================================
    // PASTAS
    // ========================================================

    const {
        folders,

        selectedFolder,
        setSelectedFolder,

        rootSelected,
        setRootSelected,

        expandedFolders,
        loadingFolders,

        newFolderName,
        setNewFolderName,

        newFolderParentId,
        creatingFolder,

        showFolderForm,

        openFolderMenu,
        setOpenFolderMenu,

        alternarPasta,

        abrirCriacaoPastaRaiz,
        abrirCriacaoSubpasta,

        criarPasta,
        excluirPasta,
    } = useRobotFolders({
        setError,
    });


    // ========================================================
    // ROBOTS
    // ========================================================

    const {
        robots,
        loadingRobots,

        openRobotMenu,
        setOpenRobotMenu,

        uploadTargetFolderId,
        setUploadTargetFolderId,

        uploadInputRef,

        carregarRobosRaiz,
        carregarRobos,

        abrirUploadParaPasta,
        enviarRobo,

        excluirRobo,
        baixarRobo,

        criarProjetoDeAlteracao,
    } = useRobotsData({
        folders,

        selectedFolder,
        rootSelected,

        setSelectedFolder,
        setRootSelected,

        setError,
        setSuccess,
    });


    // ========================================================
    // EXECUÇÃO
    // ========================================================

    const {
        executionAgents,

        selectedExecutionAgent,
        setSelectedExecutionAgent,

        executingRobotId,

        executarRobo,
    } = useRobotExecution();


    // ========================================================
    // LIBRARIES DO RELEASE
    // ========================================================

    const {
        robotLibraries,
        loadedRobotLibraries,

        expandedRobotLibraries,
        loadingRobotLibraries,

        alternarBibliotecasDoRobo,
    } = useRobotLibraries({
        setError,
    });
    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container robots-page">
            {/* ========================================================
                INPUT OCULTO - UPLOAD DE ROBOT

                O menu contextual de uma pasta define o folder_id e abre
                este input. O arquivo escolhido é enviado para a pasta
                selecionada.
            ======================================================== */}
            <input
                ref={uploadInputRef}
                type="file"
                accept=".zip"
                style={{
                    display: "none",
                }}
                onChange={async (event) => {

                    const file =
                        event.target.files?.[0];


                    if (
                        !file ||
                        uploadTargetFolderId === null
                    ) {
                        return;
                    }


                    await enviarRobo(
                        file,
                        uploadTargetFolderId
                    );


                    // Permite selecionar novamente o mesmo ZIP.
                    event.target.value = "";

                    setUploadTargetFolderId(null);
                }}
            />



            {/* Cabeçalho principal da página. */}
            <RobotsHeader />
            

            {/* ============================================================
                MENSAGEM DE ERRO
                ============================================================

                Exibe o motivo real retornado pelo backend.
            ============================================================ */}

            {error && (
                <div className="alert alert-error">
                    {error}
                </div>
            )}


            {/* ============================================================
                MENSAGEM DE SUCESSO
                ============================================================

                Só aparece depois que o backend confirmou a operação.
            ============================================================ */}

            {success && (
                <div className="alert alert-success">
                    {success}
                </div>
            )}

            {/* Área superior: criação de pasta e upload */}
            {/* ========================================================
                CRIAÇÃO DE PASTAS
            ======================================================== */}
            <div className="robots-management-grid">

                {showFolderForm && (
                    <CreateRobotFolderForm
                        folders={folders}
                        newFolderName={newFolderName}
                        newFolderParentId={newFolderParentId}
                        creatingFolder={creatingFolder}
                        onFolderNameChange={
                            setNewFolderName
                        }
                        onCreateFolder={
                            criarPasta
                        }
                    />
                )}

            </div>

            {/* Lista de pastas */}
            <section className="content-panel robots-folders-panel">
                <div className="content-panel-header">
                    <div className="section-heading-group">
                        <div className="section-icon">
                            <Folder size={18} strokeWidth={1.8} />
                        </div>

                        <div>
                            <h2>Pastas de robôs</h2>
                            <p>
                                Selecione uma pasta para visualizar seus robôs.
                            </p>
                        </div>
                    </div>


                    <div className="panel-header-meta">
                        <button
                            type="button"
                            className="secondary-button"
                            onClick={
                                    abrirCriacaoPastaRaiz
                                }
                        >
                            <Plus size={15} strokeWidth={1.9} />
                            Nova pasta
                        </button>

                        <span className="panel-count">
                            {folders.length}
                        </span>

                        <span className="panel-count-label">
                            pastas
                        </span>
                    </div>
                    
                </div>

                <RobotFolderTree
                    folders={folders}
                    loadingFolders={loadingFolders}
                    rootSelected={rootSelected}
                    selectedFolder={selectedFolder}
                    expandedFolders={expandedFolders}
                    openFolderMenu={openFolderMenu}

                    onSelectRoot={
                        carregarRobosRaiz
                    }

                    onSelectFolder={
                        carregarRobos
                    }

                    onToggleFolder={
                        alternarPasta
                    }

                    onSetOpenFolderMenu={
                        setOpenFolderMenu
                    }

                    onUploadRobot={(
                        folderId
                    ) => {

                        // Preserva o comportamento existente:
                        // o menu é fechado antes de abrir o seletor.
                        setOpenFolderMenu(null);

                        abrirUploadParaPasta(
                            folderId
                        );
                    }}

                    onCreateSubfolder={
                        abrirCriacaoSubpasta
                    }

                    onDeleteFolder={
                        excluirPasta
                    }
                />
            </section>

            {/* Robôs da pasta selecionada */}
            {(rootSelected || selectedFolder) && (
                <section className="content-panel selected-robots-panel">
                    <div className="content-panel-header">
                        <div className="section-heading-group">
                            <div className="section-icon">
                                <Package size={18} strokeWidth={1.8} />
                            </div>

                            <div>
                                <h2>
                                    {rootSelected
                                        ? "Raiz de Robôs"
                                        : selectedFolder?.name}
                                </h2>
                                <p>
                                    {rootSelected
                                        ? "Robôs publicados diretamente na raiz."
                                        : "Robôs disponíveis nesta pasta."}
                                </p>
                            </div>
                        </div>

                        <div className="panel-header-meta">
                            <span className="panel-count">
                                {robots.length}
                            </span>

                            <span className="panel-count-label">
                                robôs
                            </span>
                        </div>
                    </div>

                    {/* Agent de execução */}
                    {/* ========================================================
                            AGENT DE EXECUÇÃO
                        ======================================================== */}
                        <RobotExecutionAgent
                            executionAgents={
                                executionAgents
                            }
                            selectedExecutionAgent={
                                selectedExecutionAgent
                            }
                            onSelectedExecutionAgentChange={
                                setSelectedExecutionAgent
                            }
                        />


                        {/* ========================================================
                            ROBOTS DA LOCALIZAÇÃO SELECIONADA
                        ======================================================== */}
                        <RobotsGrid
                            robots={robots}
                            loadingRobots={loadingRobots}

                            openRobotMenu={
                                openRobotMenu
                            }

                            expandedRobotLibraries={
                                expandedRobotLibraries
                            }

                            loadingRobotLibraries={
                                loadingRobotLibraries
                            }

                            robotLibraries={
                                robotLibraries
                            }

                            loadedRobotLibraries={
                                loadedRobotLibraries
                            }

                            selectedExecutionAgent={
                                selectedExecutionAgent
                            }

                            executingRobotId={
                                executingRobotId
                            }

                            onSetOpenRobotMenu={
                                setOpenRobotMenu
                            }

                            onDownloadRobot={
                                baixarRobo
                            }

                            onDeleteRobot={
                                excluirRobo
                            }

                            onToggleLibraries={
                                alternarBibliotecasDoRobo
                            }

                            onCreateNewVersion={
                                criarProjetoDeAlteracao
                            }

                            onExecuteRobot={
                                executarRobo
                            }
                        />
                </section>
            )}

            {/* Catálogo global de Bibliotecas.
                A lógica fica isolada em components/libraries. */}
            <LibrariesPanel />
        </div>
);
}

export default Robots;