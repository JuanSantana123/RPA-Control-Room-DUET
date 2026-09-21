// ============================================================
// CREATE PROJECT FORM
// ============================================================
//
// Responsabilidade:
//     Renderiza o formulário utilizado para criar um novo
//     AutomationProject na área de Desenvolvimento.
//
// O componente suporta duas origens:
//
//     1. Novo Robô
//        Cria uma nova automação sem base em Produção.
//
//     2. Robô existente
//        Permite navegar pela estrutura de pastas da área de
//        Robôs e selecionar uma versão publicada como origem.
//
// Este componente apresenta:
//     - seleção do tipo de origem;
//     - árvore hierárquica de pastas;
//     - Robots da pasta selecionada;
//     - Robot de origem selecionado;
//     - título da demanda;
//     - descrição;
//     - ações Cancelar e Criar projeto.
//
// Arquitetura:
//     Este componente é exclusivamente responsável pela
//     apresentação e interação do formulário.
//
// Este arquivo NÃO deve:
//     - chamar endpoints HTTP;
//     - criar projetos diretamente;
//     - carregar Robots;
//     - conhecer regras de persistência;
//     - navegar para o Studio.
//
// Development.tsx continua responsável por:
//     - carregar a estrutura de Produção;
//     - manter os estados;
//     - executar POST /development/projects;
//     - atualizar lista e Kanban.
//
// A navegação visual das pastas fica neste componente porque
// é responsabilidade direta do formulário de criação.
// ============================================================

import {
    Folder,
    Plus,
} from "lucide-react";


import type {
    ReactNode,
} from "react";


import type {
    OriginRobot,
    OriginRobotFolder,
    ProjectOriginMode,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface CreateProjectFormProps {

    // ========================================================
    // ORIGEM
    // ========================================================

    originMode:
        ProjectOriginMode;


    baseRobotId:
        string;


    folders:
        OriginRobotFolder[];


    robots:
        OriginRobot[];


    selectedFolderId:
        number | null;


    robotsError:
        string;


    // ========================================================
    // DADOS DA DEMANDA
    // ========================================================

    projectName:
        string;


    projectDescription:
        string;


    // ========================================================
    // ESTADO OPERACIONAL
    // ========================================================

    creating:
        boolean;


    // ========================================================
    // CALLBACKS - ORIGEM
    // ========================================================

    onOriginModeChange:
        (mode: ProjectOriginMode) => void;


    onBaseRobotChange:
        (robotId: string) => void;


    onSelectedFolderChange:
        (folderId: number | null) => void;


    // ========================================================
    // CALLBACKS - DEMANDA
    // ========================================================

    onProjectNameChange:
        (value: string) => void;


    onProjectDescriptionChange:
        (value: string) => void;


    // ========================================================
    // AÇÕES
    // ========================================================

    onCancel:
        () => void;


    onCreate:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function CreateProjectForm({
    originMode,

    baseRobotId,

    folders,
    robots,

    selectedFolderId,

    robotsError,

    projectName,
    projectDescription,

    creating,

    onOriginModeChange,
    onBaseRobotChange,
    onSelectedFolderChange,

    onProjectNameChange,
    onProjectDescriptionChange,

    onCancel,
    onCreate,
}: CreateProjectFormProps) {

    // ========================================================
    // ROBOT SELECIONADO
    // ========================================================

    const selectedRobot =
        robots.find(
            (robot) =>
                String(robot.id) ===
                    baseRobotId
        ) ?? null;


    // ========================================================
    // ROBOTS DA PASTA ATUAL
    // ========================================================

    const robotsInSelectedFolder =
        robots.filter(
            (robot) =>
                robot.folder_id ===
                    selectedFolderId
        );


    // ========================================================
    // FILHOS DE UMA PASTA
    // ========================================================

    const getFolderChildren = (
        parentId: number | null
    ) =>
        folders
            .filter(
                (folder) =>
                    folder.parent_id ===
                        parentId
            )
            .sort(
                (a, b) =>
                    a.name.localeCompare(
                        b.name,
                        "pt-BR"
                    )
            );


    // ========================================================
    // CAMINHO AMIGÁVEL DA PASTA
    // ========================================================

    const getFolderPath = (
        folderId: number | null
    ): string => {

        if (folderId === null) {
            return "Raiz de Robôs";
        }


        const names:
            string[] = [];


        const visited =
            new Set<number>();


        let currentId:
            number | null =
                folderId;


        while (
            currentId !== null &&
            !visited.has(currentId)
        ) {

            visited.add(
                currentId
            );


            const folder =
                folders.find(
                    (item) =>
                        item.id === currentId
                );


            if (!folder) {
                break;
            }


            names.unshift(
                folder.name
            );


            currentId =
                folder.parent_id;
        }


        return [
            "Raiz de Robôs",
            ...names,
        ].join(" / ");
    };


    // ========================================================
    // ÁRVORE DE PASTAS
    // ========================================================

    const renderFolderTree = (
        parentId: number | null,
        depth = 0
    ): ReactNode[] => {

        return getFolderChildren(
            parentId
        ).flatMap(
            (folder) => [

                <button
                    key={
                        `folder-${folder.id}`
                    }

                    type="button"

                    disabled={
                        creating
                    }

                    onClick={() => {

                        // Muda a pasta exibida no navegador.
                        onSelectedFolderChange(
                            folder.id
                        );


                        // Ao trocar de pasta, remove qualquer Robot
                        // que estivesse selecionado em outra pasta.
                        onBaseRobotChange(
                            ""
                        );
                    }}

                    style={{
                        width:
                            "100%",

                        display:
                            "flex",

                        alignItems:
                            "center",

                        gap:
                            8,

                        padding:
                            `8px 10px 8px ${12 + depth * 18}px`,

                        border:
                            "none",

                        borderRadius:
                            7,

                        background:
                            selectedFolderId === folder.id
                                ? "var(--surface-hover, rgba(100, 116, 139, 0.14))"
                                : "transparent",

                        color:
                            "inherit",

                        textAlign:
                            "left",

                        cursor:
                            creating
                                ? "not-allowed"
                                : "pointer",

                        fontSize:
                            13,
                    }}
                >

                    <Folder
                        size={15}
                        strokeWidth={1.8}
                    />


                    <span>
                        {folder.name}
                    </span>

                </button>,


                // Renderização recursiva das subpastas.
                ...renderFolderTree(
                    folder.id,
                    depth + 1
                ),
            ]
        );
    };


    // ========================================================
    // VALIDAÇÃO VISUAL
    // ========================================================

    const createDisabled =
        !projectName.trim() ||
        creating ||
        (
            originMode === "existing" &&
            !baseRobotId
        );


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <div
            style={{
                padding:
                    18,

                marginBottom:
                    18,

                border:
                    "1px solid var(--border-color, #2f3540)",

                borderRadius:
                    8,
            }}
        >

            <div
                style={{
                    display:
                        "grid",

                    gap:
                        12,
                }}
            >

                {/* =================================================
                    ORIGEM DO PROJETO
                ================================================= */}

                <div
                    className="form-field"

                    style={{
                        gap:
                            10,
                    }}
                >

                    <label>
                        Origem do projeto
                    </label>


                    {/* =============================================
                        TIPO DE ORIGEM
                    ============================================= */}

                    <div
                        style={{
                            display:
                                "grid",

                            gridTemplateColumns:
                                "repeat(auto-fit, minmax(220px, 1fr))",

                            gap:
                                10,
                        }}
                    >

                        {/* =========================================
                            NOVO ROBÔ
                        ========================================= */}

                        <button
                            type="button"

                            disabled={
                                creating
                            }

                            onClick={() => {

                                onOriginModeChange(
                                    "new"
                                );


                                onBaseRobotChange(
                                    ""
                                );


                                onSelectedFolderChange(
                                    null
                                );
                            }}

                            style={{
                                padding:
                                    14,

                                border:
                                    originMode === "new"
                                        ? "1px solid var(--primary-color, #2563eb)"
                                        : "1px solid var(--border-color, #dfe3ea)",

                                borderRadius:
                                    9,

                                background:
                                    originMode === "new"
                                        ? "var(--surface-hover, rgba(37, 99, 235, 0.08))"
                                        : "transparent",

                                color:
                                    "inherit",

                                textAlign:
                                    "left",

                                cursor:
                                    creating
                                        ? "not-allowed"
                                        : "pointer",
                            }}
                        >

                            <div
                                style={{
                                    fontSize:
                                        13,

                                    fontWeight:
                                        700,

                                    marginBottom:
                                        4,
                                }}
                            >
                                Novo Robô
                            </div>


                            <div
                                style={{
                                    fontSize:
                                        12,

                                    opacity:
                                        0.68,

                                    lineHeight:
                                        1.45,
                                }}
                            >
                                Inicia uma nova automação sem
                                código de Produção como base.
                            </div>

                        </button>


                        {/* =========================================
                            ROBÔ EXISTENTE
                        ========================================= */}

                        <button
                            type="button"

                            disabled={
                                creating
                            }

                            onClick={() => {

                                onOriginModeChange(
                                    "existing"
                                );
                            }}

                            style={{
                                padding:
                                    14,

                                border:
                                    originMode === "existing"
                                        ? "1px solid var(--primary-color, #2563eb)"
                                        : "1px solid var(--border-color, #dfe3ea)",

                                borderRadius:
                                    9,

                                background:
                                    originMode === "existing"
                                        ? "var(--surface-hover, rgba(37, 99, 235, 0.08))"
                                        : "transparent",

                                color:
                                    "inherit",

                                textAlign:
                                    "left",

                                cursor:
                                    creating
                                        ? "not-allowed"
                                        : "pointer",
                            }}
                        >

                            <div
                                style={{
                                    fontSize:
                                        13,

                                    fontWeight:
                                        700,

                                    marginBottom:
                                        4,
                                }}
                            >
                                Robô existente
                            </div>


                            <div
                                style={{
                                    fontSize:
                                        12,

                                    opacity:
                                        0.68,

                                    lineHeight:
                                        1.45,
                                }}
                            >
                                Recupera uma versão já publicada
                                para criar uma nova alteração.
                            </div>

                        </button>

                    </div>


                    {/* =================================================
                        NAVEGADOR DE ROBÔS
                    ================================================= */}

                    {originMode ===
                        "existing" && (

                        <div
                            style={{
                                marginTop:
                                    4,

                                display:
                                    "grid",

                                gridTemplateColumns:
                                    "repeat(auto-fit, minmax(260px, 1fr))",

                                border:
                                    "1px solid var(--border-color, #dfe3ea)",

                                borderRadius:
                                    9,

                                overflow:
                                    "hidden",

                                minHeight:
                                    220,
                            }}
                        >

                            {/* =========================================
                                ÁRVORE DE PASTAS
                            ========================================= */}

                            <div
                                style={{
                                    padding:
                                        10,

                                    borderRight:
                                        "1px solid var(--border-color, #dfe3ea)",

                                    minWidth:
                                        0,
                                }}
                            >

                                <div
                                    style={{
                                        padding:
                                            "4px 8px 9px",

                                        fontSize:
                                            11,

                                        fontWeight:
                                            800,

                                        letterSpacing:
                                            "0.06em",

                                        opacity:
                                            0.55,

                                        textTransform:
                                            "uppercase",
                                    }}
                                >
                                    Pastas de Robôs
                                </div>


                                {/* =====================================
                                    RAIZ
                                ===================================== */}

                                <button
                                    type="button"

                                    disabled={
                                        creating
                                    }

                                    onClick={() => {

                                        onSelectedFolderChange(
                                            null
                                        );


                                        onBaseRobotChange(
                                            ""
                                        );
                                    }}

                                    style={{
                                        width:
                                            "100%",

                                        display:
                                            "flex",

                                        alignItems:
                                            "center",

                                        gap:
                                            8,

                                        padding:
                                            "8px 10px",

                                        border:
                                            "none",

                                        borderRadius:
                                            7,

                                        background:
                                            selectedFolderId === null
                                                ? "var(--surface-hover, rgba(100, 116, 139, 0.14))"
                                                : "transparent",

                                        color:
                                            "inherit",

                                        textAlign:
                                            "left",

                                        cursor:
                                            creating
                                                ? "not-allowed"
                                                : "pointer",

                                        fontSize:
                                            13,

                                        fontWeight:
                                            650,
                                    }}
                                >

                                    <Folder
                                        size={15}
                                        strokeWidth={1.8}
                                    />

                                    Raiz de Robôs

                                </button>


                                {/* Todas as subpastas. */}
                                {renderFolderTree(
                                    null
                                )}

                            </div>


                            {/* =========================================
                                ROBÔS DA PASTA
                            ========================================= */}

                            <div
                                style={{
                                    padding:
                                        12,

                                    minWidth:
                                        0,
                                }}
                            >

                                <div
                                    style={{
                                        marginBottom:
                                            10,
                                    }}
                                >

                                    <div
                                        style={{
                                            fontSize:
                                                11,

                                            fontWeight:
                                                800,

                                            letterSpacing:
                                                "0.06em",

                                            opacity:
                                                0.55,

                                            textTransform:
                                                "uppercase",
                                        }}
                                    >
                                        Robôs da pasta
                                    </div>


                                    <div
                                        style={{
                                            marginTop:
                                                3,

                                            fontSize:
                                                12,

                                            opacity:
                                                0.7,
                                        }}
                                    >
                                        {getFolderPath(
                                            selectedFolderId
                                        )}
                                    </div>

                                </div>


                                {robotsInSelectedFolder.length ===
                                    0 ? (

                                    <div
                                        style={{
                                            padding:
                                                "28px 14px",

                                            textAlign:
                                                "center",

                                            fontSize:
                                                12,

                                            opacity:
                                                0.6,
                                        }}
                                    >
                                        Nenhum Robô publicado
                                        nesta pasta.
                                    </div>

                                ) : (

                                    <div
                                        style={{
                                            display:
                                                "grid",

                                            gap:
                                                7,
                                        }}
                                    >

                                        {robotsInSelectedFolder.map(
                                            (robot) => {

                                                const selected =
                                                    String(
                                                        robot.id
                                                    ) ===
                                                    baseRobotId;


                                                return (

                                                    <button
                                                        key={
                                                            robot.id
                                                        }

                                                        type="button"

                                                        disabled={
                                                            creating
                                                        }

                                                        onClick={() => {

                                                            onBaseRobotChange(
                                                                String(
                                                                    robot.id
                                                                )
                                                            );
                                                        }}

                                                        style={{
                                                            width:
                                                                "100%",

                                                            display:
                                                                "flex",

                                                            alignItems:
                                                                "center",

                                                            justifyContent:
                                                                "space-between",

                                                            gap:
                                                                12,

                                                            padding:
                                                                "10px 12px",

                                                            border:
                                                                selected
                                                                    ? "1px solid var(--primary-color, #2563eb)"
                                                                    : "1px solid var(--border-color, #dfe3ea)",

                                                            borderRadius:
                                                                8,

                                                            background:
                                                                selected
                                                                    ? "var(--surface-hover, rgba(37, 99, 235, 0.08))"
                                                                    : "transparent",

                                                            color:
                                                                "inherit",

                                                            textAlign:
                                                                "left",

                                                            cursor:
                                                                creating
                                                                    ? "not-allowed"
                                                                    : "pointer",
                                                        }}
                                                    >

                                                        <div
                                                            style={{
                                                                minWidth:
                                                                    0,
                                                            }}
                                                        >

                                                            <div
                                                                style={{
                                                                    fontSize:
                                                                        13,

                                                                    fontWeight:
                                                                        700,

                                                                    overflow:
                                                                        "hidden",

                                                                    textOverflow:
                                                                        "ellipsis",

                                                                    whiteSpace:
                                                                        "nowrap",
                                                                }}
                                                            >
                                                                {robot.name}
                                                            </div>


                                                            <div
                                                                style={{
                                                                    marginTop:
                                                                        2,

                                                                    fontSize:
                                                                        11,

                                                                    opacity:
                                                                        0.62,
                                                                }}
                                                            >
                                                                Robot #{robot.id}
                                                            </div>

                                                        </div>


                                                        <span
                                                            style={{
                                                                flexShrink:
                                                                    0,

                                                                padding:
                                                                    "3px 7px",

                                                                borderRadius:
                                                                    999,

                                                                fontSize:
                                                                    11,

                                                                fontWeight:
                                                                    700,

                                                                background:
                                                                    "var(--surface-hover, rgba(100, 116, 139, 0.14))",
                                                            }}
                                                        >
                                                            v{robot.version}
                                                        </span>

                                                    </button>
                                                );
                                            }
                                        )}

                                    </div>
                                )}

                            </div>

                        </div>
                    )}


                    {/* =================================================
                        ROBOT SELECIONADO
                    ================================================= */}

                    {originMode ===
                        "existing" &&
                        selectedRobot && (

                        <div
                            style={{
                                padding:
                                    "10px 12px",

                                border:
                                    "1px solid rgba(37, 99, 235, 0.22)",

                                borderRadius:
                                    8,

                                background:
                                    "rgba(37, 99, 235, 0.06)",

                                fontSize:
                                    12,

                                lineHeight:
                                    1.5,
                            }}
                        >

                            <strong>
                                Selecionado:
                            </strong>{" "}


                            {getFolderPath(
                                selectedRobot.folder_id
                            )}


                            {" / "}


                            {selectedRobot.name}


                            {" · "}


                            versão {selectedRobot.version}


                            <div
                                style={{
                                    marginTop:
                                        2,

                                    opacity:
                                        0.72,
                                }}
                            >
                                O código e as Bibliotecas desta
                                versão serão recuperados no novo
                                projeto.
                            </div>

                        </div>
                    )}


                    {robotsError && (

                        <small role="alert">
                            {robotsError}
                        </small>
                    )}

                </div>


                {/* =================================================
                    TÍTULO DA DEMANDA
                ================================================= */}

                <div className="form-field">

                    <label
                        htmlFor="development-project-name"
                    >
                        Título da demanda
                    </label>


                    <input
                        id="development-project-name"

                        type="text"

                        value={
                            projectName
                        }

                        placeholder="Ex.: Melhoria no campo de contrato"

                        autoFocus

                        onChange={(event) => {

                            onProjectNameChange(
                                event.target.value
                            );
                        }}

                        onKeyDown={(event) => {

                            if (
                                event.key ===
                                "Enter"
                            ) {
                                onCreate();
                            }
                        }}
                    />

                </div>


                {/* =================================================
                    DESCRIÇÃO
                ================================================= */}

                <div className="form-field">

                    <label
                        htmlFor="development-project-description"
                    >
                        Descrição
                    </label>


                    <input
                        id="development-project-description"

                        type="text"

                        value={
                            projectDescription
                        }

                        placeholder="Descrição opcional da automação"

                        onChange={(event) => {

                            onProjectDescriptionChange(
                                event.target.value
                            );
                        }}
                    />

                </div>


                {/* =================================================
                    AÇÕES
                ================================================= */}

                <div
                    style={{
                        display:
                            "flex",

                        gap:
                            8,

                        justifyContent:
                            "flex-end",
                    }}
                >

                    <button
                        type="button"

                        className="secondary-button"

                        onClick={
                            onCancel
                        }
                    >
                        Cancelar
                    </button>


                    {/* Mantém o mesmo ícone utilizado atualmente
                        na área de criação do projeto. */}
                    <Plus
                        size={15}
                        strokeWidth={2}
                    />


                    <button
                        type="button"

                        className="primary-button"

                        disabled={
                            createDisabled
                        }

                        onClick={
                            onCreate
                        }
                    >

                        {creating
                            ? "Criando..."
                            : "Criar projeto"}

                    </button>

                </div>

            </div>

        </div>
    );
}


export default CreateProjectForm;