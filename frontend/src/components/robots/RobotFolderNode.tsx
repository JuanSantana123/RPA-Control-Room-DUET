// ============================================================
// DUET CORE - ROBOTS - ROBOT FOLDER NODE
// ============================================================
//
// Responsabilidade:
// - renderizar uma pasta individual da árvore de Robots;
// - renderizar recursivamente suas subpastas;
// - apresentar seleção, expansão e menu contextual da pasta.
//
// Os dados e ações são recebidos por propriedades.
//
// Este componente NÃO:
// - realiza chamadas HTTP;
// - cria ou exclui pastas diretamente;
// - realiza upload;
// - mantém a lista global de pastas;
// - contém regras de negócio do backend.
//
// Integrações:
// - RobotFolderTree;
// - tipo RobotFolder;
// - callbacks controlados futuramente pelos hooks/página Robots.
//
// IMPORTANTE:
// A estrutura visual e o comportamento correspondem ao
// renderizarPasta existente no Robots.tsx.
// ============================================================

import {
    ChevronDown,
    ChevronRight,
    Folder,
    FolderPlus,
    MoreVertical,
    Trash2,
    Upload,
} from "lucide-react";

import type { RobotFolder } from "../../types/robots";


interface RobotFolderNodeProps {
    folder: RobotFolder;
    folders: RobotFolder[];
    nivel?: number;

    selectedFolder: RobotFolder | null;
    expandedFolders: Set<number>;
    openFolderMenu: number | null;

    onSelectFolder: (folder: RobotFolder) => void;
    onToggleFolder: (folderId: number) => void;
    onSetOpenFolderMenu: (folderId: number | null) => void;
    onUploadRobot: (folderId: number) => void;
    onCreateSubfolder: (folder: RobotFolder) => void;
    onDeleteFolder: (folder: RobotFolder) => void;
}


function RobotFolderNode({
    folder,
    folders,
    nivel = 0,
    selectedFolder,
    expandedFolders,
    openFolderMenu,
    onSelectFolder,
    onToggleFolder,
    onSetOpenFolderMenu,
    onUploadRobot,
    onCreateSubfolder,
    onDeleteFolder,
}: RobotFolderNodeProps) {

    // --------------------------------------------------------
    // Localiza somente as filhas diretas da pasta atual.
    //
    // A recursão deste próprio componente permite qualquer
    // quantidade de níveis na árvore.
    // --------------------------------------------------------

    const subpastas = folders.filter(
        (candidate) =>
            candidate.parent_id === folder.id
    );

    const expandida =
        expandedFolders.has(folder.id);


    return (
        <div
            className="robot-folder-node"
        >
            {/* Linha visual da pasta */}
            <div
                className={`robot-folder-row ${
                    selectedFolder?.id === folder.id
                        ? "robot-folder-row-selected"
                        : ""
                }`}
                style={{
                    paddingLeft: `${nivel * 24}px`,
                }}
                onClick={() =>
                    onSetOpenFolderMenu(null)
                }
            >
                <div className="robot-folder-main">

                    {/* Botão de expansão */}
                    {subpastas.length > 0 ? (
                        <button
                            type="button"
                            className="robot-folder-expand"
                            onClick={() =>
                                onToggleFolder(folder.id)
                            }
                            aria-label={
                                expandida
                                    ? "Recolher pasta"
                                    : "Expandir pasta"
                            }
                        >
                            {expandida ? (
                                <ChevronDown size={16} />
                            ) : (
                                <ChevronRight size={16} />
                            )}
                        </button>
                    ) : (
                        <span className="robot-folder-expand-placeholder" />
                    )}


                    {/* Seleção da pasta */}
                    <button
                        type="button"
                        className="robot-folder-select"
                        onClick={(event) => {
                            event.stopPropagation();

                            onSelectFolder(folder);
                        }}
                    >
                        <Folder
                            size={17}
                            strokeWidth={1.8}
                            className="robot-folder-icon"
                        />

                        <span>{folder.name}</span>
                    </button>
                </div>


                {/* Menu de ações da pasta */}
                <div className="robot-folder-actions">
                    <button
                        type="button"
                        className="robot-folder-menu-button"
                        onClick={(event) => {
                            event.stopPropagation();

                            onSetOpenFolderMenu(
                                openFolderMenu === folder.id
                                    ? null
                                    : folder.id
                            );
                        }}
                        aria-label={`Ações da pasta ${folder.name}`}
                        title="Ações da pasta"
                    >
                        <MoreVertical
                            size={17}
                            strokeWidth={1.8}
                        />
                    </button>


                    {openFolderMenu === folder.id && (
                        <div className="robot-folder-context-menu">

                            {/* Adiciona Robot à pasta atual. */}
                            <button
                                type="button"
                                onClick={(event) => {
                                    event.stopPropagation();

                                    onUploadRobot(folder.id);
                                }}
                            >
                                <Upload
                                    size={15}
                                    strokeWidth={1.8}
                                />

                                <span>Adicionar robô</span>
                            </button>


                            {/* Cria uma subpasta dentro da pasta atual. */}
                            <button
                                type="button"
                                onClick={(event) => {
                                    event.stopPropagation();

                                    onCreateSubfolder(folder);
                                }}
                            >
                                <FolderPlus
                                    size={15}
                                    strokeWidth={1.8}
                                />

                                <span>Criar subpasta</span>
                            </button>


                            {/* Solicita exclusão da pasta atual. */}
                            <button
                                type="button"
                                className="robot-folder-context-danger"
                                onClick={(event) => {
                                    event.stopPropagation();

                                    onSetOpenFolderMenu(null);
                                    onDeleteFolder(folder);
                                }}
                            >
                                <Trash2
                                    size={15}
                                    strokeWidth={1.8}
                                />

                                <span>Excluir pasta</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>


            {/* Subpastas renderizadas recursivamente. */}
            {expandida && subpastas.length > 0 && (
                <div className="robot-folder-children">
                    {subpastas.map((subpasta) => (
                        <RobotFolderNode
                            key={subpasta.id}
                            folder={subpasta}
                            folders={folders}
                            nivel={nivel + 1}
                            selectedFolder={selectedFolder}
                            expandedFolders={expandedFolders}
                            openFolderMenu={openFolderMenu}
                            onSelectFolder={onSelectFolder}
                            onToggleFolder={onToggleFolder}
                            onSetOpenFolderMenu={onSetOpenFolderMenu}
                            onUploadRobot={onUploadRobot}
                            onCreateSubfolder={onCreateSubfolder}
                            onDeleteFolder={onDeleteFolder}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}


export default RobotFolderNode;