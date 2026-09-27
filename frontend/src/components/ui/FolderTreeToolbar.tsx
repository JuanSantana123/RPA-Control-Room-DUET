import {
    ChevronsDownUp,
    ChevronsUpDown,
} from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "./Button";
import SearchField from "./SearchField";
import "./folder-tree.css";

interface FolderTreeToolbarProps {
    searchLabel: string;
    searchPlaceholder: string;
    searchValue: string;
    clearLabel: string;
    summary?: ReactNode;
    onSearchChange: (value: string) => void;
    onExpandAll: () => void;
    onCollapseAll: () => void;
}

export function FolderTreeToolbar({
    searchLabel,
    searchPlaceholder,
    searchValue,
    clearLabel,
    summary,
    onSearchChange,
    onExpandAll,
    onCollapseAll,
}: FolderTreeToolbarProps) {
    return (
        <div className="folder-tree-toolbar">
            <SearchField
                label={searchLabel}
                placeholder={searchPlaceholder}
                value={searchValue}
                clearLabel={clearLabel}
                onValueChange={onSearchChange}
            />

            <div className="folder-tree-toolbar__footer">
                {summary && (
                    <div className="folder-tree-toolbar__summary">
                        {summary}
                    </div>
                )}
                <div
                    className="folder-tree-toolbar__actions"
                    aria-label="Controles da árvore"
                >
                    <Button size="sm" variant="ghost" onClick={onExpandAll}>
                        <ChevronsUpDown size={15} aria-hidden="true" />
                        Expandir
                    </Button>
                    <Button size="sm" variant="ghost" onClick={onCollapseAll}>
                        <ChevronsDownUp size={15} aria-hidden="true" />
                        Recolher
                    </Button>
                </div>
            </div>
        </div>
    );
}
