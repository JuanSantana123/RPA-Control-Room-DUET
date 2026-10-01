import {
    Boxes,
    Check,
    ChevronDown,
    ChevronUp,
    Download,
    FileArchive,
    GitBranch,
    History,
    RotateCw,
    ShieldCheck,
    UserRound,
    X,
} from "lucide-react";
import { createPortal } from "react-dom";

import { useDialogFocus } from "../../hooks/ui/useDialogFocus";
import type {
    Robot,
    RobotLibraryDependency,
    RobotReleaseVersion,
} from "../../types/robots";
import { parseApiDateTime } from "../../utils/dateTime";
import { Button, IconButton } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import FeedbackBanner from "../ui/FeedbackBanner";
import { PanelSkeleton } from "../ui/Skeletons";
import RobotLibrariesSnapshot from "./RobotLibrariesSnapshot";


interface RobotVersionsDialogProps {
    robot: Robot;
    versions: RobotReleaseVersion[];
    loading: boolean;
    error: string;
    downloadingVersion: number | null;
    expandedVersion: number | null;
    loadingLibraries: number | null;
    librariesByVersion: Record<number, RobotLibraryDependency[]>;
    onClose: () => void;
    onRetry?: () => void;
    onDownload: (version: RobotReleaseVersion) => void | Promise<void>;
    onToggleLibraries: (version: RobotReleaseVersion) => void | Promise<void>;
}


function formatDate(value: string | null) {
    const parsed = parseApiDateTime(value);
    return parsed
        ? new Intl.DateTimeFormat("pt-BR", {
            dateStyle: "medium",
            timeStyle: "short",
        }).format(parsed)
        : "Data original não registrada";
}


function shortHash(value: string) {
    return value.length > 18
        ? `${value.slice(0, 10)}…${value.slice(-8)}`
        : value;
}


export default function RobotVersionsDialog({
    robot,
    versions,
    loading,
    error,
    downloadingVersion,
    expandedVersion,
    loadingLibraries,
    librariesByVersion,
    onClose,
    onRetry,
    onDownload,
    onToggleLibraries,
}: RobotVersionsDialogProps) {
    const busy = downloadingVersion !== null;
    const dialogRef = useDialogFocus<HTMLDivElement>({
        open: true,
        onClose,
        closeOnEscape: !busy,
    });

    return createPortal(
        <div
            className="robot-versions-overlay ui-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget && !busy) onClose();
            }}
        >
            <div
                ref={dialogRef}
                className="robot-versions-dialog ui-modal-surface"
                role="dialog"
                aria-modal="true"
                aria-labelledby="robot-versions-title"
                aria-describedby="robot-versions-description"
                tabIndex={-1}
            >
                <header className="robot-versions-header ui-modal-header">
                    <div className="robot-versions-heading">
                        <span className="robot-versions-heading__icon" aria-hidden="true">
                            <History size={20} />
                        </span>
                        <div>
                            <span className="page-eyebrow">CENTRAL DE VERSÕES</span>
                            <h2 id="robot-versions-title">{robot.name}</h2>
                            <p id="robot-versions-description">
                                Consulte a proveniência e exporte snapshots imutáveis já publicados.
                            </p>
                        </div>
                    </div>
                    <IconButton
                        data-autofocus
                        label="Fechar histórico de versões"
                        icon={<X size={18} aria-hidden="true" />}
                        disabled={busy}
                        onClick={onClose}
                    />
                </header>

                <div className="robot-versions-summary" aria-label="Resumo do robô">
                    <div>
                        <FileArchive size={16} aria-hidden="true" />
                        <span>Pacote atual</span>
                        <strong title={robot.filename}>{robot.filename}</strong>
                    </div>
                    <div>
                        <ShieldCheck size={16} aria-hidden="true" />
                        <span>Release vigente</span>
                        <strong>v{robot.version}</strong>
                    </div>
                    <div>
                        <GitBranch size={16} aria-hidden="true" />
                        <span>Histórico</span>
                        <strong>{loading ? "…" : `${versions.length} ${versions.length === 1 ? "versão" : "versões"}`}</strong>
                    </div>
                </div>

                <div className="robot-versions-body">
                    {error && (
                        <FeedbackBanner
                            tone="error"
                            title="Não foi possível concluir a consulta"
                            message={error}
                            hint="Os releases existentes não foram alterados. Tente novamente ou valide o artefato com a equipe responsável."
                            action={onRetry ? { label: "Tentar novamente", onClick: onRetry } : undefined}
                        />
                    )}

                    {loading ? (
                        <PanelSkeleton lines={4} />
                    ) : versions.length === 0 && !error ? (
                        <EmptyState
                            icon={<History />}
                            title="Nenhum release registrado"
                            description="Este robô não possui snapshots no catálogo de versões. Pacotes legados podem precisar de reconciliação administrativa."
                        />
                    ) : (
                        <ol className="robot-version-timeline">
                            {versions.map((version) => {
                                const expanded = expandedVersion === version.version;
                                const libraries = librariesByVersion[version.version] ?? [];
                                const publisher = version.publisher?.name || version.publisher?.username || "Autor não identificado";

                                return (
                                    <li
                                        key={version.id}
                                        className={`robot-version-item${version.is_current ? " robot-version-item--current" : ""}`}
                                    >
                                        <span className="robot-version-rail" aria-hidden="true">
                                            {version.is_current ? <Check size={13} /> : null}
                                        </span>
                                        <div className="robot-version-card">
                                            <div className="robot-version-card__top">
                                                <div className="robot-version-identity">
                                                    <span className="robot-version-number">v{version.version}</span>
                                                    {version.is_current && <span className="robot-version-current">Vigente</span>}
                                                </div>
                                                <time dateTime={version.published_at || version.created_at}>
                                                    {formatDate(version.published_at || version.created_at)}
                                                </time>
                                            </div>

                                            <div className="robot-version-metadata">
                                                <span><UserRound size={14} aria-hidden="true" />{publisher}</span>
                                                <span><GitBranch size={14} aria-hidden="true" />{version.source_project?.name || "Publicação direta"}</span>
                                                <span title={version.file_hash}><ShieldCheck size={14} aria-hidden="true" />SHA-256 {shortHash(version.file_hash)}</span>
                                            </div>

                                            <div className="robot-version-actions">
                                                <Button
                                                    size="sm"
                                                    variant="ghost"
                                                    onClick={() => void onToggleLibraries(version)}
                                                    aria-expanded={expanded}
                                                >
                                                    <Boxes size={15} aria-hidden="true" />
                                                    Bibliotecas
                                                    {expanded ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant={version.is_current ? "primary" : "secondary"}
                                                    busy={downloadingVersion === version.version}
                                                    loadingLabel={`Validando e exportando versão ${version.version}`}
                                                    disabled={busy && downloadingVersion !== version.version}
                                                    onClick={() => void onDownload(version)}
                                                >
                                                    <Download size={15} aria-hidden="true" />
                                                    Exportar v{version.version}
                                                </Button>
                                            </div>

                                            {expanded && (
                                                <RobotLibrariesSnapshot
                                                    libraries={libraries}
                                                    loading={loadingLibraries === version.version}
                                                />
                                            )}
                                        </div>
                                    </li>
                                );
                            })}
                        </ol>
                    )}
                </div>

                <footer className="robot-versions-footer ui-modal-footer">
                    <p>
                        <ShieldCheck size={15} aria-hidden="true" />
                        O servidor valida o SHA-256 antes de disponibilizar qualquer pacote.
                    </p>
                    <Button variant="secondary" onClick={onClose} disabled={busy}>Fechar</Button>
                    {error && onRetry && (
                        <Button onClick={onRetry} disabled={loading}>
                            <RotateCw size={15} aria-hidden="true" /> Atualizar
                        </Button>
                    )}
                </footer>
            </div>
        </div>,
        document.body,
    );
}
