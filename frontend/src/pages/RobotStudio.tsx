// ============================================================
// ROBOT STUDIO - TREE UTILITIES
// ============================================================
//
// Utilizado pela composição visual ainda existente nesta página
// para localizar o arquivo correspondente a uma aba aberta.
// ============================================================

import {
    findNodeById,
} from "../utils/robotStudioTree";

import { type CSSProperties, type ReactNode } from "react";

import { useLocation, useNavigate, useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import {
    ArrowLeft,
    ChevronDown,
    ChevronRight,
    FileCode2,
    FileJson,
    FilePlus2,
    Folder,
    FolderOpen,
    FolderPlus,
    Pencil,
    Plus,
    Save,
    Terminal,
    Trash2,
    Unlink,
    X,
} from "lucide-react";

import type {
    StudioLocationState,
    StudioNode,
} from "../types/robotStudio";

import { useRobotStudioData } from "../hooks/robot-studio/useRobotStudioData";
import { useRobotStudioCheckout } from "../hooks/robot-studio/useRobotStudioCheckout";
import { useRobotStudioWorkspace } from "../hooks/robot-studio/useRobotStudioWorkspace";
import { useRobotStudioLibraries } from "../hooks/robot-studio/useRobotStudioLibraries";


// ============================================================
// TERMINAL INTEGRADO
// ============================================================
//
// O componente encapsula xterm + WebSocket.
// RobotStudio apenas decide qual projeto está aberto e se o
// usuário possui Checkout para utilizar o terminal.
// ============================================================

import RobotStudioTerminal from
    "../components/robot-studio/RobotStudioTerminal";
import LibraryActionsModal from "../components/robot-studio/libraries/LibraryActionsModal";
import AddExistingLibrariesModal from "../components/robot-studio/libraries/AddExistingLibrariesModal";
import CreateLibraryModal from "../components/robot-studio/libraries/CreateLibraryModal";
import type { LibraryActionsModalStyles } from "../components/robot-studio/libraries/LibraryActionsModal";
import type { AddExistingLibrariesModalStyles } from "../components/robot-studio/libraries/AddExistingLibrariesModal";
import type { CreateLibraryModalStyles } from "../components/robot-studio/libraries/CreateLibraryModal";
import "./RobotStudio.css";
// ============================================================
// DUET CORE - ROBOT STUDIO
// ============================================================
//
// Página orquestradora do ambiente de desenvolvimento.
//
// As regras de dados, Checkout, Workspace e Libraries ficam
// isoladas nos hooks especializados. Esta página mantém a
// composição visual já existente do Studio e seus estilos.
// ============================================================

const languageFromFilename = (filename: string): string => {
    const lower = filename.toLowerCase();

    if (lower.endsWith(".py")) return "python";
    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return "typescript";
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return "javascript";
    if (lower.endsWith(".md")) return "markdown";
    if (lower.endsWith(".css")) return "css";
    if (lower.endsWith(".html")) return "html";
    if (lower.endsWith(".yaml") || lower.endsWith(".yml")) return "yaml";

    return "plaintext";
};

const fileIcon = (filename: string, size = 15) => {
    if (filename.toLowerCase().endsWith(".json")) {
        return <FileJson size={size} strokeWidth={1.7} />;
    }

    return <FileCode2 size={size} strokeWidth={1.7} />;
};

function RobotStudio() {

    const navigate = useNavigate();
    const location = useLocation();

    const { projectId } =
        useParams<{ projectId: string }>();


    // ========================================================
    // DADOS / RBAC
    // ========================================================

    const {
        project,
        permissionsLoaded,
        canViewDevelopment,
        canEditWorkspace,
        canCheckout,
        canForceCheckoutRelease,
        canViewLibraries,
        canUseLibrary,
        canCreateLibrary,
    } = useRobotStudioData({
        projectId,
    });


    // ========================================================
    // CHECKOUT + OUTPUT
    // ========================================================
    //
    // O bloqueio visual do Checkin por dirtyFiles continua na
    // página logo abaixo. Por isso o hook recebe zero aqui e a
    // validação real usa o Set do Workspace antes da chamada.
    // ========================================================

    const checkout =
        useRobotStudioCheckout({
            projectId,
            permissionsLoaded,
            canViewDevelopment,
            canEditWorkspace,
            canCheckout,
            canForceCheckoutRelease,
            dirtyFilesCount: 0,
        });

    const {
        checkoutState,
        loadingCheckout,
        checkoutActionLoading,
        ownsCheckout,
        canWriteWorkspace,
        workspaceReadOnlyMessage,
        carregarCheckout,
        realizarCheckout,
        realizarForceReleaseCheckout,
        showOutput,
        setShowOutput,
        outputLines,
        setOutputLines,
    } = checkout;


    // ========================================================
    // WORKSPACE
    // ========================================================

    const workspaceController =
        useRobotStudioWorkspace({
            projectId,
            permissionsLoaded,
            canViewDevelopment,
            canWriteWorkspace,
            carregarCheckout,
            setOutputLines,
        });

    const {
        workspace,
        setWorkspace,
        activeFileId,
        setActiveFileId,
        activeFile,
        openTabs,
        setOpenTabs,
        expandedFolders,
        setExpandedFolders,
        selectedFolderId,
        setSelectedFolderId,
        dirtyFiles,
        // Permite ao hook de Libraries sincronizar o estado
        // de arquivos modificados quando a composição mudar.
        setDirtyFiles,
        dirty,
        openFile,
        closeTab,
        handleEditorChange,
        saveWorkspace,
        createFile,
        createFolder,
        createFileInFolder,
        createFolderInFolder,
        renomearItem,
        excluirItem,
        toggleFolder,
    } = workspaceController;


    // ========================================================
    // CHECKIN
    // ========================================================
    //
    // Preserva a regra original: não libera o Checkout quando
    // existe qualquer arquivo ainda não salvo.
    // ========================================================

    const realizarCheckin = async () => {

        if (dirtyFiles.size > 0) {
            setOutputLines((current) => [
                ...current,
                "[DUET] CHECKIN BLOQUEADO: salve as alterações antes de liberar o projeto.",
            ]);

            return;
        }

        await checkout.realizarCheckin();
    };


    // ========================================================
    // LIBRARIES
    // ========================================================

    const {
        showLibraryActions,
        setShowLibraryActions,
        showAddExistingLibraries,
        setShowAddExistingLibraries,
        availableLibraries,
        selectedExistingLibraries,
        selectedExistingVersions,
        loadingAvailableLibraries,
        addingExistingLibraries,
        existingLibraryError,
        showCreateLibrary,
        setShowCreateLibrary,
        libraryName,
        setLibraryName,
        libraryImportName,
        setLibraryImportName,
        libraryImportTouched,
        setLibraryImportTouched,
        libraryDescription,
        setLibraryDescription,
        libraryCreateError,
        setLibraryCreateError,
        creatingLibrary,
        suggestImportName,
        abrirGerenciamentoBibliotecas,
        abrirCriacaoBiblioteca,
        criarBibliotecaProjeto,
        abrirBibliotecasExistentes,
        alternarBibliotecaExistente,
        selecionarVersaoBibliotecaExistente,
        adicionarBibliotecasExistentes,
        removerBibliotecaDoProjeto,
        } = useRobotStudioLibraries({
        projectId,
        canWriteWorkspace,
        canViewLibraries,
        canUseLibrary,
        canCreateLibrary,

        // Estado dos arquivos modificados do Workspace.
        // O hook de Libraries recebe tanto o estado atual quanto
        // o setter para manter a composição do projeto sincronizada.
        dirtyFiles,
        setDirtyFiles,

        setWorkspace,
        setOpenTabs,
        setActiveFileId,
        setSelectedFolderId,
        setExpandedFolders,
        openFile,
        carregarCheckout,
        setOutputLines,
    });


    // ========================================================
    // NOME VISUAL DO PROJETO
    // ========================================================

    const projectName =
        project?.name ||
        (
            location.state as StudioLocationState | null
        )?.projectName ||
        `Projeto ${projectId || ""}`;

    const renderNode = (
        node: StudioNode,
        level = 0
    ): ReactNode => {

        const paddingLeft =
            10 + level * 14;


        // ====================================================
        // PASTA
        // ====================================================

        if (node.type === "folder") {

            const expanded =
                expandedFolders.has(
                    node.id
                );

            const selected =
                selectedFolderId ===
                node.id;

            // O contêiner técnico e o namespace principal possuem
            // responsabilidades diferentes:
            //
            // - _libraries: apenas agrupa Bibliotecas;
            // - _libraries/<namespace>: raiz de uma Biblioteca;
            // - níveis abaixo do namespace: pastas normais editáveis.
            const isLibraryContainer =
                node.id === "_libraries";

            const isLibraryNamespaceRoot =
                /^_libraries\/[^/]+$/.test(node.id);

            const isInsideLibrary =
                node.id.startsWith("_libraries/");

            const displayName =
                node.id === "_libraries"
                    ? "Bibliotecas"
                    : node.name;


            return (
                <div key={node.id}>

                    <div
                        style={{
                            ...styles.treeItemRow,

                            background:
                                selected
                                    ? "var(--studio-surface-raised)"
                                    : "transparent",
                        }}
                    >

                        {/* =====================================
                            ÁREA PRINCIPAL DA PASTA
                        ===================================== */}

                        <button
                            type="button"
                            onClick={() => {

                                setSelectedFolderId(
                                    node.id
                                );

                                toggleFolder(
                                    node.id
                                );
                            }}
                            style={{
                                ...styles.treeRowMain,
                                paddingLeft,
                            }}
                        >

                            <span style={styles.treeChevron}>
                                {expanded ? (
                                    <ChevronDown size={14} />
                                ) : (
                                    <ChevronRight size={14} />
                                )}
                            </span>


                            {expanded ? (
                                <FolderOpen
                                    size={15}
                                    strokeWidth={1.7}
                                />
                            ) : (
                                <Folder
                                    size={15}
                                    strokeWidth={1.7}
                                />
                            )}


                            <span style={styles.treeLabel}>
                                {displayName}
                            </span>

                        </button>


                        {/* =====================================
                            AÇÕES DA PASTA
                        ===================================== */}

                        {!isLibraryContainer && (
                            <div style={styles.treeItemActions}>

                                {/* ---------------------------------
                                    BIBLIOTECAS: NOVO ARQUIVO
                                   ---------------------------------

                                   A raiz do namespace e qualquer
                                   subpasta interna podem receber
                                   novos arquivos.
                                */}
                                {isInsideLibrary && (
                                    <button
                                        type="button"
                                        onClick={() =>
                                            createFileInFolder(
                                                node.id
                                            )
                                        }
                                        disabled={!canWriteWorkspace}
                                        style={{
                                            ...styles.treeActionButton,
                                            opacity:
                                                canWriteWorkspace
                                                    ? 1
                                                    : 0.35,
                                            cursor:
                                                canWriteWorkspace
                                                    ? "pointer"
                                                    : "not-allowed",
                                        }}
                                        title="Novo arquivo nesta pasta"
                                        aria-label={`Novo arquivo em ${node.name}`}
                                    >
                                        <FilePlus2
                                            size={13}
                                            strokeWidth={1.8}
                                        />
                                    </button>
                                )}


                                {/* ---------------------------------
                                    BIBLIOTECAS: NOVA SUBPASTA
                                   ---------------------------------

                                   Funciona tanto na raiz da
                                   Biblioteca quanto em qualquer
                                   subpasta abaixo dela.
                                */}
                                {isInsideLibrary && (
                                    <button
                                        type="button"
                                        onClick={() =>
                                            createFolderInFolder(
                                                node.id
                                            )
                                        }
                                        disabled={!canWriteWorkspace}
                                        style={{
                                            ...styles.treeActionButton,
                                            opacity:
                                                canWriteWorkspace
                                                    ? 1
                                                    : 0.35,
                                            cursor:
                                                canWriteWorkspace
                                                    ? "pointer"
                                                    : "not-allowed",
                                        }}
                                        title="Nova pasta dentro desta pasta"
                                        aria-label={`Nova pasta em ${node.name}`}
                                    >
                                        <FolderPlus
                                            size={13}
                                            strokeWidth={1.8}
                                        />
                                    </button>
                                )}
                                

                                {/* ---------------------------------
                                    REMOVER LIBRARY DO PROJETO
                                   ---------------------------------

                                   Diferente da lixeira comum:

                                   - não apaga uma pasta arbitrária;
                                   - não exclui a Library global;
                                   - remove oficialmente a dependência
                                     deste AutomationProject.
                                */}
                                {isLibraryNamespaceRoot && (
                                    <button
                                        type="button"
                                        onClick={() =>
                                            removerBibliotecaDoProjeto(
                                                node
                                            )
                                        }
                                        disabled={
                                            !canWriteWorkspace ||
                                            !canUseLibrary
                                        }
                                        style={{
                                            ...styles.treeActionButton,

                                            opacity:
                                                canWriteWorkspace &&
                                                canUseLibrary
                                                    ? 1
                                                    : 0.35,

                                            cursor:
                                                canWriteWorkspace &&
                                                canUseLibrary
                                                    ? "pointer"
                                                    : "not-allowed",
                                        }}
                                        title="Remover biblioteca do projeto"
                                        aria-label={`Remover ${node.name} do projeto`}
                                    >
                                        <Unlink
                                            size={13}
                                            strokeWidth={1.8}
                                        />
                                    </button>
                                )}

                                {/* A raiz da Biblioteca não pode ser
                                    renomeada ou excluída diretamente
                                    pelo Explorer. Isso continua sendo
                                    responsabilidade da gestão da Library.

                                    Subpastas internas seguem editáveis. */}
                                {!isLibraryNamespaceRoot && (
                                    <>
                                        <button
                                            type="button"
                                            onClick={() =>
                                                renomearItem(
                                                    node
                                                )
                                            }
                                            disabled={!canWriteWorkspace}
                                            style={{
                                                ...styles.treeActionButton,
                                                opacity:
                                                    canWriteWorkspace
                                                        ? 1
                                                        : 0.35,
                                                cursor:
                                                    canWriteWorkspace
                                                        ? "pointer"
                                                        : "not-allowed",
                                            }}
                                            title="Renomear pasta"
                                            aria-label={`Renomear ${node.name}`}
                                        >
                                            <Pencil
                                                size={13}
                                                strokeWidth={1.8}
                                            />
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                excluirItem(
                                                    node
                                                )
                                            }
                                            disabled={!canWriteWorkspace}
                                            style={{
                                                ...styles.treeActionButton,
                                                opacity:
                                                    canWriteWorkspace
                                                        ? 1
                                                        : 0.35,
                                                cursor:
                                                    canWriteWorkspace
                                                        ? "pointer"
                                                        : "not-allowed",
                                            }}
                                            title="Excluir pasta"
                                            aria-label={`Excluir ${node.name}`}
                                        >
                                            <Trash2
                                                size={13}
                                                strokeWidth={1.8}
                                            />
                                        </button>
                                    </>
                                )}

                            </div>
                        )}

                    </div>


                    {/* =========================================
                        FILHOS
                    ========================================= */}

                    {expanded &&
                        node.children?.map(
                            (child) =>
                                renderNode(
                                    child,
                                    level + 1
                                )
                        )}

                </div>
            );
        }


        // ====================================================
        // ARQUIVO
        // ====================================================

        const active =
            activeFileId ===
            node.id;


        return (

            <div
                key={node.id}
                style={{
                    ...styles.treeItemRow,

                    background:
                        active
                            ? "var(--studio-border)"
                            : "transparent",
                }}
            >

                {/* =============================================
                    ÁREA PRINCIPAL DO ARQUIVO
                ============================================= */}

                <button
                    type="button"
                    onClick={() =>
                        openFile(
                            node
                        )
                    }
                    style={{
                        ...styles.treeRowMain,

                        paddingLeft:
                            paddingLeft + 20,
                    }}
                >

                    <span style={styles.fileIcon}>
                        {fileIcon(
                            node.name
                        )}
                    </span>


                    <span style={styles.treeLabel}>
                        {node.name}
                    </span>

                </button>


                {/* =============================================
                    AÇÕES DO ARQUIVO
                ============================================= */}

                {node.id !== "main.py" && (

                    <div style={styles.treeItemActions}>

                        <button
                            type="button"
                            onClick={() =>
                                renomearItem(
                                    node
                                )
                            }
                            disabled={!canWriteWorkspace}

                            style={{
                                ...styles.treeActionButton,

                                opacity:
                                    canWriteWorkspace
                                        ? 1
                                        : 0.35,

                                cursor:
                                    canWriteWorkspace
                                        ? "pointer"
                                        : "not-allowed",
                            }}
                            title="Renomear arquivo"
                            aria-label={`Renomear ${node.name}`}
                        >
                            <Pencil
                                size={13}
                                strokeWidth={1.8}
                            />
                        </button>


                        <button
                            type="button"
                            onClick={() =>
                                excluirItem(
                                    node
                                )
                            }
                            disabled={!canWriteWorkspace}

                            style={{
                                ...styles.treeActionButton,

                                opacity:
                                    canWriteWorkspace
                                        ? 1
                                        : 0.35,

                                cursor:
                                    canWriteWorkspace
                                        ? "pointer"
                                        : "not-allowed",
                            }}
                            title="Excluir arquivo"
                            aria-label={`Excluir ${node.name}`}
                        >
                            <Trash2
                                size={13}
                                strokeWidth={1.8}
                            />
                        </button>

                    </div>
                )}

            </div>
        );
    };
    // ========================================================
    // INTERFACE
    // ========================================================

    if (!permissionsLoaded) {
        return (
            <div
                className="robot-studio"
                style={{
                    ...styles.page,
                    alignItems: "center",
                    justifyContent: "center",
                }}
            >
                Verificando permissões...
            </div>
        );
    }


    if (!canViewDevelopment) {
        return (
            <div
                className="robot-studio"
                style={{
                    ...styles.page,
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 12,
                }}
            >
                <strong>Acesso não autorizado.</strong>

                <span>
                    Seu usuário não possui Development:view.
                </span>

                <button
                    type="button"
                    onClick={() => navigate("/")}
                    style={styles.secondaryAccessButton}
                >
                    Voltar
                </button>
            </div>
        );
    }


    return (
        <div className="robot-studio route-transition" style={styles.page}>
            {/* =================================================
                TOP BAR
            ================================================= */}
            <header className="robot-studio__topbar" style={styles.topbar}>
                <div className="robot-studio__topbar-left" style={styles.topbarLeft}>
                    <button
                        type="button"
                        onClick={() => navigate("/development")}
                        style={styles.iconButton}
                        title="Voltar para Robôs"
                        aria-label="Voltar para Robôs"
                    >
                        <ArrowLeft size={18} />
                    </button>

                    <div>
                        <div style={styles.eyebrow}>
                            DUET STUDIO
                        </div>

                        <div style={styles.robotTitle}>
                            {projectName}
                        </div>
                    </div>
                </div>

                <div className="robot-studio__topbar-right" style={styles.topbarRight}>

                    {/* Mostra o estado atual do Checkout. */}
                    <span style={styles.checkoutState}>

                        {loadingCheckout
                            ? "Verificando Checkout..."

                            : ownsCheckout
                                ? "Checkout: você"

                                : checkoutState.checked_out
                                    ? `Checkout: ${
                                        checkoutState.checkout?.user_name ||
                                        "outro usuário"
                                    }`

                                    : "Somente leitura"}

                    </span>


                    {/* Se o projeto estiver livre, mostra Checkout. */}
                    {canCheckout &&
                        !loadingCheckout &&
                        !checkoutState.checked_out && (

                        <button
                            type="button"
                            onClick={realizarCheckout}
                            disabled={checkoutActionLoading}
                            style={{
                                ...styles.checkoutButton,
                                opacity:
                                    checkoutActionLoading
                                        ? 0.6
                                        : 1,
                                cursor:
                                    checkoutActionLoading
                                        ? "not-allowed"
                                        : "pointer",
                            }}
                        >
                            {checkoutActionLoading
                                ? "Aguarde..."
                                : "Checkout"}
                        </button>
                    )}


                    {/* Se EU possuir Checkout, mostra Checkin. */}
                    {canCheckout &&
                        !loadingCheckout &&
                        ownsCheckout && (

                        <button
                            type="button"
                            onClick={realizarCheckin}
                            disabled={
                                checkoutActionLoading ||
                                dirty
                            }
                            title={
                                dirty
                                    ? "Salve as alterações antes do Checkin."
                                    : "Liberar Checkout"
                            }
                            style={{
                                ...styles.checkinButton,
                                opacity:
                                    checkoutActionLoading ||
                                    dirty
                                        ? 0.55
                                        : 1,
                                cursor:
                                    checkoutActionLoading ||
                                    dirty
                                        ? "not-allowed"
                                        : "pointer",
                            }}
                        >
                            {checkoutActionLoading
                                ? "Aguarde..."
                                : "Checkin"}
                        </button>
                    )}


                    {/* Force Release aparece somente para usuários autorizados. */}
                    {canForceCheckoutRelease &&
                        !loadingCheckout &&
                        checkoutState.checked_out &&
                        !ownsCheckout && (

                        <button
                            type="button"
                            onClick={realizarForceReleaseCheckout}
                            disabled={checkoutActionLoading}
                            style={{
                                ...styles.forceReleaseButton,
                                opacity:
                                    checkoutActionLoading
                                        ? 0.6
                                        : 1,
                                cursor:
                                    checkoutActionLoading
                                        ? "not-allowed"
                                        : "pointer",
                            }}
                            title="Forçar liberação do Checkout"
                        >
                            {checkoutActionLoading
                                ? "Aguarde..."
                                : "Force Release"}
                        </button>
                    )}


                    {/* Estado dos arquivos. */}
                    <span
                        style={{
                            ...styles.saveState,
                            color:
                                dirty
                                    ? "var(--studio-warning)"
                                    : "var(--studio-text-muted)",
                        }}
                    >
                        {dirty
                            ? "Alterações não salvas"
                            : "Salvo"}
                    </span>


                    {/* Salvar só funciona com Checkout e alteração. */}
                    <button
                        type="button"
                        onClick={saveWorkspace}
                        disabled={
                            !canWriteWorkspace ||
                            !dirty ||
                            !activeFile
                        }
                        style={{
                            ...styles.primaryButton,
                            opacity:
                                !canWriteWorkspace ||
                                !dirty ||
                                !activeFile
                                    ? 0.5
                                    : 1,
                            cursor:
                                !canWriteWorkspace ||
                                !dirty ||
                                !activeFile
                                    ? "not-allowed"
                                    : "pointer",
                        }}
                    >
                        <Save
                            size={15}
                            strokeWidth={1.9}
                        />

                        Salvar
                    </button>

                </div>
            </header>

            {/* =================================================
                WORKSPACE
            ================================================= */}
            <div className="robot-studio__workspace" style={styles.workspace}>
                {/* =============================================
                    EXPLORER
                ============================================= */}
                <aside className="robot-studio__explorer" style={styles.sidebar}>
                    <div style={styles.sidebarHeader}>
                        <span>EXPLORER</span>

                        <div style={styles.sidebarActions}>
                            <button
                                type="button"
                                onClick={abrirGerenciamentoBibliotecas}
                                disabled={
                                    !canWriteWorkspace ||
                                    (
                                        !canCreateLibrary &&
                                        !(
                                            canViewLibraries &&
                                            canUseLibrary
                                        )
                                    )
                                }
                                style={{
                                    ...styles.libraryCreateButton,

                                    opacity:
                                        canWriteWorkspace &&
                                        (
                                            canCreateLibrary ||
                                            (
                                                canViewLibraries &&
                                                canUseLibrary
                                            )
                                        )
                                            ? 1
                                            : 0.4,

                                    cursor:
                                        canWriteWorkspace &&
                                        (
                                            canCreateLibrary ||
                                            (
                                                canViewLibraries &&
                                                canUseLibrary
                                            )
                                        )
                                            ? "pointer"
                                            : "not-allowed",
                                }}
                                title={
                                    canWriteWorkspace
                                        ? "Gerenciar bibliotecas do projeto"
                                        : workspaceReadOnlyMessage
                                }
                                aria-label="Gerenciar bibliotecas"
                            >
                                <Plus size={13} />
                                <span>Lib</span>
                            </button>

                            <button
                                type="button"
                                onClick={createFile}

                                // Sem Checkout, não permite criar.
                                disabled={!canWriteWorkspace}

                                style={{
                                    ...styles.smallIconButton,
                                    opacity:
                                        canWriteWorkspace
                                            ? 1
                                            : 0.4,
                                    cursor:
                                        canWriteWorkspace
                                            ? "pointer"
                                            : "not-allowed",
                                }}

                                title={
                                    canWriteWorkspace
                                        ? "Novo arquivo"
                                        : workspaceReadOnlyMessage
                                }

                                aria-label="Novo arquivo"
                            >
                                <FilePlus2 size={15} />
                            </button>

                            <button
                                type="button"
                                onClick={createFolder}

                                // Sem Checkout, não permite criar.
                                disabled={!canWriteWorkspace}

                                style={{
                                    ...styles.smallIconButton,
                                    opacity:
                                        canWriteWorkspace
                                            ? 1
                                            : 0.4,
                                    cursor:
                                        canWriteWorkspace
                                            ? "pointer"
                                            : "not-allowed",
                                }}

                                title={
                                    canWriteWorkspace
                                        ? "Nova pasta"
                                        : workspaceReadOnlyMessage
                                }

                                aria-label="Nova pasta"
                            >
                                <FolderPlus size={15} />
                            </button>
                        </div>
                    </div>

                    <button
                        type="button"
                        onClick={() => setSelectedFolderId(null)}
                        style={{
                            ...styles.projectRoot,
                            background:
                                selectedFolderId === null
                                    ? "var(--studio-surface-raised)"
                                    : "transparent",
                        }}
                    >
                        <ChevronDown size={14} />
                        <FolderOpen size={16} />
                        <strong>{projectName}</strong>
                    </button>

                    <div style={styles.tree}>
                        {workspace.map((node) =>
                            renderNode(node)
                        )}
                    </div>

                    <div style={styles.sidebarFooter}>
                        <span>Destino de criação:</span>
                        <strong>
                            {selectedFolderId
                                ? findNodeById(
                                    workspace,
                                    selectedFolderId
                                )?.name || "Pasta"
                                : "Raiz"}
                        </strong>
                    </div>
                </aside>

                {/* =============================================
                    ÁREA CENTRAL
                ============================================= */}
                <main className="robot-studio__center" style={styles.center}>
                    {/* =========================================
                        ABAS
                    ========================================= */}
                    <div style={styles.tabs}>
                        {openTabs.map((tab) => {
                            const active = tab.id === activeFileId;

                            return (
                                <div
                                    key={tab.id}
                                    style={{
                                        ...styles.tab,
                                        background: active
                                            ? "var(--studio-surface)"
                                            : "var(--studio-surface-hover)",
                                        borderTop: active
                                            ? "1px solid var(--studio-accent)"
                                            : "1px solid transparent",
                                    }}
                                >
                                    <button
                                        type="button"
                                        onClick={() => setActiveFileId(tab.id)}
                                        style={styles.tabMain}
                                    >
                                        {fileIcon(tab.name, 14)}
                                        <span>{tab.name}</span>

                                        {dirtyFiles.has(tab.id) && (
                                            <span style={styles.dirtyDot}>
                                                ●
                                            </span>
                                        )}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => closeTab(tab.id)}
                                        style={styles.tabClose}
                                        title="Fechar"
                                        aria-label={`Fechar ${tab.name}`}
                                    >
                                        <X size={13} />
                                    </button>
                                </div>
                            );
                        })}
                    </div>

                    {/* =========================================
                        MONACO EDITOR
                    ========================================= */}
                    <div style={styles.editorArea}>
                        {activeFile && activeFile.type === "file" ? (
                            <Editor
                                height="100%"
                                theme="vs-dark"
                                language={languageFromFilename(activeFile.name)}
                                value={activeFile.content || ""}
                                onChange={handleEditorChange}
                                onMount={(editor) => {
                                    editor.getDomNode()
                                        ?.querySelector(".ime-text-area")
                                        ?.setAttribute("aria-hidden", "true");
                                }}
                                options={{
                                    ariaLabel: "Editor de código",
                                    // O código somente pode ser alterado
                                    // com Development:edit + Checkout próprio.
                                    readOnly: !canWriteWorkspace,

                                    readOnlyMessage: {
                                        value: workspaceReadOnlyMessage,
                                    },
                                    fontSize: 14,
                                    fontFamily:
                                        "Consolas, 'Courier New', monospace",
                                    minimap: {
                                        enabled: true,
                                    },
                                    automaticLayout: true,
                                    scrollBeyondLastLine: false,
                                    wordWrap: "off",
                                    tabSize: 4,
                                    insertSpaces: true,
                                    renderWhitespace: "selection",
                                    smoothScrolling: true,
                                    padding: {
                                        top: 12,
                                    },
                                }}
                            />
                        ) : (
                            <div style={styles.editorEmpty}>
                                <FileCode2 size={34} strokeWidth={1.3} />
                                <h3>Nenhum arquivo aberto</h3>
                                <p>
                                    Selecione um arquivo no Explorer para começar a desenvolver.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* =========================================
                        OUTPUT
                    ========================================= */}
                    {showOutput ? (
                        <section style={styles.output}>
                            <div style={styles.outputHeader}>
                                <div style={styles.outputTitle}>
                                    <Terminal size={15} />
                                    OUTPUT
                                </div>

                                <button
                                    type="button"
                                    onClick={() => setShowOutput(false)}
                                    style={styles.smallIconButton}
                                    title="Fechar output"
                                    aria-label="Fechar output"
                                >
                                    <X size={14} />
                                </button>
                            </div>

                            <div style={styles.outputBody}>
                                {outputLines.map((line, index) => (
                                    <div key={`${index}-${line}`}>
                                        {line}
                                    </div>
                                ))}
                            </div>
                        </section>
                    ) : (
                        <button
                            type="button"
                            onClick={() => setShowOutput(true)}
                            style={styles.outputCollapsed}
                        >
                            <Terminal size={14} />
                            OUTPUT
                        </button>
                    )}


                    {/* =========================================
                        TERMINAL
                    =========================================

                        O terminal pertence ao projeto atualmente
                        aberto no Studio.

                        canWriteWorkspace já representa a regra:

                            Development:edit
                                    +
                            Checkout do próprio usuário

                        O backend repete essas validações antes de
                        iniciar o cmd.exe, portanto esta condição
                        frontend é apenas a camada visual.
                    ========================================= */}

                    {projectId && (
                        <RobotStudioTerminal
                            projectId={Number(projectId)}
                            enabled={canWriteWorkspace}
                        />
                    )}

                </main>
            </div>

            <LibraryActionsModal
                open={showLibraryActions}
                canCreateLibrary={canCreateLibrary}
                canViewLibraries={canViewLibraries}
                canUseLibrary={canUseLibrary}
                styles={styles}
                onClose={() => setShowLibraryActions(false)}
                onCreateLibrary={abrirCriacaoBiblioteca}
                onAddExistingLibraries={abrirBibliotecasExistentes}
            />

            <AddExistingLibrariesModal
                open={showAddExistingLibraries}
                availableLibraries={availableLibraries}
                selectedExistingLibraries={selectedExistingLibraries}
                selectedExistingVersions={selectedExistingVersions}
                loadingAvailableLibraries={loadingAvailableLibraries}
                addingExistingLibraries={addingExistingLibraries}
                existingLibraryError={existingLibraryError}
                styles={styles}
                onClose={() => setShowAddExistingLibraries(false)}
                onToggleLibrary={alternarBibliotecaExistente}
                onSelectVersion={selecionarVersaoBibliotecaExistente}
                onAddLibraries={adicionarBibliotecasExistentes}
            />

            <CreateLibraryModal
                open={showCreateLibrary}
                libraryName={libraryName}
                libraryImportName={libraryImportName}
                libraryImportTouched={libraryImportTouched}
                libraryDescription={libraryDescription}
                libraryCreateError={libraryCreateError}
                creatingLibrary={creatingLibrary}
                styles={styles}
                onClose={() => setShowCreateLibrary(false)}
                onLibraryNameChange={setLibraryName}
                onLibraryImportNameChange={setLibraryImportName}
                onLibraryImportTouchedChange={setLibraryImportTouched}
                onLibraryDescriptionChange={setLibraryDescription}
                onClearError={() => setLibraryCreateError("")}
                onSuggestImportName={suggestImportName}
                onCreateLibrary={criarBibliotecaProjeto}
            />
            {/* =================================================
                STATUS BAR
            ================================================= */}
            <footer style={styles.statusBar}>
                <span>DUET CORE</span>
                <span>Project ID: {projectId || "-"}</span>
                <span>
                    {activeFile && activeFile.type === "file"
                        ? languageFromFilename(activeFile.name)
                        : "—"}
                </span>
            </footer>
        </div>
    );
}
// ============================================================
// ESTILOS LOCAIS
// ============================================================
//
// Mantidos no próprio arquivo para que RobotStudio.tsx seja adicionado
// ao projeto sem exigir a criação imediata de outro CSS.
// Depois podemos mover tudo para RobotStudio.css.
// ============================================================

type RobotStudioStyles = Record<string, CSSProperties>
    & LibraryActionsModalStyles
    & AddExistingLibrariesModalStyles
    & CreateLibraryModalStyles;

const styles: RobotStudioStyles = {
    page: {
        width: "100%",
        height: "100vh",
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background: "var(--studio-canvas)",
        color: "var(--studio-text)",
        overflow: "hidden",
        fontFamily:
            "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    },

    topbar: {
        height: 58,
        minHeight: 58,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        background: "var(--studio-surface)",
        borderBottom: "1px solid var(--studio-surface-hover)",
        boxSizing: "border-box",
    },

    topbarLeft: {
        display: "flex",
        alignItems: "center",
        gap: 12,
        minWidth: 0,
    },

    topbarRight: {
        display: "flex",
        alignItems: "center",
        gap: 12,
    },

    eyebrow: {
        fontSize: 10,
        letterSpacing: "0.12em",
        color: "var(--studio-text-muted)",
        fontWeight: 700,
    },

    robotTitle: {
        marginTop: 2,
        fontSize: 15,
        fontWeight: 650,
        color: "var(--studio-text)",
        maxWidth: 500,
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    },

    // Estado atual do Checkout mostrado no topo.
    checkoutState: {
        height: 26,
        padding: "0 9px",
        border: "1px solid var(--studio-border)",
        borderRadius: 5,
        display: "inline-flex",
        alignItems: "center",
        color: "var(--studio-text-secondary)",
        background: "var(--studio-surface-raised)",
        fontSize: 11,
        fontWeight: 600,
        whiteSpace: "nowrap",
    },


    // Botão utilizado para adquirir o Checkout.
    checkoutButton: {
        height: 30,
        padding: "0 11px",
        border: "1px solid var(--studio-accent)",
        borderRadius: 5,
        background: "var(--studio-accent)",
        color: "var(--studio-text-on-accent)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontWeight: 600,
    },


    // Botão utilizado para liberar o Checkout.
    checkinButton: {
        height: 30,
        padding: "0 11px",
        border: "1px solid var(--studio-border-strong)",
        borderRadius: 5,
        background: "var(--studio-surface-hover)",
        color: "var(--studio-text)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontWeight: 600,
    },


    // Ação administrativa separada do Checkin normal.
    forceReleaseButton: {
        height: 30,
        padding: "0 11px",
        border: "1px solid color-mix(in srgb, var(--studio-danger) 45%, var(--studio-border))",
        borderRadius: 5,
        background: "var(--studio-danger-soft)",
        color: "var(--studio-danger)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontWeight: 600,
    },


    secondaryAccessButton: {
        height: 34,
        padding: "0 13px",
        border: "1px solid var(--studio-border-strong)",
        borderRadius: 6,
        background: "var(--studio-surface-hover)",
        color: "var(--studio-text)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 13,
        fontWeight: 600,
        cursor: "pointer",
    },

    iconButton: {
        width: 34,
        height: 34,
        border: "1px solid var(--studio-border)",
        borderRadius: 6,
        background: "var(--studio-surface-raised)",
        color: "var(--studio-text)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    primaryButton: {
        height: 34,
        padding: "0 13px",
        border: "1px solid var(--studio-accent)",
        borderRadius: 6,
        background: "var(--studio-accent)",
        color: "var(--studio-text-on-accent)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 7,
        fontSize: 13,
        fontWeight: 600,
        cursor: "pointer",
    },

    saveState: {
        fontSize: 12,
        whiteSpace: "nowrap",
    },

    workspace: {
        flex: 1,
        minHeight: 0,
        display: "flex",
    },

    sidebar: {
        width: 260,
        minWidth: 220,
        maxWidth: 340,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background: "var(--studio-surface)",
        borderRight: "1px solid var(--studio-surface-hover)",
    },

    sidebarHeader: {
        height: 36,
        minHeight: 36,
        padding: "0 9px 0 13px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        color: "var(--studio-text-secondary)",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.08em",
    },

    sidebarActions: {
        display: "flex",
        alignItems: "center",
        gap: 2,
    },

    smallIconButton: {
        width: 26,
        height: 26,
        padding: 0,
        border: "none",
        borderRadius: 4,
        background: "transparent",
        color: "var(--studio-text-secondary)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    libraryCreateButton: {
        height: 24,
        padding: "0 7px",
        border: "1px solid var(--studio-accent-soft)",
        borderRadius: 5,
        background: "var(--studio-accent-soft)",
        color: "color-mix(in srgb, var(--studio-accent) 28%, var(--studio-text))",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.02em",
    },

    projectRoot: {
        width: "100%",
        height: 30,
        padding: "0 8px",
        border: "none",
        color: "var(--studio-text)",
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontSize: 12,
        cursor: "pointer",
        textAlign: "left",
    },

    tree: {
        flex: 1,
        minHeight: 0,
        overflow: "auto",
        paddingTop: 3,
    },


    treeItemRow: {
        width: "100%",
        height: 28,
        display: "flex",
        alignItems: "center",
        boxSizing: "border-box",
    },


    treeRowMain: {
        flex: 1,
        minWidth: 0,
        height: "100%",
        border: "none",
        background: "transparent",
        color: "var(--studio-text-secondary)",
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontSize: 12.5,
        cursor: "pointer",
        textAlign: "left",
        boxSizing: "border-box",
    },


    treeItemActions: {
        height: "100%",
        display: "flex",
        alignItems: "center",
        gap: 1,
        paddingRight: 4,
        flexShrink: 0,
    },


    treeActionButton: {
        width: 24,
        height: 24,
        padding: 0,
        border: "none",
        borderRadius: 4,
        background: "transparent",
        color: "var(--studio-text-secondary)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    treeChevron: {
        width: 14,
        minWidth: 14,
        height: 14,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
    },

    treeLabel: {
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    },

    fileIcon: {
        width: 15,
        minWidth: 15,
        height: 15,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
    },

    sidebarFooter: {
        minHeight: 42,
        padding: "8px 12px",
        borderTop: "1px solid var(--studio-surface-hover)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 2,
        color: "var(--studio-text-muted)",
        fontSize: 10,
    },

    center: {
        flex: 1,
        minWidth: 0,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
        background: "var(--studio-surface)",
    },

    tabs: {
        minHeight: 35,
        height: 35,
        display: "flex",
        alignItems: "stretch",
        overflowX: "auto",
        overflowY: "hidden",
        background: "var(--studio-surface-raised)",
        borderBottom: "1px solid var(--studio-surface-raised)",
    },

    tab: {
        minWidth: 120,
        maxWidth: 220,
        height: 35,
        display: "flex",
        alignItems: "center",
        borderRight: "1px solid var(--studio-surface)",
        boxSizing: "border-box",
    },

    tabMain: {
        flex: 1,
        minWidth: 0,
        height: "100%",
        padding: "0 7px 0 10px",
        border: "none",
        background: "transparent",
        color: "var(--studio-text-secondary)",
        display: "flex",
        alignItems: "center",
        gap: 7,
        fontSize: 12,
        cursor: "pointer",
    },

    tabClose: {
        width: 26,
        minWidth: 26,
        height: 26,
        border: "none",
        borderRadius: 4,
        background: "transparent",
        color: "var(--studio-text-muted)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        marginRight: 3,
    },

    dirtyDot: {
        marginLeft: "auto",
        fontSize: 8,
        color: "var(--studio-text-secondary)",
    },

    editorArea: {
        flex: 1,
        minHeight: 0,
        position: "relative",
    },

    editorEmpty: {
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--studio-text-muted)",
        textAlign: "center",
        gap: 8,
    },

    output: {
        height: 165,
        minHeight: 110,
        display: "flex",
        flexDirection: "column",
        background: "var(--studio-canvas)",
        borderTop: "1px solid var(--studio-surface-hover)",
    },

    outputHeader: {
        minHeight: 34,
        height: 34,
        padding: "0 8px 0 13px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid var(--studio-surface)",
    },

    outputTitle: {
        display: "flex",
        alignItems: "center",
        gap: 7,
        fontSize: 11,
        fontWeight: 700,
        color: "var(--studio-text-secondary)",
        letterSpacing: "0.05em",
    },

    outputBody: {
        flex: 1,
        minHeight: 0,
        overflow: "auto",
        padding: "8px 12px",
        fontFamily: "Consolas, 'Courier New', monospace",
        fontSize: 12,
        lineHeight: 1.55,
        color: "var(--studio-text-secondary)",
    },

    outputCollapsed: {
        height: 30,
        minHeight: 30,
        border: "none",
        borderTop: "1px solid var(--studio-surface-hover)",
        background: "var(--studio-canvas)",
        color: "var(--studio-text-secondary)",
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "0 12px",
        fontSize: 11,
        fontWeight: 700,
        cursor: "pointer",
    },

    modalBackdrop: {
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "var(--studio-overlay)",
        backdropFilter: "blur(4px)",
    },

    modalCard: {
        width: "min(520px, calc(100vw - 40px))",
        border: "1px solid var(--studio-border)",
        borderRadius: 12,
        background: "var(--studio-surface)",
        boxShadow: "var(--studio-shadow-lg)",
        overflow: "hidden",
    },

    modalHeader: {
        padding: "20px 22px 16px",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 18,
        borderBottom: "1px solid var(--studio-surface-hover)",
    },

    modalEyebrow: {
        marginBottom: 6,
        color: "var(--studio-accent-hover)",
        fontSize: 10,
        fontWeight: 800,
        letterSpacing: "0.12em",
    },

    modalTitle: {
        margin: 0,
        color: "var(--studio-text)",
        fontSize: 18,
        fontWeight: 700,
    },

    modalSubtitle: {
        margin: "7px 0 0",
        color: "var(--studio-text-muted)",
        fontSize: 12,
        lineHeight: 1.55,
    },

    modalClose: {
        width: 30,
        height: 30,
        flexShrink: 0,
        border: "1px solid var(--studio-border)",
        borderRadius: 6,
        background: "var(--studio-surface-raised)",
        color: "var(--studio-text-secondary)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
    },

    modalBody: {
        padding: "18px 22px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 15,
    },

    modalField: {
        display: "flex",
        flexDirection: "column",
        gap: 7,
        color: "var(--studio-text-secondary)",
        fontSize: 12,
        fontWeight: 650,
    },

    modalInput: {
        width: "100%",
        height: 38,
        padding: "0 11px",
        border: "1px solid var(--studio-border)",
        borderRadius: 7,
        outline: "none",
        background: "var(--studio-canvas)",
        color: "var(--studio-text)",
        fontSize: 13,
        boxSizing: "border-box",
    },

    modalTextarea: {
        width: "100%",
        minHeight: 82,
        resize: "vertical",
        padding: "10px 11px",
        border: "1px solid var(--studio-border)",
        borderRadius: 7,
        outline: "none",
        background: "var(--studio-canvas)",
        color: "var(--studio-text)",
        fontSize: 13,
        lineHeight: 1.5,
        boxSizing: "border-box",
        fontFamily: "inherit",
    },

    modalHint: {
        color: "var(--studio-text-muted)",
        fontSize: 10.5,
        fontWeight: 500,
        lineHeight: 1.45,
    },

    modalError: {
        padding: "9px 11px",
        border: "1px solid color-mix(in srgb, var(--studio-danger) 45%, var(--studio-border))",
        borderRadius: 7,
        background: "var(--studio-danger-soft)",
        color: "var(--studio-danger)",
        fontSize: 11.5,
        lineHeight: 1.45,
    },

    modalFooter: {
        padding: "14px 22px",
        display: "flex",
        justifyContent: "flex-end",
        gap: 9,
        borderTop: "1px solid var(--studio-surface-hover)",
        background: "var(--studio-canvas)",
    },

    modalSecondaryButton: {
        height: 34,
        padding: "0 13px",
        border: "1px solid var(--studio-border-strong)",
        borderRadius: 6,
        background: "var(--studio-surface-raised)",
        color: "var(--studio-text)",
        fontSize: 12,
        fontWeight: 650,
        cursor: "pointer",
    },

    modalPrimaryButton: {
        height: 34,
        padding: "0 14px",
        border: "1px solid var(--studio-accent)",
        borderRadius: 6,
        background: "var(--studio-accent)",
        color: "var(--studio-text-on-accent)",
        fontSize: 12,
        fontWeight: 700,
        cursor: "pointer",
    },

    // ========================================================
    // GERENCIAMENTO DE BIBLIOTECAS
    // ========================================================

    modalCardWide: {
        width: "min(760px, calc(100vw - 40px))",
        maxHeight: "min(760px, calc(100vh - 48px))",
        display: "flex",
        flexDirection: "column",
        border: "1px solid var(--studio-border)",
        borderRadius: 12,
        background: "var(--studio-surface)",
        boxShadow: "var(--studio-shadow-lg)",
        overflow: "hidden",
    },


    libraryChoiceGrid: {
        padding: 22,
        display: "grid",
        gridTemplateColumns:
            "repeat(2, minmax(0, 1fr))",
        gap: 12,
    },


    libraryChoiceButton: {
        minHeight: 124,
        padding: 16,
        border: "1px solid var(--studio-border)",
        borderRadius: 10,
        background: "var(--studio-canvas)",
        color: "var(--studio-text)",
        display: "flex",
        alignItems: "flex-start",
        gap: 13,
        textAlign: "left",
    },


    libraryChoiceIcon: {
        width: 38,
        minWidth: 38,
        height: 38,
        borderRadius: 8,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--studio-accent-soft)",
        color: "var(--studio-accent-hover)",
    },


    existingLibrariesBody: {
        minHeight: 180,
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        overflow: "hidden",
    },


    existingLibrariesList: {
        display: "flex",
        flexDirection: "column",
        gap: 9,
        maxHeight: 440,
        overflowY: "auto",
        paddingRight: 4,
    },


    existingLibraryRow: {
        padding: 13,
        border: "1px solid var(--studio-border)",
        borderRadius: 9,
        display: "flex",
        flexDirection: "column",
        gap: 10,
        transition:
            "border-color 120ms ease, background 120ms ease",
    },


    existingLibraryMain: {
        display: "flex",
        alignItems: "flex-start",
        gap: 11,
    },


    libraryCheckbox: {
        width: 16,
        height: 16,
        marginTop: 3,
        accentColor: "var(--studio-accent)",
        cursor: "pointer",
    },


    existingLibraryInfo: {
        flex: 1,
        minWidth: 0,
        display: "flex",
        flexDirection: "column",
        gap: 4,
    },


    existingLibraryNameRow: {
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 8,
        color: "var(--studio-text)",
        fontSize: 13,
    },


    existingLibraryDescription: {
        color: "var(--studio-text-muted)",
        fontSize: 11,
        lineHeight: 1.4,
    },


    libraryAlreadyBadge: {
        padding: "2px 6px",
        border: "1px solid var(--studio-border-strong)",
        borderRadius: 999,
        color: "var(--studio-text-secondary)",
        fontSize: 9,
        fontWeight: 800,
        letterSpacing: "0.05em",
    },


    existingLibraryVersionArea: {
        marginLeft: 27,
        display: "grid",
        gridTemplateColumns: "70px minmax(180px, 1fr)",
        alignItems: "center",
        gap: 10,
        color: "var(--studio-text-secondary)",
        fontSize: 11,
    },


    libraryVersionSelect: {
        width: "100%",
        height: 34,
        padding: "0 9px",
        border: "1px solid var(--studio-border-strong)",
        borderRadius: 6,
        outline: "none",
        background: "var(--studio-canvas)",
        color: "var(--studio-text)",
        fontSize: 12,
    },


    productionVersionInfo: {
        marginLeft: 27,
        color: "var(--studio-accent-hover)",
        fontSize: 10.5,
    },


    oldVersionWarning: {
        marginLeft: 27,
        padding: "8px 10px",
        border: "1px solid color-mix(in srgb, var(--studio-warning) 45%, var(--studio-border))",
        borderRadius: 6,
        display: "flex",
        flexDirection: "column",
        gap: 3,
        background: "var(--studio-warning-soft)",
        color: "var(--studio-warning)",
        fontSize: 10.5,
        lineHeight: 1.45,
    },


    libraryEmptyState: {
        minHeight: 150,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: "1px dashed var(--studio-border)",
        borderRadius: 8,
        color: "var(--studio-text-muted)",
        fontSize: 12,
    },


    librarySelectionCount: {
        marginRight: "auto",
        display: "flex",
        alignItems: "center",
        color: "var(--studio-text-muted)",
        fontSize: 11,
    },
    statusBar: {
        height: 23,
        minHeight: 23,
        padding: "0 10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "color-mix(in srgb, var(--studio-accent) 72%, var(--studio-canvas))",
        color: "var(--studio-text-on-accent)",
        fontSize: 11,
        boxSizing: "border-box",
    },
};

export default RobotStudio;
