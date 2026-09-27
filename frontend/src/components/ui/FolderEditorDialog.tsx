import {
    ChevronRight,
    Folder,
    FolderPlus,
    Plus,
    Save,
    X,
} from "lucide-react";
import type { FormEvent } from "react";
import { createPortal } from "react-dom";

import { useDialogFocus } from "../../hooks/ui/useDialogFocus";
import { Button, IconButton } from "./Button";
import PremiumSelect from "./PremiumSelect";
import { TextField } from "./TextField";
import "./folder-tree.css";

export interface FolderDestinationOption {
    id: number;
    name: string;
    depth: number;
    path: string[];
}

interface FolderEditorDialogProps {
    idPrefix: string;
    mode: "create" | "rename";
    eyebrow: string;
    rootLabel: string;
    name: string;
    parentId: number | null;
    options: FolderDestinationOption[];
    busy: boolean;
    placeholder?: string;
    onNameChange: (value: string) => void;
    onParentChange: (parentId: number | null) => void;
    onSubmit: () => void;
    onCancel: () => void;
}

export function FolderEditorDialog({
    idPrefix,
    mode,
    eyebrow,
    rootLabel,
    name,
    parentId,
    options,
    busy,
    placeholder = "Ex.: Financeiro",
    onNameChange,
    onParentChange,
    onSubmit,
    onCancel,
}: FolderEditorDialogProps) {
    const dialogRef = useDialogFocus<HTMLDivElement>({
        open: true,
        onClose: onCancel,
        closeOnEscape: !busy,
    });
    const selectedDestination = parentId === null
        ? null
        : options.find((option) => option.id === parentId) ?? null;
    const isCreate = mode === "create";
    const isSubfolder = isCreate && parentId !== null;
    const title = isCreate
        ? isSubfolder ? "Nova subpasta" : "Nova pasta"
        : "Renomear pasta";
    const description = isCreate
        ? "Defina um nome e escolha exatamente onde ela será criada."
        : "Atualize o nome sem alterar a localização atual da pasta.";

    const submit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!busy && name.trim()) onSubmit();
    };

    return createPortal(
        <div
            className="folder-editor-overlay ui-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget && !busy) onCancel();
            }}
        >
            <div
                ref={dialogRef}
                className="folder-editor-dialog ui-modal-surface"
                role="dialog"
                aria-modal="true"
                aria-labelledby={`${idPrefix}-title`}
                aria-describedby={`${idPrefix}-description`}
                tabIndex={-1}
            >
                <header className="folder-editor-dialog__header ui-modal-header">
                    <span className="folder-editor-dialog__icon" aria-hidden="true">
                        <FolderPlus size={20} strokeWidth={1.8} />
                    </span>
                    <div>
                        <span className="folder-editor-dialog__eyebrow">{eyebrow}</span>
                        <h2 id={`${idPrefix}-title`}>{title}</h2>
                        <p id={`${idPrefix}-description`}>{description}</p>
                    </div>
                    <IconButton
                        className="folder-editor-dialog__close"
                        label="Fechar edição de pasta"
                        icon={<X size={17} aria-hidden="true" />}
                        disabled={busy}
                        onClick={onCancel}
                    />
                </header>

                <form className="folder-editor-dialog__form" onSubmit={submit}>
                    <TextField
                        id={`${idPrefix}-name`}
                        label="Nome da pasta"
                        type="text"
                        placeholder={placeholder}
                        value={name}
                        disabled={busy}
                        maxLength={120}
                        autoComplete="off"
                        data-autofocus
                        onChange={(event) => onNameChange(event.target.value)}
                    />

                    {isCreate && (
                        <div className="ui-field folder-editor-dialog__destination-field">
                            <label htmlFor={`${idPrefix}-parent`}>Criar dentro de</label>
                            <PremiumSelect
                                id={`${idPrefix}-parent`}
                                value={parentId === null ? "root" : String(parentId)}
                                disabled={busy}
                                onChange={(event) => {
                                    onParentChange(
                                        event.target.value === "root"
                                            ? null
                                            : Number(event.target.value),
                                    );
                                }}
                            >
                                <option value="root">{rootLabel}</option>
                                {options.map((option) => (
                                    <option key={option.id} value={option.id}>
                                        {`${"— ".repeat(Math.min(option.depth + 1, 4))}${option.name}`}
                                    </option>
                                ))}
                            </PremiumSelect>
                            <span className="ui-field__hint">
                                Crie na raiz ou dentro de qualquer pasta existente.
                            </span>
                        </div>
                    )}

                    {isCreate && (
                        <div className="folder-editor-dialog__path-preview" aria-live="polite">
                            <span className="folder-editor-dialog__path-label">Destino</span>
                            <div className="folder-editor-dialog__path">
                                <Folder size={15} aria-hidden="true" />
                                <span>{rootLabel}</span>
                                {selectedDestination?.path.map((segment, index) => (
                                    <span className="folder-editor-dialog__path-segment" key={`${segment}-${index}`}>
                                        <ChevronRight size={14} aria-hidden="true" />
                                        <strong>{segment}</strong>
                                    </span>
                                ))}
                                {name.trim() && (
                                    <span className="folder-editor-dialog__path-segment is-new">
                                        <ChevronRight size={14} aria-hidden="true" />
                                        <strong>{name.trim()}</strong>
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    <footer className="folder-editor-dialog__actions ui-modal-footer">
                        <Button variant="ghost" onClick={onCancel} disabled={busy}>
                            Cancelar
                        </Button>
                        <Button
                            type="submit"
                            variant="primary"
                            busy={busy}
                            loadingLabel={isCreate ? "Criando pasta" : "Salvando nome"}
                            disabled={!name.trim()}
                        >
                            {isCreate
                                ? <Plus size={16} strokeWidth={2} aria-hidden="true" />
                                : <Save size={16} strokeWidth={1.8} aria-hidden="true" />}
                            {isCreate
                                ? isSubfolder ? "Criar subpasta" : "Criar pasta"
                                : "Salvar nome"}
                        </Button>
                    </footer>
                </form>
            </div>
        </div>,
        document.body,
    );
}
