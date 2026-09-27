import type { RobotFolder } from "../types/robots";

const folderNameCollator = new Intl.Collator("pt-BR", {
    numeric: true,
    sensitivity: "base",
});

export function sortRobotFolders(folders: RobotFolder[]): RobotFolder[] {
    return [...folders].sort((left, right) => (
        folderNameCollator.compare(left.name, right.name)
    ));
}

export function getRobotFolderChildren(
    folders: RobotFolder[],
    parentId: number | null,
): RobotFolder[] {
    return sortRobotFolders(
        folders.filter((folder) => folder.parent_id === parentId),
    );
}

export function buildRobotFolderChildrenMap(
    folders: RobotFolder[],
): Map<number | null, RobotFolder[]> {
    const childrenByParent = new Map<number | null, RobotFolder[]>();

    for (const folder of folders) {
        const siblings = childrenByParent.get(folder.parent_id) ?? [];
        siblings.push(folder);
        childrenByParent.set(folder.parent_id, siblings);
    }

    for (const [parentId, children] of childrenByParent) {
        childrenByParent.set(parentId, sortRobotFolders(children));
    }

    return childrenByParent;
}

function getRobotFolderPathFromIndex(
    foldersById: Map<number, RobotFolder>,
    folderId: number,
): RobotFolder[] {
    const path: RobotFolder[] = [];
    const visited = new Set<number>();
    let current = foldersById.get(folderId);

    while (current && !visited.has(current.id)) {
        visited.add(current.id);
        path.unshift(current);
        current = current.parent_id === null
            ? undefined
            : foldersById.get(current.parent_id);
    }

    return path;
}

export function getRobotFolderPath(
    folders: RobotFolder[],
    folderId: number,
): RobotFolder[] {
    return getRobotFolderPathFromIndex(
        new Map(folders.map((folder) => [folder.id, folder])),
        folderId,
    );
}

export function getRobotFolderAncestorIds(
    folders: RobotFolder[],
    folderId: number,
): number[] {
    return getRobotFolderPath(folders, folderId)
        .slice(0, -1)
        .map((folder) => folder.id);
}

export interface RobotFolderOption {
    folder: RobotFolder;
    depth: number;
    pathLabel: string;
}

export function flattenRobotFolders(
    folders: RobotFolder[],
): RobotFolderOption[] {
    const result: RobotFolderOption[] = [];
    const visited = new Set<number>();
    const childrenByParent = buildRobotFolderChildrenMap(folders);

    const visit = (
        parentId: number | null,
        depth: number,
        parentNames: string[],
    ) => {
        for (const folder of childrenByParent.get(parentId) ?? []) {
            if (visited.has(folder.id)) continue;
            visited.add(folder.id);

            const pathNames = [...parentNames, folder.name];
            result.push({
                folder,
                depth,
                pathLabel: pathNames.join(" / "),
            });
            visit(folder.id, depth + 1, pathNames);
        }
    };

    visit(null, 0, []);
    return result;
}

function normalizeFolderSearch(value: string): string {
    return value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase("pt-BR")
        .trim();
}

export function getVisibleRobotFolderIds(
    folders: RobotFolder[],
    query: string,
): Set<number> | null {
    const normalizedQuery = normalizeFolderSearch(query);
    if (!normalizedQuery) return null;

    const visibleIds = new Set<number>();
    const foldersById = new Map(folders.map((folder) => [folder.id, folder]));

    for (const folder of folders) {
        if (!normalizeFolderSearch(folder.name).includes(normalizedQuery)) continue;

        for (const pathFolder of getRobotFolderPathFromIndex(foldersById, folder.id)) {
            visibleIds.add(pathFolder.id);
        }
    }

    return visibleIds;
}

export function countRobotFolderChildren(
    folders: RobotFolder[],
    folderId: number,
): number {
    return folders.reduce(
        (total, folder) => total + (folder.parent_id === folderId ? 1 : 0),
        0,
    );
}

export function isRobotFolder(value: unknown): value is RobotFolder {
    if (typeof value !== "object" || value === null) return false;

    const candidate = value as Record<string, unknown>;
    return Number.isInteger(candidate.id)
        && typeof candidate.name === "string"
        && candidate.name.trim().length > 0
        && (candidate.parent_id === null || Number.isInteger(candidate.parent_id));
}
