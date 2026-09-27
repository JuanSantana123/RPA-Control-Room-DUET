import {
    ChevronDown,
    ChevronRight,
    Folder,
    FolderOpen,
    FolderPlus,
    MoreVertical,
    Trash2,
    Upload,
} from "lucide-react";
import { useEffect, useRef } from "react";

import type { RobotFolder } from "../../types/robots";

interface RobotFolderNodeProps {
    folder: RobotFolder;
    childrenByParent: Map<number | null, RobotFolder[]>;
    canCreate: boolean;
    canDelete: boolean;
    level?: number;
    visibleFolderIds?: Set<number> | null;
    forceExpanded?: boolean;
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
    childrenByParent,
    canCreate,
    canDelete,
    level = 0,
    visibleFolderIds,
    forceExpanded = false,
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
    const menuButtonRef = useRef<HTMLButtonElement>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const allChildFolders = childrenByParent.get(folder.id) ?? [];
    const childFolders = allChildFolders
        .filter((child) => !visibleFolderIds || visibleFolderIds.has(child.id));
    const allChildCount = allChildFolders.length;
    const hasChildren = allChildCount > 0;
    const expanded = hasChildren && (forceExpanded || expandedFolders.has(folder.id));
    const selected = selectedFolder?.id === folder.id;
    const menuOpen = openFolderMenu === folder.id;

    useEffect(() => {
        if (!menuOpen) return;

        menuRef.current?.querySelector<HTMLButtonElement>("button")?.focus();

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key !== "Escape") return;
            event.preventDefault();
            onSetOpenFolderMenu(null);
            menuButtonRef.current?.focus();
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [menuOpen, onSetOpenFolderMenu]);

    return (
        <div
            className="robot-folder-node"
            role="treeitem"
            aria-level={level + 1}
            aria-selected={selected}
            aria-expanded={hasChildren ? expanded : undefined}
        >
            <div
                className={`robot-folder-row${selected ? " robot-folder-row-selected" : ""}`}
                style={{ paddingLeft: `${level * 20}px` }}
                onClick={() => onSetOpenFolderMenu(null)}
            >
                <div className="robot-folder-main">
                    {hasChildren ? (
                        <button
                            type="button"
                            className="robot-folder-expand"
                            onClick={(event) => {
                                event.stopPropagation();
                                onToggleFolder(folder.id);
                            }}
                            aria-label={expanded
                                ? `Recolher pasta ${folder.name}`
                                : `Expandir pasta ${folder.name}`}
                        >
                            {expanded
                                ? <ChevronDown size={15} aria-hidden="true" />
                                : <ChevronRight size={15} aria-hidden="true" />}
                        </button>
                    ) : null}

                    <button
                        type="button"
                        className="robot-folder-select"
                        aria-pressed={selected}
                        aria-label={folder.name}
                        title={folder.name}
                        onClick={(event) => {
                            event.stopPropagation();
                            onSelectFolder(folder);
                        }}
                    >
                        {!hasChildren && (
                            <span className="robot-folder-expand-placeholder" aria-hidden="true" />
                        )}
                        {selected || expanded
                            ? <FolderOpen className="robot-folder-icon" size={17} strokeWidth={1.8} aria-hidden="true" />
                            : <Folder className="robot-folder-icon" size={17} strokeWidth={1.8} aria-hidden="true" />}
                        <span className="robot-folder-name">{folder.name}</span>
                        {allChildCount > 0 && (
                            <span
                                className="robot-folder-child-count"
                                aria-label={`${allChildCount} ${allChildCount === 1 ? "subpasta" : "subpastas"}`}
                            >
                                {allChildCount}
                            </span>
                        )}
                    </button>
                </div>

                {(canCreate || canDelete) && (
                    <div className="robot-folder-actions" data-folder-actions={folder.id}>
                        {canCreate && (
                            <button
                                type="button"
                                className="robot-folder-quick-add"
                                aria-label={`Criar subpasta em ${folder.name}`}
                                title="Criar subpasta"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    onCreateSubfolder(folder);
                                }}
                            >
                                <FolderPlus size={16} strokeWidth={1.8} aria-hidden="true" />
                            </button>
                        )}
                        <button
                            ref={menuButtonRef}
                            type="button"
                            className="robot-folder-menu-button"
                            onClick={(event) => {
                                event.stopPropagation();
                                onSetOpenFolderMenu(menuOpen ? null : folder.id);
                            }}
                            aria-label={`Ações da pasta ${folder.name}`}
                            title="Mais ações"
                            aria-haspopup="menu"
                            aria-expanded={menuOpen}
                            aria-controls={`robot-folder-menu-${folder.id}`}
                        >
                            <MoreVertical size={17} strokeWidth={1.8} aria-hidden="true" />
                        </button>

                        {menuOpen && (
                            <div
                                ref={menuRef}
                                id={`robot-folder-menu-${folder.id}`}
                                className="robot-folder-context-menu"
                                role="menu"
                                aria-label={`Ações da pasta ${folder.name}`}
                            >
                                {canCreate && (
                                    <button
                                        type="button"
                                        role="menuitem"
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            onSetOpenFolderMenu(null);
                                            onUploadRobot(folder.id);
                                        }}
                                    >
                                        <Upload size={15} strokeWidth={1.8} aria-hidden="true" />
                                        <span>Enviar pacote</span>
                                    </button>
                                )}
                                {canCreate && (
                                    <button
                                        type="button"
                                        role="menuitem"
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            onSetOpenFolderMenu(null);
                                            onCreateSubfolder(folder);
                                        }}
                                    >
                                        <FolderPlus size={15} strokeWidth={1.8} aria-hidden="true" />
                                        <span>Criar subpasta</span>
                                    </button>
                                )}
                                {canDelete && (
                                    <button
                                        type="button"
                                        role="menuitem"
                                        className="robot-folder-context-danger"
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            onSetOpenFolderMenu(null);
                                            onDeleteFolder(folder);
                                        }}
                                    >
                                        <Trash2 size={15} strokeWidth={1.8} aria-hidden="true" />
                                        <span>Excluir pasta</span>
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {expanded && childFolders.length > 0 && (
                <div className="robot-folder-children" role="group">
                    {childFolders.map((child) => (
                        <RobotFolderNode
                            key={child.id}
                            folder={child}
                            childrenByParent={childrenByParent}
                            canCreate={canCreate}
                            canDelete={canDelete}
                            level={level + 1}
                            visibleFolderIds={visibleFolderIds}
                            forceExpanded={forceExpanded}
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
