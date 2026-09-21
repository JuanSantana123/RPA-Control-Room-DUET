// ============================================================
// PUBLISH MODAL
// ============================================================
//
// Responsabilidade:
//     Renderiza o modal de Release/Publicação de um projeto
//     da área de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - versão do Robot que será publicada;
//     - Robot de Produção existente, quando aplicável;
//     - definição do nome de um novo Robot;
//     - árvore de pastas de destino;
//     - criação opcional de novas subpastas;
//     - dependências de Libraries;
//     - versões de Libraries modificadas;
//     - novos pacotes que serão publicados como Libraries;
//     - confirmação final da demanda.
//
// Arquitetura:
//     PublishModal.tsx é responsável somente pela interface
//     e pelas regras visuais do formulário.
//
// Este arquivo NÃO deve:
//     - consultar a prévia do Release;
//     - realizar POST de publicação;
//     - criar Robot no backend;
//     - publicar Library;
//     - alterar o Workflow;
//     - conhecer endpoints HTTP.
//
// Development.tsx continua responsável por:
//     - carregar ReleasePreview;
//     - manter os estados;
//     - validar regras de negócio no backend;
//     - executar a publicação;
//
// PublishModal.tsx:
//     - apresenta os dados;
//     - altera os estados através de callbacks;
//     - encaminha Cancelar/Publicar ao componente pai.
//
// A árvore de pastas também pertence a este componente porque
// ela é exclusivamente uma responsabilidade visual do modal.
// ============================================================

import {
    createPortal,
} from "react-dom";


import {
    Folder,
} from "lucide-react";


import type {
    ReactNode,
} from "react";


import type {
    DevelopmentProject,
    ReleasePreview,
} from "../../../types/development";


// ============================================================
// TIPO - NOVA LIBRARY DO RELEASE
// ============================================================
//
// O estado permanece indexado pelo namespace/pacote existente
// no projeto.
//
// Exemplo:
//
// {
//     "utils_pdf": {
//         name: "Utils PDF",
//         version: "1.0.0"
//     }
// }
// ============================================================

interface NewReleaseLibraryState {
    name: string;
    version: string;
}


type NewReleaseLibrariesState =
    Record<
        string,
        NewReleaseLibraryState
    >;


// ============================================================
// PROPS
// ============================================================

interface PublishModalProps {

    // Projeto cuja publicação está sendo preparada.
    //
    // null:
    //     modal fechado.
    project:
        DevelopmentProject | null;


    // Permissão efetiva de publicação.
    canPublish:
        boolean;


    // Prévia retornada pelo backend.
    preview:
        ReleasePreview | null;


    // Prévia ainda sendo carregada.
    loading:
        boolean;


    // ID do projeto cuja publicação está em andamento.
    publishingProjectId:
        number | null;


    // ========================================================
    // DESTINO DO ROBOT
    // ========================================================

    releaseFolderId:
        string;

    newReleaseFolder:
        string;

    releaseRobotName:
        string;


    // ========================================================
    // LIBRARIES
    // ========================================================

    releaseLibraryVersions:
        Record<number, string>;


    newReleaseLibraries:
        NewReleaseLibrariesState;


    // ========================================================
    // CONFIRMAÇÃO / ERRO
    // ========================================================

    confirmation:
        string;


    error:
        string;


    // ========================================================
    // CALLBACKS - ROBOT / DESTINO
    // ========================================================

    onReleaseFolderChange:
        (folderId: string) => void;


    onNewReleaseFolderChange:
        (value: string) => void;


    onReleaseRobotNameChange:
        (value: string) => void;


    // ========================================================
    // CALLBACKS - LIBRARIES EXISTENTES
    // ========================================================

    onLibraryVersionChange: (
        libraryId: number,
        version: string
    ) => void;


    // ========================================================
    // CALLBACKS - NOVAS LIBRARIES
    // ========================================================

    onNewLibraryToggle: (
        namespace: string,
        checked: boolean
    ) => void;


    onNewLibraryNameChange: (
        namespace: string,
        name: string
    ) => void;


    onNewLibraryVersionChange: (
        namespace: string,
        version: string
    ) => void;


    // ========================================================
    // CONFIRMAÇÃO / AÇÕES
    // ========================================================

    onConfirmationChange:
        (value: string) => void;


    onClose:
        () => void;


    onPublish:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function PublishModal({
    project,
    canPublish,

    preview,
    loading,

    publishingProjectId,

    releaseFolderId,
    newReleaseFolder,
    releaseRobotName,

    releaseLibraryVersions,
    newReleaseLibraries,

    confirmation,
    error,

    onReleaseFolderChange,
    onNewReleaseFolderChange,
    onReleaseRobotNameChange,

    onLibraryVersionChange,

    onNewLibraryToggle,
    onNewLibraryNameChange,
    onNewLibraryVersionChange,

    onConfirmationChange,

    onClose,
    onPublish,
}: PublishModalProps) {

    // ========================================================
    // MODAL FECHADO / SEM PERMISSÃO
    // ========================================================

    if (
        !project ||
        !canPublish
    ) {
        return null;
    }


    // ========================================================
    // CAMINHO DA PASTA
    // ========================================================
    //
    // Constrói o caminho amigável utilizando somente as pastas
    // recebidas na ReleasePreview.
    //
    // Exemplo:
    //
    // Financeiro / Pagamentos
    // ========================================================

    const getFolderLabel = (
        folderId: number | null
    ): string => {

        const names:
            string[] = [];


        const visited =
            new Set<number>();


        let id =
            folderId;


        while (
            id !== null &&
            !visited.has(id)
        ) {

            visited.add(
                id
            );


            const folder =
                preview?.folders.find(
                    (item) =>
                        item.id === id
                );


            if (!folder) {
                break;
            }


            names.unshift(
                folder.name
            );


            id =
                folder.parent_id;
        }


        return names.length
            ? names.join(" / ")
            : "Raiz de Robôs";
    };


    // ========================================================
    // ÁRVORE DE PASTAS
    // ========================================================
    //
    // Renderiza recursivamente todas as pastas disponíveis
    // para publicação de um Robot novo.
    // ========================================================

    const renderFolderTree = (
        parentId: number | null,
        depth = 0
    ): ReactNode[] => {

        if (!preview) {
            return [];
        }


        const children =
            preview.folders
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


        return children.flatMap(
            (folder) => [

                <button
                    key={
                        `release-folder-${folder.id}`
                    }

                    type="button"

                    disabled={
                        publishingProjectId !==
                            null
                    }

                    onClick={() => {

                        onReleaseFolderChange(
                            String(
                                folder.id
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

                        gap:
                            8,

                        // Cada nível recebe indentação adicional.
                        padding:
                            `8px 10px 8px ${12 + depth * 18}px`,

                        border:
                            "none",

                        borderRadius:
                            7,

                        background:
                            releaseFolderId ===
                                String(folder.id)
                                ? "var(--surface-hover, rgba(37, 99, 235, 0.10))"
                                : "transparent",

                        color:
                            "inherit",

                        textAlign:
                            "left",

                        cursor:
                            publishingProjectId !== null
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


                // Renderiza recursivamente as subpastas.
                ...renderFolderTree(
                    folder.id,
                    depth + 1
                ),
            ]
        );
    };


    // ========================================================
    // VALIDAÇÃO VISUAL DO BOTÃO
    // ========================================================
    //
    // Mantém exatamente os critérios já utilizados pelo
    // Development.tsx antes da extração deste modal.
    // ========================================================

    const publishDisabled =
        !preview ||
        loading ||
        publishingProjectId !== null ||
        confirmation !== project.name ||
        !releaseRobotName.trim() ||
        Object
            .values(
                releaseLibraryVersions
            )
            .some(
                (value) =>
                    !value.trim()
            ) ||
        Object
            .values(
                newReleaseLibraries
            )
            .some(
                (value) =>
                    !value.name.trim() ||
                    !value.version.trim()
            );


    // ========================================================
    // INTERFACE
    // ========================================================

    return createPortal(

        <div
            role="presentation"

            onMouseDown={
                onClose
            }

            style={{
                position:
                    "fixed",

                inset:
                    0,

                zIndex:
                    10000,

                display:
                    "flex",

                alignItems:
                    "center",

                justifyContent:
                    "center",

                padding:
                    20,

                background:
                    "rgba(15, 23, 42, 0.48)",
            }}
        >

            <div
                role="dialog"

                aria-modal="true"

                aria-labelledby="development-publish-title"

                onMouseDown={(event) => {
                    event.stopPropagation();
                }}

                style={{
                    width:
                        "100%",

                    maxWidth:
                        660,

                    maxHeight:
                        "85vh",

                    overflowY:
                        "auto",

                    padding:
                        24,

                    borderRadius:
                        12,

                    background:
                        "var(--surface-color, #ffffff)",

                    boxShadow:
                        "0 24px 70px rgba(15,23,42,.28)",
                }}
            >

                {/* =================================================
                    CABEÇALHO
                ================================================= */}

                <h2
                    id="development-publish-title"

                    style={{
                        marginTop:
                            0,
                    }}
                >
                    Publicar Release
                </h2>


                <p>
                    {project.name}
                </p>


                {loading && (

                    <p role="status">
                        Preparando prévia...
                    </p>
                )}


                {/* =================================================
                    PRÉVIA
                ================================================= */}

                {preview && (
                    <>

                        <p>
                            <strong>
                                Versão do Robô:{" "}
                                {preview.next_version}
                            </strong>
                        </p>


                        {/* =========================================
                            ROBOT EXISTENTE
                        ========================================= */}

                        {preview.robot ? (

                            <p>

                                Destino:{" "}

                                <strong>
                                    {getFolderLabel(
                                        preview.robot.folder_id
                                    )}
                                </strong>

                                <br />

                                Robô:{" "}
                                {preview.robot.name}{" "}
                                (#{preview.robot.id})

                            </p>

                        ) : (

                            // =====================================
                            // ROBOT NOVO
                            // =====================================

                            <fieldset
                                disabled={
                                    publishingProjectId !==
                                        null
                                }

                                style={{
                                    border:
                                        0,

                                    padding:
                                        0,

                                    margin:
                                        0,
                                }}
                            >

                                {/* =================================
                                    NOME DO ROBOT
                                ================================= */}

                                <div className="form-field">

                                    <label
                                        htmlFor="release-robot-name"
                                    >
                                        Nome do novo Robô
                                    </label>


                                    <input
                                        id="release-robot-name"

                                        value={
                                            releaseRobotName
                                        }

                                        onChange={(event) => {

                                            onReleaseRobotNameChange(
                                                event.target.value
                                            );
                                        }}
                                    />

                                </div>


                                {/* =================================
                                    PASTA DE DESTINO
                                ================================= */}

                                <div
                                    className="form-field"

                                    style={{
                                        marginTop:
                                            12,
                                    }}
                                >

                                    <label>
                                        Pasta de destino
                                    </label>


                                    <div
                                        style={{
                                            marginTop:
                                                6,

                                            padding:
                                                10,

                                            border:
                                                "1px solid var(--border-color, #dfe3ea)",

                                            borderRadius:
                                                9,

                                            maxHeight:
                                                230,

                                            overflowY:
                                                "auto",
                                        }}
                                    >

                                        {/* =========================
                                            RAIZ DE ROBÔS
                                        ========================= */}

                                        <button
                                            type="button"

                                            disabled={
                                                publishingProjectId !==
                                                    null
                                            }

                                            onClick={() => {

                                                // String vazia representa
                                                // null para o backend.
                                                onReleaseFolderChange(
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
                                                    releaseFolderId === ""
                                                        ? "var(--surface-hover, rgba(37, 99, 235, 0.10))"
                                                        : "transparent",

                                                color:
                                                    "inherit",

                                                textAlign:
                                                    "left",

                                                cursor:
                                                    publishingProjectId !== null
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


                                        {/* Toda a hierarquia. */}
                                        {renderFolderTree(
                                            null
                                        )}

                                    </div>


                                    {/* =============================
                                        DESTINO ESCOLHIDO
                                    ============================= */}

                                    <div
                                        style={{
                                            marginTop:
                                                7,

                                            padding:
                                                "8px 10px",

                                            borderRadius:
                                                7,

                                            background:
                                                "var(--surface-hover, rgba(100, 116, 139, 0.08))",

                                            fontSize:
                                                12,
                                        }}
                                    >

                                        <span
                                            style={{
                                                opacity:
                                                    0.65,
                                            }}
                                        >
                                            Destino selecionado:
                                        </span>

                                        {" "}

                                        <strong>

                                            {releaseFolderId
                                                ? getFolderLabel(
                                                    Number(
                                                        releaseFolderId
                                                    )
                                                )
                                                : "Raiz de Robôs"}

                                        </strong>

                                    </div>

                                </div>


                                {/* =================================
                                    NOVAS SUBPASTAS
                                ================================= */}

                                <div
                                    className="form-field"

                                    style={{
                                        marginTop:
                                            12,
                                    }}
                                >

                                    <label
                                        htmlFor="release-new-folder"
                                    >
                                        Criar pastas dentro do destino (opcional)
                                    </label>


                                    <input
                                        id="release-new-folder"

                                        value={
                                            newReleaseFolder
                                        }

                                        placeholder="Ex.: Financeiro/Pagamentos"

                                        onChange={(event) => {

                                            onNewReleaseFolderChange(
                                                event.target.value
                                            );
                                        }}
                                    />

                                </div>

                            </fieldset>
                        )}


                        {/* =================================================
                            LIBRARIES EXISTENTES
                        ================================================= */}

                        <h3
                            style={{
                                marginBottom:
                                    8,
                            }}
                        >
                            Bibliotecas
                        </h3>


                        {preview.dependencies.length ===
                            0 && (

                            <p>
                                Este projeto não possui Bibliotecas vinculadas.
                            </p>
                        )}


                        {preview.dependencies.map(
                            (dependency) => (

                                <div
                                    key={
                                        dependency.library_id
                                    }

                                    style={{
                                        padding:
                                            "12px 0",

                                        borderBottom:
                                            "1px solid var(--border-color, #dfe3ea)",
                                    }}
                                >

                                    <strong>
                                        {dependency.library_name}
                                    </strong>


                                    {dependency.modified ? (

                                        <div
                                            className="form-field"

                                            style={{
                                                marginTop:
                                                    8,
                                            }}
                                        >

                                            <label
                                                htmlFor={
                                                    `release-library-${dependency.library_id}`
                                                }
                                            >
                                                Base{" "}
                                                {dependency.version}{" "}
                                                alterada — publicar como
                                            </label>


                                            <input
                                                id={
                                                    `release-library-${dependency.library_id}`
                                                }

                                                disabled={
                                                    publishingProjectId !==
                                                        null
                                                }

                                                value={
                                                    releaseLibraryVersions[
                                                        dependency.library_id
                                                    ] || ""
                                                }

                                                onChange={(event) => {

                                                    onLibraryVersionChange(
                                                        dependency.library_id,
                                                        event.target.value
                                                    );
                                                }}
                                            />

                                        </div>

                                    ) : (

                                        <span>
                                            {" — manter "}
                                            {dependency.version}
                                        </span>
                                    )}

                                </div>
                            )
                        )}


                        {/* =================================================
                            NOVAS LIBRARIES
                        ================================================= */}

                        {preview.library_candidates.length >
                            0 && (
                            <>

                                <h3>
                                    Publicar novas Bibliotecas
                                </h3>


                                <p
                                    style={{
                                        fontSize:
                                            13,
                                    }}
                                >
                                    Selecione os pacotes do projeto que deseja
                                    disponibilizar para outros Robôs.
                                </p>


                                {preview.library_candidates.map(
                                    (namespace) => (

                                        <div
                                            key={
                                                namespace
                                            }

                                            style={{
                                                marginBottom:
                                                    12,
                                            }}
                                        >

                                            <label
                                                style={{
                                                    display:
                                                        "flex",

                                                    alignItems:
                                                        "center",

                                                    gap:
                                                        8,
                                                }}
                                            >

                                                <input
                                                    type="checkbox"

                                                    checked={
                                                        Boolean(
                                                            newReleaseLibraries[
                                                                namespace
                                                            ]
                                                        )
                                                    }

                                                    disabled={
                                                        publishingProjectId !==
                                                            null
                                                    }

                                                    onChange={(event) => {

                                                        onNewLibraryToggle(
                                                            namespace,
                                                            event.target.checked
                                                        );
                                                    }}
                                                />

                                                {namespace}

                                            </label>


                                            {newReleaseLibraries[
                                                namespace
                                            ] && (

                                                <div
                                                    style={{
                                                        display:
                                                            "flex",

                                                        gap:
                                                            8,

                                                        marginTop:
                                                            8,
                                                    }}
                                                >

                                                    {/* =====================
                                                        NOME
                                                    ===================== */}

                                                    <div
                                                        className="form-field"

                                                        style={{
                                                            flex:
                                                                1,
                                                        }}
                                                    >

                                                        <label
                                                            htmlFor={
                                                                `new-library-name-${namespace}`
                                                            }
                                                        >
                                                            Nome
                                                        </label>


                                                        <input
                                                            id={
                                                                `new-library-name-${namespace}`
                                                            }

                                                            disabled={
                                                                publishingProjectId !==
                                                                    null
                                                            }

                                                            value={
                                                                newReleaseLibraries[
                                                                    namespace
                                                                ].name
                                                            }

                                                            onChange={(event) => {

                                                                onNewLibraryNameChange(
                                                                    namespace,
                                                                    event.target.value
                                                                );
                                                            }}
                                                        />

                                                    </div>


                                                    {/* =====================
                                                        VERSÃO
                                                    ===================== */}

                                                    <div
                                                        className="form-field"

                                                        style={{
                                                            width:
                                                                130,
                                                        }}
                                                    >

                                                        <label
                                                            htmlFor={
                                                                `new-library-version-${namespace}`
                                                            }
                                                        >
                                                            Versão
                                                        </label>


                                                        <input
                                                            id={
                                                                `new-library-version-${namespace}`
                                                            }

                                                            disabled={
                                                                publishingProjectId !==
                                                                    null
                                                            }

                                                            value={
                                                                newReleaseLibraries[
                                                                    namespace
                                                                ].version
                                                            }

                                                            onChange={(event) => {

                                                                onNewLibraryVersionChange(
                                                                    namespace,
                                                                    event.target.value
                                                                );
                                                            }}
                                                        />

                                                    </div>

                                                </div>
                                            )}

                                        </div>
                                    )
                                )}

                            </>
                        )}


                        <p
                            style={{
                                fontSize:
                                    13,
                            }}
                        >
                            O Release inclui o código atual e as Bibliotecas acima.
                            As versões anteriores permanecem preservadas.
                        </p>


                        {/* =================================================
                            CONFIRMAÇÃO
                        ================================================= */}

                        <div className="form-field">

                            <label
                                htmlFor="development-publish-confirmation"
                            >
                                Digite o título da demanda para confirmar
                            </label>


                            <input
                                id="development-publish-confirmation"

                                value={
                                    confirmation
                                }

                                disabled={
                                    publishingProjectId !==
                                        null
                                }

                                placeholder={
                                    project.name
                                }

                                onChange={(event) => {

                                    onConfirmationChange(
                                        event.target.value
                                    );
                                }}
                            />

                        </div>

                    </>
                )}


                {/* =================================================
                    ERRO
                ================================================= */}

                {error && (

                    <div
                        role="alert"

                        className="alert alert-error"

                        style={{
                            marginTop:
                                14,
                        }}
                    >
                        {error}
                    </div>
                )}


                {/* =================================================
                    AÇÕES
                ================================================= */}

                <div
                    style={{
                        display:
                            "flex",

                        justifyContent:
                            "flex-end",

                        gap:
                            8,

                        marginTop:
                            20,
                    }}
                >

                    <button
                        type="button"

                        className="secondary-button"

                        disabled={
                            publishingProjectId !==
                                null
                        }

                        onClick={
                            onClose
                        }
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"

                        className="primary-button"

                        onClick={
                            onPublish
                        }

                        disabled={
                            publishDisabled
                        }
                    >
                        {publishingProjectId !== null
                            ? "Publicando..."
                            : "Publicar Release"}
                    </button>

                </div>

            </div>

        </div>,

        document.body
    );
}


export default PublishModal;