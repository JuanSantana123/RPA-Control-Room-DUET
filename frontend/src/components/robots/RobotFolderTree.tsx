// ============================================================
// DUET CORE - ROBOTS - ROBOT FOLDER TREE
// ============================================================
//
// Responsabilidade:
// - renderizar a árvore completa de pastas de Robots;
// - apresentar a localização lógica "Raiz de Robôs";
// - iniciar a renderização recursiva das pastas reais.
//
// Este componente NÃO:
// - busca pastas no backend;
// - carrega Robots;
// - cria ou exclui pastas;
// - executa uploads;
// - mantém regras de negócio.
//
// A página/hook continua sendo responsável pelos estados e
// operações. Este componente apenas recebe dados e callbacks.
//
// Integrações:
// - RobotFolderNode;
// - tipo RobotFolder;
// - página Robots / futuro hook useRobotFolders.
//
// IMPORTANTE:
// "Raiz de Robôs" continua sendo uma localização lógica,
// não uma RobotFolder persistida no banco.
// ============================================================

import { Folder } from "lucide-react";

import type { RobotFolder } from "../../types/robots";
import RobotFolderNode from "./RobotFolderNode";


interface RobotFolderTreeProps {
    folders: RobotFolder[];

    loadingFolders: boolean;

    rootSelected: boolean;
    selectedFolder: RobotFolder | null;

    expandedFolders: Set<number>;
    openFolderMenu: number | null;

    onSelectRoot: () => void;
    onSelectFolder: (folder: RobotFolder) => void;
    onToggleFolder: (folderId: number) => void;
    onSetOpenFolderMenu: (folderId: number | null) => void;
    onUploadRobot: (folderId: number) => void;
    onCreateSubfolder: (folder: RobotFolder) => void;
    onDeleteFolder: (folder: RobotFolder) => void;
}


function RobotFolderTree({
    folders,
    loadingFolders,
    rootSelected,
    selectedFolder,
    expandedFolders,
    openFolderMenu,
    onSelectRoot,
    onSelectFolder,
    onToggleFolder,
    onSetOpenFolderMenu,
    onUploadRobot,
    onCreateSubfolder,
    onDeleteFolder,
}: RobotFolderTreeProps) {

    return (
        <div className="robots-folders-content">

            {loadingFolders ? (
                <div className="panel-loading">
                    Carregando pastas...
                </div>
            ) : (
                <div className="robot-folders-tree">

                    {/* ====================================================
                        RAIZ DE ROBÔS

                        A raiz é uma localização lógica e permanente.

                        Não possui:
                        - ID de RobotFolder;
                        - menu de exclusão;
                        - renomeação;
                        - movimentação.

                        Ao selecioná-la, mostramos somente Robots
                        cujo folder_id é NULL.
                    ==================================================== */}

                    <div className="robot-folder-node">
                        <div
                            className={`robot-folder-row ${
                                rootSelected
                                    ? "robot-folder-row-selected"
                                    : ""
                            }`}
                        >
                            <div className="robot-folder-main">

                                {/* Mantém alinhamento com as pastas normais. */}
                                <span className="robot-folder-expand-placeholder" />

                                <button
                                    type="button"
                                    className="robot-folder-select"
                                    onClick={onSelectRoot}
                                >
                                    <Folder
                                        size={17}
                                        strokeWidth={1.8}
                                        className="robot-folder-icon"
                                    />

                                    <span>Raiz de Robôs</span>
                                </button>
                            </div>
                        </div>
                    </div>


                    {/* ====================================================
                        PASTAS REAIS

                        Apenas pastas com parent_id NULL iniciam a árvore.
                        Cada RobotFolderNode renderiza suas próprias filhas
                        recursivamente.
                    ==================================================== */}

                    {folders
                        .filter(
                            (folder) =>
                                folder.parent_id === null
                        )
                        .map((folder) => (
                            <RobotFolderNode
                                key={folder.id}
                                folder={folder}
                                folders={folders}
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


export default RobotFolderTree;