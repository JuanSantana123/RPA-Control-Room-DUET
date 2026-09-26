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
    useMemo,
    useState,
} from "react";

import {
    Folder,
    Blocks,
    Package,
    Plus,
    MousePointer2,
} from "lucide-react";

import LibrariesPanel from "../components/libraries/LibrariesPanel";

import RobotsHeader from "../components/robots/RobotsHeader";
import RobotFolderTree from "../components/robots/RobotFolderTree";
import CreateRobotFolderForm from "../components/robots/CreateRobotFolderForm";
import RobotExecutionAgent from "../components/robots/RobotExecutionAgent";
import RobotsGrid from "../components/robots/RobotsGrid";
import RobotsOverview from "../components/robots/RobotsOverview";
import RobotsToolbar, { type RobotSort, type RobotView } from "../components/robots/RobotsToolbar";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import { Button } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";

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

    const [robotQuery, setRobotQuery] = useState("");
    const [robotSort, setRobotSort] = useState<RobotSort>("name-asc");
    const [robotView, setRobotView] = useState<RobotView>("grid");

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
        fecharCriacaoPasta,

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
    } = useRobotExecution({ setError, setSuccess });


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

    const visibleRobots = useMemo(() => {
        const term = robotQuery.trim().toLocaleLowerCase("pt-BR");
        const filtered = term
            ? robots.filter((robot) => [robot.name, robot.filename, robot.version].some((value) => String(value).toLocaleLowerCase("pt-BR").includes(term)))
            : [...robots];

        return filtered.sort((left, right) => {
            if (robotSort === "name-desc") return right.name.localeCompare(left.name, "pt-BR");
            if (robotSort === "version-desc") return String(right.version).localeCompare(String(left.version), "pt-BR", { numeric: true });
            return left.name.localeCompare(right.name, "pt-BR");
        });
    }, [robotQuery, robotSort, robots]);

    const selectedLocation = rootSelected
        ? "Raiz de Robôs"
        : selectedFolder?.name || "Nenhuma pasta selecionada";
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


                    if (!file || uploadTargetFolderId === null) {
                        return;
                    }


                    await enviarRobo(
                        file,
                        uploadTargetFolderId === "root"
                            ? null
                            : uploadTargetFolderId
                    );


                    // Permite selecionar novamente o mesmo ZIP.
                    event.target.value = "";

                    setUploadTargetFolderId(null);
                }}
            />



            {/* Cabeçalho principal da página. */}
            <RobotsHeader />

            <RobotsOverview
                folderCount={folders.length}
                robotCount={robots.length}
                availableAgentCount={executionAgents.length}
                selectedLocation={selectedLocation}
            />
            

            {/* ============================================================
                MENSAGEM DE ERRO
                ============================================================

                Exibe o motivo real retornado pelo backend.
            ============================================================ */}

            {error && (
                <FeedbackBanner
                    tone="error"
                    title="A operação em Robôs não foi concluída"
                    message={error}
                    hint="Revise a pasta, o pacote e suas permissões. Se persistir, consulte os logs do sistema."
                    onDismiss={() => setError("")}
                />
            )}


            {/* ============================================================
                MENSAGEM DE SUCESSO
                ============================================================

                Só aparece depois que o backend confirmou a operação.
            ============================================================ */}

            {success && (
                <FeedbackBanner
                    tone="success"
                    title="Operação concluída"
                    message={success}
                    onDismiss={() => setSuccess("")}
                />
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
                        onCancel={fecharCriacaoPasta}
                    />
                )}

            </div>

            <div className="robots-workspace-grid">
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


                    <div className="robots-folder-header-actions">
                        <span className="panel-count-group" aria-label={`${folders.length} pastas cadastradas`}>
                            <span className="panel-count">
                                {folders.length}
                            </span>

                            <span className="panel-count-label">
                                pastas
                            </span>
                        </span>

                        <Button
                            size="sm"
                            variant="secondary"
                            onClick={
                                    abrirCriacaoPastaRaiz
                                }
                        >
                            <Plus size={15} strokeWidth={1.9} />
                            Nova pasta
                        </Button>
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

                    <RobotsToolbar
                        query={robotQuery}
                        sort={robotSort}
                        view={robotView}
                        visibleCount={visibleRobots.length}
                        totalCount={robots.length}
                        canUpload
                        uploadLocation={rootSelected ? "Raiz de Robôs" : selectedFolder?.name || "pasta atual"}
                        onQueryChange={setRobotQuery}
                        onSortChange={setRobotSort}
                        onViewChange={setRobotView}
                        onUpload={() => {
                            abrirUploadParaPasta(selectedFolder?.id ?? null);
                        }}
                    />

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
                            robots={visibleRobots}
                            totalRobotCount={robots.length}
                            viewMode={robotView}
                            hasActiveFilter={Boolean(robotQuery.trim())}
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
                            onClearFilter={() => setRobotQuery("")}
                        />
                </section>
            )}
            {!rootSelected && !selectedFolder && (
                <section className="content-panel robots-selection-state">
                    <EmptyState
                        icon={<MousePointer2 />}
                        title="Selecione uma localização"
                        description="Escolha a raiz ou uma pasta para pesquisar, organizar, baixar e executar suas automações."
                        action={(
                            <Button onClick={carregarRobosRaiz}>
                                <Package size={15} aria-hidden="true" />
                                Abrir Raiz de Robôs
                            </Button>
                        )}
                    />
                </section>
            )}
            </div>

            {/* Catálogo global de Bibliotecas.
                A lógica fica isolada em components/libraries. */}
            <div className="robots-catalog-intro">
                <span className="section-icon"><Blocks size={18} strokeWidth={1.8} aria-hidden="true" /></span>
                <div>
                    <small>Dependências reutilizáveis</small>
                    <h2>Catálogo de bibliotecas</h2>
                    <p>Consulte versões publicadas e os componentes compartilhados pelas automações.</p>
                </div>
            </div>
            <LibrariesPanel />
        </div>
);
}

export default Robots;
