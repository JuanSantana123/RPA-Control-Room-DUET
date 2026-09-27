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
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    ChevronRight,
    Folder,
    Package,
    Plus,
    MousePointer2,
} from "lucide-react";

import RobotsHeader from "../components/robots/RobotsHeader";
import RobotFolderTree from "../components/robots/RobotFolderTree";
import CreateRobotFolderForm from "../components/robots/CreateRobotFolderForm";
import RobotExecutionAgent from "../components/robots/RobotExecutionAgent";
import RobotsGrid from "../components/robots/RobotsGrid";
import RobotsOverview from "../components/robots/RobotsOverview";
import RobotsToolbar, { type RobotSort, type RobotView } from "../components/robots/RobotsToolbar";
import RobotVersionsDialog from "../components/robots/RobotVersionsDialog";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import { Button } from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import AccessModeBadge from "../components/ui/AccessModeBadge";
import PanelHeader from "../components/ui/PanelHeader";
import { useAuth } from "../context/useAuth";

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
import { useRobotVersions } from "../hooks/robots/useRobotVersions";
import { getRobotFolderPath } from "../utils/robotFolders";

// ============================================================

// ============================================================
// PÁGINA DE ROBÔS
// ============================================================

interface RobotsProps {
    embedded?: boolean;
}

function Robots({ embedded = false }: RobotsProps) {

    const { can } = useAuth();
    const canCreateRobots = can("Robots:create");
    const canDeleteRobots = can("Robots:delete");
    const canExecuteRobots = can("Executions:execute");
    const canCreateDevelopmentProject = can("Development:create");

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
        setNewFolderParentId,
        creatingFolder,

        showFolderForm,

        openFolderMenu,
        setOpenFolderMenu,

        alternarPasta,
        expandirTodasPastas,
        recolherTodasPastas,
        revelarPasta,

        abrirCriacaoPastaRaiz,
        abrirCriacaoSubpasta,
        fecharCriacaoPasta,

        criarPasta,
        excluirPasta,
    } = useRobotFolders({
        setError,
        setSuccess,
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

    const robotVersions = useRobotVersions();

    useEffect(() => {
        if (!rootSelected && selectedFolder === null) {
            void carregarRobosRaiz();
        }
    }, [carregarRobosRaiz, rootSelected, selectedFolder]);

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

    const selectedFolderPath = useMemo(
        () => selectedFolder ? getRobotFolderPath(folders, selectedFolder.id) : [],
        [folders, selectedFolder],
    );
    const selectedLocation = rootSelected
        ? "Raiz de Robôs"
        : selectedFolderPath.length > 0
            ? ["Raiz de Robôs", ...selectedFolderPath.map((folder) => folder.name)].join(" / ")
            : "Nenhuma pasta selecionada";
    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className={embedded ? "automation-center__view robots-page" : "page-container robots-page"}>
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
            {!embedded && <RobotsHeader />}

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
            {canCreateRobots && showFolderForm && (
                <CreateRobotFolderForm
                    folders={folders}
                    newFolderName={newFolderName}
                    newFolderParentId={newFolderParentId}
                    creatingFolder={creatingFolder}
                    onFolderNameChange={setNewFolderName}
                    onParentChange={setNewFolderParentId}
                    onCreateFolder={criarPasta}
                    onCancel={fecharCriacaoPasta}
                />
            )}

            <div className="robots-workspace-grid">
            {/* Lista de pastas */}
            <section className="content-panel robots-folders-panel">
                <PanelHeader
                    className="robots-folder-panel-header"
                    icon={<Folder />}
                    title="Pastas de robôs"
                    description="Selecione uma pasta para visualizar seus robôs."
                    actions={(
                        <div className="robots-folder-header-actions">
                            {!canCreateRobots && !canDeleteRobots && <AccessModeBadge />}
                            <span className="panel-count-group" aria-label={`${folders.length} pastas cadastradas`}>
                                <span className="panel-count">{folders.length}</span>
                                <span className="panel-count-label">pastas</span>
                            </span>
                            {canCreateRobots && (
                                <Button size="sm" variant="secondary" onClick={abrirCriacaoPastaRaiz}>
                                    <Plus size={15} strokeWidth={1.9} />
                                    Nova pasta
                                </Button>
                            )}
                        </div>
                    )}
                />

                <RobotFolderTree
                    canCreate={canCreateRobots}
                    canDelete={canDeleteRobots}
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
                        (folder) => {
                            revelarPasta(folder.id);
                            void carregarRobos(folder);
                        }
                    }

                    onToggleFolder={
                        alternarPasta
                    }

                    onExpandAll={expandirTodasPastas}

                    onCollapseAll={recolherTodasPastas}

                    onSetOpenFolderMenu={
                        setOpenFolderMenu
                    }

                    onCreateRootFolder={abrirCriacaoPastaRaiz}

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
                    <PanelHeader
                        icon={<Package />}
                        title={rootSelected ? "Raiz de Robôs" : selectedFolder?.name}
                        description={rootSelected ? "Robôs publicados diretamente na raiz." : "Robôs disponíveis nesta pasta."}
                        actions={(
                            <div className="panel-header-meta">
                                <span className="panel-count">{robots.length}</span>
                                <span className="panel-count-label">robôs</span>
                            </div>
                        )}
                    />

                    <nav className="robot-location-path" aria-label="Caminho da pasta atual">
                        <button
                            type="button"
                            aria-current={rootSelected ? "location" : undefined}
                            onClick={() => void carregarRobosRaiz()}
                        >
                            <Folder size={14} aria-hidden="true" />
                            <span>Raiz de Robôs</span>
                        </button>
                        {selectedFolderPath.map((folder, index) => {
                            const current = index === selectedFolderPath.length - 1;
                            return (
                                <span className="robot-location-path__segment" key={folder.id}>
                                    <ChevronRight size={14} aria-hidden="true" />
                                    <button
                                        type="button"
                                        aria-current={current ? "location" : undefined}
                                        onClick={() => {
                                            revelarPasta(folder.id);
                                            void carregarRobos(folder);
                                        }}
                                    >
                                        {folder.name}
                                    </button>
                                </span>
                            );
                        })}
                    </nav>

                    <RobotsToolbar
                        query={robotQuery}
                        sort={robotSort}
                        view={robotView}
                        visibleCount={visibleRobots.length}
                        totalCount={robots.length}
                        canUpload={canCreateRobots}
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
                        {canExecuteRobots && <RobotExecutionAgent
                            executionAgents={
                                executionAgents
                            }
                            selectedExecutionAgent={
                                selectedExecutionAgent
                            }
                            onSelectedExecutionAgentChange={
                                setSelectedExecutionAgent
                            }
                        />}


                        {/* ========================================================
                            ROBOTS DA LOCALIZAÇÃO SELECIONADA
                        ======================================================== */}
                        <RobotsGrid
                            canCreate={canCreateRobots}
                            canDelete={canDeleteRobots}
                            canCreateProject={canCreateDevelopmentProject}
                            canExecute={canExecuteRobots}
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
                            onOpenVersions={robotVersions.open}

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

            {robotVersions.selectedRobot && (
                <RobotVersionsDialog
                    robot={robotVersions.selectedRobot}
                    versions={robotVersions.versions}
                    loading={robotVersions.loading}
                    error={robotVersions.error}
                    downloadingVersion={robotVersions.downloadingVersion}
                    expandedVersion={robotVersions.expandedVersion}
                    loadingLibraries={robotVersions.loadingLibraries}
                    librariesByVersion={robotVersions.librariesByVersion}
                    onClose={robotVersions.close}
                    onRetry={robotVersions.retry}
                    onDownload={robotVersions.downloadVersion}
                    onToggleLibraries={robotVersions.toggleLibraries}
                />
            )}
        </div>
);
}

export default Robots;
