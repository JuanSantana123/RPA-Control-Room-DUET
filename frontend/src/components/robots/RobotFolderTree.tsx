import {
    Folder,
    FolderOpen,
    FolderPlus,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { RobotFolder } from "../../types/robots";
import {
    buildRobotFolderChildrenMap,
    getVisibleRobotFolderIds,
} from "../../utils/robotFolders";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import { FolderTreeToolbar } from "../ui/FolderTreeToolbar";
import { PanelSkeleton } from "../ui/Skeletons";
import RobotFolderNode from "./RobotFolderNode";

interface RobotFolderTreeProps {
    folders: RobotFolder[];
    canCreate: boolean;
    canDelete: boolean;
    loadingFolders: boolean;
    rootSelected: boolean;
    selectedFolder: RobotFolder | null;
    expandedFolders: Set<number>;
    openFolderMenu: number | null;
    onSelectRoot: () => void;
    onSelectFolder: (folder: RobotFolder) => void;
    onToggleFolder: (folderId: number) => void;
    onExpandAll: () => void;
    onCollapseAll: () => void;
    onSetOpenFolderMenu: (folderId: number | null) => void;
    onUploadRobot: (folderId: number) => void;
    onCreateRootFolder: () => void;
    onCreateSubfolder: (folder: RobotFolder) => void;
    onDeleteFolder: (folder: RobotFolder) => void;
}

function RobotFolderTree({
    folders,
    canCreate,
    canDelete,
    loadingFolders,
    rootSelected,
    selectedFolder,
    expandedFolders,
    openFolderMenu,
    onSelectRoot,
    onSelectFolder,
    onToggleFolder,
    onExpandAll,
    onCollapseAll,
    onSetOpenFolderMenu,
    onUploadRobot,
    onCreateRootFolder,
    onCreateSubfolder,
    onDeleteFolder,
}: RobotFolderTreeProps) {
    const [query, setQuery] = useState("");
    const visibleFolderIds = useMemo(
        () => getVisibleRobotFolderIds(folders, query),
        [folders, query],
    );
    const childrenByParent = useMemo(
        () => buildRobotFolderChildrenMap(folders),
        [folders],
    );
    const rootFolders = (childrenByParent.get(null) ?? [])
        .filter((folder) => !visibleFolderIds || visibleFolderIds.has(folder.id));
    const searching = Boolean(query.trim());
    const resultCount = visibleFolderIds
        ? folders.filter((folder) => visibleFolderIds.has(folder.id)).length
        : folders.length;

    useEffect(() => {
        if (openFolderMenu === null) return;

        const closeFromOutside = (event: PointerEvent) => {
            const target = event.target;
            if (target instanceof Element && target.closest(`[data-folder-actions="${openFolderMenu}"]`)) return;
            onSetOpenFolderMenu(null);
        };

        document.addEventListener("pointerdown", closeFromOutside);
        return () => document.removeEventListener("pointerdown", closeFromOutside);
    }, [onSetOpenFolderMenu, openFolderMenu]);

    if (loadingFolders) {
        return (
            <div className="robots-folders-content">
                <PanelSkeleton lines={4} />
            </div>
        );
    }

    return (
        <div className="robots-folders-content">
            {folders.length > 0 && (
                <FolderTreeToolbar
                    searchLabel="Pesquisar pastas"
                    searchPlaceholder="Pesquisar pastas..."
                    searchValue={query}
                    clearLabel="Limpar pesquisa de pastas"
                    onSearchChange={setQuery}
                    onExpandAll={onExpandAll}
                    onCollapseAll={onCollapseAll}
                />
            )}

            {searching && (
                <div className="robot-folder-search-status" role="status">
                    {resultCount === 0
                        ? "Nenhuma pasta corresponde à pesquisa."
                        : `${resultCount} ${resultCount === 1 ? "pasta visível" : "pastas visíveis"} no contexto da pesquisa.`}
                </div>
            )}

            {folders.length === 0 ? (
                <EmptyState
                    icon={<FolderPlus />}
                    title="Organize seu catálogo"
                    description="Crie a primeira pasta e depois adicione subpastas para representar áreas, processos ou ambientes."
                    action={canCreate ? (
                        <Button size="sm" onClick={onCreateRootFolder}>
                            <FolderPlus size={15} aria-hidden="true" />
                            Criar primeira pasta
                        </Button>
                    ) : undefined}
                />
            ) : searching && rootFolders.length === 0 ? (
                <EmptyState
                    icon={<Folder />}
                    title="Nenhuma pasta encontrada"
                    description="Tente outro termo ou limpe a pesquisa para voltar à árvore completa."
                    action={(
                        <Button size="sm" variant="secondary" onClick={() => setQuery("")}>
                            Limpar pesquisa
                        </Button>
                    )}
                />
            ) : (
                <div className="robot-folders-tree" role="tree" aria-label="Pastas de robôs">
                    {!searching && (
                        <div
                            className="robot-folder-node robot-folder-root"
                            role="treeitem"
                            aria-level={1}
                            aria-selected={rootSelected}
                        >
                            <div className={`robot-folder-row${rootSelected ? " robot-folder-row-selected" : ""}`}>
                                <div className="robot-folder-main">
                                    <button
                                        type="button"
                                        className="robot-folder-select"
                                        aria-pressed={rootSelected}
                                        onClick={onSelectRoot}
                                    >
                                        <span className="robot-folder-expand-placeholder" aria-hidden="true" />
                                        {rootSelected
                                            ? <FolderOpen className="robot-folder-icon" size={17} strokeWidth={1.8} aria-hidden="true" />
                                            : <Folder className="robot-folder-icon" size={17} strokeWidth={1.8} aria-hidden="true" />}
                                        <span className="robot-folder-name">Raiz de Robôs</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {rootFolders.map((folder) => (
                        <RobotFolderNode
                            key={folder.id}
                            folder={folder}
                            childrenByParent={childrenByParent}
                            canCreate={canCreate}
                            canDelete={canDelete}
                            visibleFolderIds={visibleFolderIds}
                            forceExpanded={searching}
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
