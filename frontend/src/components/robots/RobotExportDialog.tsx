// ============================================================
// DUET CORE - ROBOTS - EXPORT DIALOG
// ============================================================
//
// Responsabilidade:
// - permitir selecionar um Robot publicado da localização atual;
// - permitir selecionar uma versão imutável desse Robot;
// - confirmar a exportação do ZIP.
//
// Toda regra de carregamento e download permanece fora do
// componente, no hook useRobotExport.
// ============================================================

import {
    Download,
    FileArchive,
    Package,
    ShieldCheck,
    X,
} from "lucide-react";

import {
    createPortal,
} from "react-dom";

import {
    useDialogFocus,
} from "../../hooks/ui/useDialogFocus";

import type {
    Robot,
    RobotReleaseVersion,
} from "../../types/robots";

import {
    Button,
    IconButton,
} from "../ui/Button";

import EmptyState from "../ui/EmptyState";
import FeedbackBanner from "../ui/FeedbackBanner";
import PremiumSelect from "../ui/PremiumSelect";
import { PanelSkeleton } from "../ui/Skeletons";


interface RobotExportDialogProps {
    robots: Robot[];
    selectedRobot: Robot | null;
    versions: RobotReleaseVersion[];
    selectedVersion: RobotReleaseVersion | null;
    loadingVersions: boolean;
    exporting: boolean;
    error: string;
    onClose: () => void;
    onRobotChange: (robot: Robot | null) => void | Promise<void>;
    onVersionChange: (versionNumber: number) => void;
    onExport: () => void | Promise<void>;
}


function shortHash(value: string): string {
    return value.length > 20
        ? `${value.slice(0, 10)}…${value.slice(-8)}`
        : value;
}


export default function RobotExportDialog({
    robots,
    selectedRobot,
    versions,
    selectedVersion,
    loadingVersions,
    exporting,
    error,
    onClose,
    onRobotChange,
    onVersionChange,
    onExport,
}: RobotExportDialogProps) {
    const dialogRef = useDialogFocus<HTMLDivElement>({
        open: true,
        onClose,
        closeOnEscape: !exporting,
    });

    return createPortal(
        <div
            className="robot-export-overlay ui-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget && !exporting) {
                    onClose();
                }
            }}
        >
            <div
                ref={dialogRef}
                className="robot-export-dialog ui-modal-surface"
                role="dialog"
                aria-modal="true"
                aria-labelledby="robot-export-title"
                aria-describedby="robot-export-description"
                tabIndex={-1}
            >
                <header className="robot-export-header ui-modal-header">
                    <div className="robot-export-heading">
                        <span className="robot-export-heading__icon" aria-hidden="true">
                            <Download size={20} strokeWidth={1.8} />
                        </span>

                        <div>
                            <span className="page-eyebrow">EXPORTAR PACOTE</span>
                            <h2 id="robot-export-title">Exportar robô publicado</h2>
                            <p id="robot-export-description">
                                Escolha o robô e a versão exata que será salva como arquivo ZIP.
                            </p>
                        </div>
                    </div>

                    <IconButton
                        data-autofocus
                        label="Fechar exportação"
                        icon={<X size={18} aria-hidden="true" />}
                        disabled={exporting}
                        onClick={onClose}
                    />
                </header>

                <div className="robot-export-body">
                    {error && (
                        <FeedbackBanner
                            tone="error"
                            title="Não foi possível concluir a exportação"
                            message={error}
                            hint="Nenhum release foi alterado. Revise a seleção e tente novamente."
                        />
                    )}

                    {robots.length === 0 ? (
                        <EmptyState
                            icon={<Package />}
                            title="Nenhum robô nesta localização"
                            description="Selecione uma pasta que possua robôs publicados antes de exportar um pacote."
                        />
                    ) : (
                        <>
                            <div className="robot-export-form">
                                <div className="form-field">
                                    <label htmlFor="robot-export-robot">Robô publicado</label>
                                    <PremiumSelect
                                        id="robot-export-robot"
                                        value={selectedRobot ? String(selectedRobot.id) : ""}
                                        placeholder="Selecione um robô"
                                        disabled={exporting}
                                        onChange={(event) => {
                                            const robotId = Number(event.target.value);
                                            const robot = robots.find((item) => item.id === robotId) ?? null;
                                            void onRobotChange(robot);
                                        }}
                                    >
                                        <option value="" disabled>Selecione um robô</option>
                                        {robots.map((robot) => (
                                            <option key={robot.id} value={String(robot.id)}>
                                                {robot.name} · v{robot.version}
                                            </option>
                                        ))}
                                    </PremiumSelect>
                                </div>

                                <div className="form-field">
                                    <label htmlFor="robot-export-version">Versão publicada</label>
                                    <PremiumSelect
                                        id="robot-export-version"
                                        value={selectedVersion ? String(selectedVersion.version) : ""}
                                        placeholder={loadingVersions ? "Carregando versões..." : "Selecione uma versão"}
                                        disabled={!selectedRobot || loadingVersions || exporting || versions.length === 0}
                                        onChange={(event) => {
                                            onVersionChange(Number(event.target.value));
                                        }}
                                    >
                                        <option value="" disabled>
                                            {loadingVersions ? "Carregando versões..." : "Selecione uma versão"}
                                        </option>
                                        {versions.map((version) => (
                                            <option key={version.id} value={String(version.version)}>
                                                v{version.version}{version.is_current ? " · Vigente" : ""}
                                            </option>
                                        ))}
                                    </PremiumSelect>
                                </div>
                            </div>

                            {loadingVersions ? (
                                <div className="robot-export-loading">
                                    <PanelSkeleton lines={3} />
                                </div>
                            ) : selectedRobot && versions.length === 0 && !error ? (
                                <EmptyState
                                    icon={<FileArchive />}
                                    title="Nenhuma versão disponível"
                                    description="Este robô não possui um snapshot publicado disponível para exportação."
                                />
                            ) : selectedRobot && selectedVersion ? (
                                <section className="robot-export-preview" aria-label="Resumo da exportação">
                                    <div>
                                        <FileArchive size={16} aria-hidden="true" />
                                        <span>Pacote</span>
                                        <strong title={selectedVersion.filename}>{selectedVersion.filename}</strong>
                                    </div>

                                    <div>
                                        <Package size={16} aria-hidden="true" />
                                        <span>Versão</span>
                                        <strong>
                                            v{selectedVersion.version}
                                            {selectedVersion.is_current ? " · Vigente" : ""}
                                        </strong>
                                    </div>

                                    <div>
                                        <ShieldCheck size={16} aria-hidden="true" />
                                        <span>Integridade</span>
                                        <strong title={selectedVersion.file_hash}>
                                            SHA-256 {shortHash(selectedVersion.file_hash)}
                                        </strong>
                                    </div>
                                </section>
                            ) : null}
                        </>
                    )}
                </div>

                <footer className="robot-export-footer ui-modal-footer">
                    <p>
                        <ShieldCheck size={15} aria-hidden="true" />
                        O DUET exporta o snapshot publicado, sem reconstruir o pacote.
                    </p>

                    <div className="robot-export-footer__actions">
                        <Button
                            variant="secondary"
                            disabled={exporting}
                            onClick={onClose}
                        >
                            Cancelar
                        </Button>

                        <Button
                            variant="primary"
                            busy={exporting}
                            loadingLabel="Exportando pacote"
                            disabled={!selectedRobot || !selectedVersion || loadingVersions}
                            onClick={() => void onExport()}
                        >
                            <Download size={15} strokeWidth={1.9} aria-hidden="true" />
                            Exportar .zip
                        </Button>
                    </div>
                </footer>
            </div>
        </div>,
        document.body,
    );
}
