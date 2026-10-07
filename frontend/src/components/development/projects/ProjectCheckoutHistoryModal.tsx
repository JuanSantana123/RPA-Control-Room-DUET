import { createPortal } from "react-dom";
import { History, LockKeyhole, ShieldAlert, LockKeyholeOpen, X } from "lucide-react";

import type { DevelopmentProject } from "../../../types/development";
import type { ProjectCheckoutHistoryEvent } from "../../../hooks/development/useProjectCheckoutHistory";

interface ProjectCheckoutHistoryModalProps {
    project: DevelopmentProject | null;
    events: ProjectCheckoutHistoryEvent[];
    loading: boolean;
    error: string;
    onClose: () => void;
}

const formatDateTime = (value: string | null): string => {
    if (!value) {
        return "Data não informada";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString("pt-BR");
};

const eventPresentation = (
    event: ProjectCheckoutHistoryEvent
) => {
    if (event.event_type === "checkout") {
        return {
            label: "Checkout",
            icon: <LockKeyhole size={16} strokeWidth={1.8} />,
            description: `${event.actor_user_name} reservou o projeto para edição.`,
        };
    }

    if (event.event_type === "checkin") {
        return {
            label: "Check-in",
            icon: <LockKeyholeOpen size={16} strokeWidth={1.8} />,
            description: `${event.actor_user_name} liberou o projeto.`,
        };
    }

    const owner = event.checkout_owner_user_name;
    return {
        label: "Force Release",
        icon: <ShieldAlert size={16} strokeWidth={1.8} />,
        description:
            event.actor_user_name === owner
                ? `${event.actor_user_name} forçou a liberação do Checkout.`
                : `${event.actor_user_name} liberou administrativamente o Checkout de ${owner}.`,
    };
};

function ProjectCheckoutHistoryModal({
    project,
    events,
    loading,
    error,
    onClose,
}: ProjectCheckoutHistoryModalProps) {
    if (!project) {
        return null;
    }

    return createPortal(
        <div
            className="execution-modal-overlay ui-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
        >
            <div
                className="execution-modal ui-modal-surface"
                role="dialog"
                aria-modal="true"
                aria-labelledby="checkout-history-title"
                style={{
                    width: "min(720px, calc(100vw - 32px))",
                    maxHeight: "min(760px, calc(100vh - 48px))",
                    overflow: "hidden",
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <header className="execution-modal-header ui-modal-header">
                    <div>
                        <span className="page-eyebrow">
                            RASTREABILIDADE
                        </span>
                        <h2 id="checkout-history-title">
                            Histórico de Checkout
                        </h2>
                        <p>
                            {project.name}
                        </p>
                    </div>

                    <button
                        type="button"
                        className="icon-button"
                        onClick={onClose}
                        title="Fechar histórico"
                        aria-label="Fechar histórico de Checkout"
                    >
                        <X size={18} strokeWidth={1.8} />
                    </button>
                </header>

                <div
                    className="execution-modal-body"
                    style={{
                        overflowY: "auto",
                        display: "grid",
                        gap: 10,
                    }}
                >
                    {loading && (
                        <div className="panel-empty-state">
                            Carregando histórico...
                        </div>
                    )}

                    {!loading && error && (
                        <div className="alert alert-error">
                            {error}
                        </div>
                    )}

                    {!loading && !error && events.length === 0 && (
                        <div className="panel-empty-state">
                            <History size={22} strokeWidth={1.7} />
                            <p>
                                Nenhum evento de Checkout foi registrado ainda.
                            </p>
                        </div>
                    )}

                    {!loading && !error && events.map((event) => {
                        const presentation = eventPresentation(event);

                        return (
                            <article
                                key={event.id}
                                style={{
                                    display: "grid",
                                    gridTemplateColumns: "32px minmax(0, 1fr)",
                                    gap: 10,
                                    padding: 12,
                                    border: "1px solid var(--border-color)",
                                    borderRadius: "var(--radius-md, 10px)",
                                    background: "var(--surface-1)",
                                }}
                            >
                                <div
                                    style={{
                                        display: "grid",
                                        placeItems: "center",
                                        alignSelf: "start",
                                        minHeight: 32,
                                    }}
                                >
                                    {presentation.icon}
                                </div>

                                <div style={{ minWidth: 0 }}>
                                    <strong>
                                        {presentation.label}
                                    </strong>
                                    <p style={{ margin: "4px 0" }}>
                                        {presentation.description}
                                    </p>
                                    <small>
                                        {formatDateTime(event.occurred_at)}
                                    </small>
                                </div>
                            </article>
                        );
                    })}
                </div>
            </div>
        </div>,
        document.body
    );
}

export default ProjectCheckoutHistoryModal;
