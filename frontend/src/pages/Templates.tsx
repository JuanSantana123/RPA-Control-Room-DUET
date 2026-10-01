// ============================================================
// DUET CORE - TEMPLATES PAGE
// ============================================================
//
// Administração dos Templates versionados utilizados como base
// para novos AutomationProjects.
//
// Conceito:
//     Template = origem inicial do projeto.
//
// Uma nova versão do Template NÃO atualiza projetos existentes.
// Cada versão permanece imutável e pode ser baixada ou novamente
// definida como a versão atual.
// ============================================================

import {
    useMemo,
    useState,
} from "react";

import {
    Check,
    ChevronDown,
    ChevronUp,
    Download,
    FileArchive,
    Pencil,
    Plus,
    Upload,
    X,
} from "lucide-react";

import {
    Button,
} from "../components/ui/Button";

import {
    useAuth,
} from "../context/useAuth";

import {
    useTemplatesAdmin,
} from "../hooks/templates/useTemplatesAdmin";

import type {
    AutomationTemplate,
} from "../types/development";

import "../styles/templates.css";


// ============================================================
// PÁGINA
// ============================================================

function Templates() {
    const { can } = useAuth();

    // O backend desta V1 reutiliza as permissões de Development.
    // Portanto a interface aplica exatamente o mesmo contrato.
    const canCreate = can("Development:create");
    const canEdit = can("Development:edit");

    const {
        templates,
        loading,
        busyAction,
        error,
        success,
        clearFeedback,
        createTemplate,
        publishVersion,
        saveMetadata,
        setTemplateActive,
        setCurrentVersion,
        downloadVersion,
    } = useTemplatesAdmin();


    // ========================================================
    // CRIAÇÃO
    // ========================================================

    const [showCreate, setShowCreate] =
        useState(false);

    const [createName, setCreateName] =
        useState("");

    const [createDescription, setCreateDescription] =
        useState("");

    const [createFile, setCreateFile] =
        useState<File | null>(null);

    const [createFileKey, setCreateFileKey] =
        useState(0);


    // ========================================================
    // PAINÉIS POR TEMPLATE
    // ========================================================

    const [expandedTemplateId, setExpandedTemplateId] =
        useState<number | null>(null);

    const [editingTemplateId, setEditingTemplateId] =
        useState<number | null>(null);

    const [editName, setEditName] =
        useState("");

    const [editDescription, setEditDescription] =
        useState("");

    const [versionTemplateId, setVersionTemplateId] =
        useState<number | null>(null);

    const [versionFile, setVersionFile] =
        useState<File | null>(null);

    const [versionFileKey, setVersionFileKey] =
        useState(0);


    // ========================================================
    // RESUMO
    // ========================================================

    const summary = useMemo(() => {
        const active =
            templates.filter(
                (template) => template.is_active
            ).length;

        const totalVersions =
            templates.reduce(
                (total, template) =>
                    total + template.versions.length,
                0,
            );

        return {
            total: templates.length,
            active,
            inactive:
                templates.length - active,
            totalVersions,
        };
    }, [templates]);


    // ========================================================
    // AÇÕES DE FORMULÁRIO
    // ========================================================

    const closeCreate = () => {
        if (busyAction === "create") {
            return;
        }

        setShowCreate(false);
        setCreateName("");
        setCreateDescription("");
        setCreateFile(null);
        setCreateFileKey((value) => value + 1);
    };


    const handleCreate = async () => {
        if (
            !createName.trim() ||
            !createFile ||
            busyAction === "create"
        ) {
            return;
        }

        const created =
            await createTemplate(
                createName,
                createDescription,
                createFile,
            );

        if (created) {
            closeCreate();
        }
    };


    const startEdit = (
        template: AutomationTemplate,
    ) => {
        clearFeedback();
        setVersionTemplateId(null);
        setVersionFile(null);

        setEditingTemplateId(template.id);
        setEditName(template.name);
        setEditDescription(
            template.description || ""
        );
    };


    const cancelEdit = () => {
        setEditingTemplateId(null);
        setEditName("");
        setEditDescription("");
    };


    const handleSaveMetadata = async (
        templateId: number,
    ) => {
        if (!editName.trim()) {
            return;
        }

        const saved =
            await saveMetadata(
                templateId,
                editName,
                editDescription,
            );

        if (saved) {
            cancelEdit();
        }
    };


    const startNewVersion = (
        templateId: number,
    ) => {
        clearFeedback();
        cancelEdit();

        setVersionTemplateId(templateId);
        setVersionFile(null);
        setVersionFileKey((value) => value + 1);
    };


    const cancelNewVersion = () => {
        setVersionTemplateId(null);
        setVersionFile(null);
        setVersionFileKey((value) => value + 1);
    };


    const handlePublishVersion = async (
        templateId: number,
    ) => {
        if (!versionFile) {
            return;
        }

        const published =
            await publishVersion(
                templateId,
                versionFile,
            );

        if (published) {
            cancelNewVersion();
            setExpandedTemplateId(templateId);
        }
    };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="templates-page">
            <header className="templates-header">
                <div>
                    <span className="templates-header__eyebrow">
                        Administração
                    </span>

                    <h1>Templates</h1>

                    <p>
                        Gerencie projetos-base versionados para iniciar novas automações com uma estrutura pronta.
                    </p>
                </div>

                {canCreate && (
                    <Button
                        variant="primary"
                        type="button"
                        onClick={() => {
                            clearFeedback();
                            setShowCreate(true);
                        }}
                    >
                        <Plus size={16} aria-hidden="true" />
                        Novo Template
                    </Button>
                )}
            </header>


            {/* ==================================================
                FEEDBACK
                ================================================== */}

            {error && (
                <div className="templates-feedback templates-feedback--error" role="alert">
                    <strong>Não foi possível concluir a operação.</strong>
                    <span>{error}</span>
                </div>
            )}

            {success && (
                <div className="templates-feedback templates-feedback--success" role="status">
                    <Check size={17} aria-hidden="true" />
                    <span>{success}</span>
                </div>
            )}


            {/* ==================================================
                CRIAR TEMPLATE
                ================================================== */}

            {showCreate && canCreate && (
                <section className="templates-editor-card">
                    <div className="templates-editor-card__header">
                        <div>
                            <span>Novo Template</span>
                            <strong>Publique a primeira versão</strong>
                        </div>

                        <button
                            className="templates-icon-button"
                            type="button"
                            aria-label="Fechar criação de Template"
                            disabled={busyAction === "create"}
                            onClick={closeCreate}
                        >
                            <X size={18} aria-hidden="true" />
                        </button>
                    </div>

                    <div className="templates-form-grid">
                        <label className="templates-field">
                            <span>Nome</span>
                            <input
                                type="text"
                                value={createName}
                                disabled={busyAction === "create"}
                                placeholder="Ex.: Template Padrão DUET"
                                onChange={(event) =>
                                    setCreateName(event.target.value)
                                }
                            />
                        </label>

                        <label className="templates-field templates-field--wide">
                            <span>Descrição</span>
                            <textarea
                                value={createDescription}
                                disabled={busyAction === "create"}
                                rows={3}
                                placeholder="Descreva quando este Template deve ser utilizado."
                                onChange={(event) =>
                                    setCreateDescription(event.target.value)
                                }
                            />
                        </label>

                        <label className="templates-file-field templates-field--wide">
                            <span>Projeto-base (.zip)</span>

                            <input
                                key={createFileKey}
                                type="file"
                                accept=".zip,application/zip"
                                disabled={busyAction === "create"}
                                onChange={(event) =>
                                    setCreateFile(
                                        event.target.files?.[0] || null
                                    )
                                }
                            />

                            <small>
                                O ZIP precisa representar o projeto completo e conter main.py na raiz lógica.
                            </small>
                        </label>
                    </div>

                    <div className="templates-editor-actions">
                        <Button
                            variant="secondary"
                            type="button"
                            disabled={busyAction === "create"}
                            onClick={closeCreate}
                        >
                            Cancelar
                        </Button>

                        <Button
                            variant="primary"
                            type="button"
                            busy={busyAction === "create"}
                            loadingLabel="Criando Template"
                            disabled={
                                !createName.trim() ||
                                !createFile ||
                                busyAction === "create"
                            }
                            onClick={() => void handleCreate()}
                        >
                            <Upload size={16} aria-hidden="true" />
                            Criar Template
                        </Button>
                    </div>
                </section>
            )}


            {/* ==================================================
                RESUMO
                ================================================== */}

            <section className="templates-summary" aria-label="Resumo de Templates">
                <article>
                    <span>Templates</span>
                    <strong>{summary.total}</strong>
                    <small>cadastrados</small>
                </article>

                <article>
                    <span>Ativos</span>
                    <strong>{summary.active}</strong>
                    <small>disponíveis para novos projetos</small>
                </article>

                <article>
                    <span>Inativos</span>
                    <strong>{summary.inactive}</strong>
                    <small>preservados no histórico</small>
                </article>

                <article>
                    <span>Versões</span>
                    <strong>{summary.totalVersions}</strong>
                    <small>snapshots imutáveis</small>
                </article>
            </section>


            {/* ==================================================
                CATÁLOGO
                ================================================== */}

            <section className="templates-catalog">
                <div className="templates-catalog__heading">
                    <div>
                        <h2>Catálogo de Templates</h2>
                        <p>
                            A versão marcada como Atual é selecionada automaticamente na criação de uma nova automação.
                        </p>
                    </div>
                </div>

                {loading ? (
                    <div className="templates-empty-state">
                        <FileArchive size={28} aria-hidden="true" />
                        <strong>Carregando Templates...</strong>
                    </div>
                ) : templates.length === 0 ? (
                    <div className="templates-empty-state">
                        <FileArchive size={30} aria-hidden="true" />
                        <strong>Nenhum Template cadastrado</strong>
                        <span>
                            Publique um ZIP para disponibilizar uma base pronta aos novos projetos.
                        </span>
                    </div>
                ) : (
                    <div className="templates-list">
                        {templates.map((template) => {
                            const expanded =
                                expandedTemplateId === template.id;

                            const editing =
                                editingTemplateId === template.id;

                            const publishing =
                                versionTemplateId === template.id;

                            const currentVersion =
                                template.versions.find(
                                    (version) => version.is_current
                                ) || null;

                            return (
                                <article
                                    className={`template-card${
                                        template.is_active
                                            ? ""
                                            : " template-card--inactive"
                                    }`}
                                    key={template.id}
                                >
                                    <div className="template-card__main">
                                        <div className="template-card__identity">
                                            <div className="template-card__icon">
                                                <FileArchive size={20} aria-hidden="true" />
                                            </div>

                                            <div>
                                                <div className="template-card__title-row">
                                                    <h3>{template.name}</h3>

                                                    <span
                                                        className={`template-status${
                                                            template.is_active
                                                                ? " template-status--active"
                                                                : " template-status--inactive"
                                                        }`}
                                                    >
                                                        {template.is_active
                                                            ? "Ativo"
                                                            : "Inativo"}
                                                    </span>
                                                </div>

                                                <p>
                                                    {template.description ||
                                                        "Sem descrição cadastrada."}
                                                </p>
                                            </div>
                                        </div>

                                        <div className="template-card__version-summary">
                                            <span>Versão atual</span>
                                            <strong>
                                                {currentVersion
                                                    ? `v${currentVersion.version}`
                                                    : "—"}
                                            </strong>
                                            <small>
                                                {template.versions.length} versão(ões)
                                            </small>
                                        </div>
                                    </div>

                                    <div className="template-card__actions">
                                        <Button
                                            variant="secondary"
                                            type="button"
                                            onClick={() =>
                                                setExpandedTemplateId(
                                                    expanded
                                                        ? null
                                                        : template.id
                                                )
                                            }
                                        >
                                            {expanded ? (
                                                <ChevronUp size={15} aria-hidden="true" />
                                            ) : (
                                                <ChevronDown size={15} aria-hidden="true" />
                                            )}
                                            Histórico
                                        </Button>

                                        {canEdit && (
                                            <>
                                                <Button
                                                    variant="secondary"
                                                    type="button"
                                                    disabled={busyAction !== null}
                                                    onClick={() =>
                                                        startEdit(template)
                                                    }
                                                >
                                                    <Pencil size={15} aria-hidden="true" />
                                                    Editar
                                                </Button>

                                                <Button
                                                    variant="secondary"
                                                    type="button"
                                                    disabled={busyAction !== null}
                                                    onClick={() =>
                                                        startNewVersion(template.id)
                                                    }
                                                >
                                                    <Upload size={15} aria-hidden="true" />
                                                    Nova versão
                                                </Button>

                                                <Button
                                                    variant="secondary"
                                                    type="button"
                                                    busy={
                                                        busyAction ===
                                                        `active:${template.id}`
                                                    }
                                                    disabled={
                                                        busyAction !== null &&
                                                        busyAction !==
                                                            `active:${template.id}`
                                                    }
                                                    onClick={() =>
                                                        void setTemplateActive(
                                                            template.id,
                                                            !template.is_active,
                                                        )
                                                    }
                                                >
                                                    {template.is_active
                                                        ? "Desativar"
                                                        : "Reativar"}
                                                </Button>
                                            </>
                                        )}
                                    </div>


                                    {/* ==========================================
                                        EDIÇÃO DE METADADOS
                                        ========================================== */}

                                    {editing && canEdit && (
                                        <div className="template-inline-editor">
                                            <div className="templates-form-grid">
                                                <label className="templates-field">
                                                    <span>Nome</span>
                                                    <input
                                                        type="text"
                                                        value={editName}
                                                        disabled={
                                                            busyAction ===
                                                            `metadata:${template.id}`
                                                        }
                                                        onChange={(event) =>
                                                            setEditName(event.target.value)
                                                        }
                                                    />
                                                </label>

                                                <label className="templates-field templates-field--wide">
                                                    <span>Descrição</span>
                                                    <textarea
                                                        rows={3}
                                                        value={editDescription}
                                                        disabled={
                                                            busyAction ===
                                                            `metadata:${template.id}`
                                                        }
                                                        onChange={(event) =>
                                                            setEditDescription(event.target.value)
                                                        }
                                                    />
                                                </label>
                                            </div>

                                            <div className="templates-editor-actions">
                                                <Button
                                                    variant="secondary"
                                                    type="button"
                                                    disabled={
                                                        busyAction ===
                                                        `metadata:${template.id}`
                                                    }
                                                    onClick={cancelEdit}
                                                >
                                                    Cancelar
                                                </Button>

                                                <Button
                                                    variant="primary"
                                                    type="button"
                                                    busy={
                                                        busyAction ===
                                                        `metadata:${template.id}`
                                                    }
                                                    loadingLabel="Salvando"
                                                    disabled={!editName.trim()}
                                                    onClick={() =>
                                                        void handleSaveMetadata(
                                                            template.id
                                                        )
                                                    }
                                                >
                                                    <Check size={15} aria-hidden="true" />
                                                    Salvar
                                                </Button>
                                            </div>
                                        </div>
                                    )}


                                    {/* ==========================================
                                        NOVA VERSÃO
                                        ========================================== */}

                                    {publishing && canEdit && (
                                        <div className="template-inline-editor">
                                            <div className="template-version-upload-copy">
                                                <strong>
                                                    Publicar nova versão de {template.name}
                                                </strong>
                                                <span>
                                                    O próximo número será gerado automaticamente e esta versão passará a ser a Atual.
                                                </span>
                                            </div>

                                            <label className="templates-file-field">
                                                <span>Novo projeto-base (.zip)</span>
                                                <input
                                                    key={versionFileKey}
                                                    type="file"
                                                    accept=".zip,application/zip"
                                                    disabled={
                                                        busyAction ===
                                                        `publish:${template.id}`
                                                    }
                                                    onChange={(event) =>
                                                        setVersionFile(
                                                            event.target.files?.[0] || null
                                                        )
                                                    }
                                                />
                                            </label>

                                            <div className="templates-editor-actions">
                                                <Button
                                                    variant="secondary"
                                                    type="button"
                                                    disabled={
                                                        busyAction ===
                                                        `publish:${template.id}`
                                                    }
                                                    onClick={cancelNewVersion}
                                                >
                                                    Cancelar
                                                </Button>

                                                <Button
                                                    variant="primary"
                                                    type="button"
                                                    busy={
                                                        busyAction ===
                                                        `publish:${template.id}`
                                                    }
                                                    loadingLabel="Publicando"
                                                    disabled={!versionFile}
                                                    onClick={() =>
                                                        void handlePublishVersion(
                                                            template.id
                                                        )
                                                    }
                                                >
                                                    <Upload size={15} aria-hidden="true" />
                                                    Publicar versão
                                                </Button>
                                            </div>
                                        </div>
                                    )}


                                    {/* ==========================================
                                        HISTÓRICO DE VERSÕES
                                        ========================================== */}

                                    {expanded && (
                                        <div className="template-version-history">
                                            <div className="template-version-history__heading">
                                                <strong>Histórico de versões</strong>
                                                <span>
                                                    Versões anteriores permanecem imutáveis.
                                                </span>
                                            </div>

                                            <div className="template-version-list">
                                                {template.versions.map((version) => (
                                                    <div
                                                        className={`template-version-row${
                                                            version.is_current
                                                                ? " template-version-row--current"
                                                                : ""
                                                        }`}
                                                        key={version.id}
                                                    >
                                                        <div className="template-version-row__identity">
                                                            <span className="template-version-number">
                                                                v{version.version}
                                                            </span>

                                                            <div>
                                                                <strong>
                                                                    {version.filename}
                                                                </strong>
                                                                <small>
                                                                    {version.published_at
                                                                        ? new Date(
                                                                            version.published_at
                                                                        ).toLocaleString("pt-BR")
                                                                        : "Data não disponível"}
                                                                </small>
                                                            </div>
                                                        </div>

                                                        <div className="template-version-row__actions">
                                                            {version.is_current && (
                                                                <span className="template-current-badge">
                                                                    Atual
                                                                </span>
                                                            )}

                                                            <Button
                                                                variant="secondary"
                                                                type="button"
                                                                busy={
                                                                    busyAction ===
                                                                    `download:${template.id}:${version.id}`
                                                                }
                                                                disabled={
                                                                    busyAction !== null &&
                                                                    busyAction !==
                                                                        `download:${template.id}:${version.id}`
                                                                }
                                                                onClick={() =>
                                                                    void downloadVersion(
                                                                        template,
                                                                        version,
                                                                    )
                                                                }
                                                            >
                                                                <Download size={14} aria-hidden="true" />
                                                                Baixar
                                                            </Button>

                                                            {canEdit && !version.is_current && (
                                                                <Button
                                                                    variant="secondary"
                                                                    type="button"
                                                                    busy={
                                                                        busyAction ===
                                                                        `current:${template.id}:${version.id}`
                                                                    }
                                                                    disabled={busyAction !== null}
                                                                    onClick={() =>
                                                                        void setCurrentVersion(
                                                                            template.id,
                                                                            version.id,
                                                                        )
                                                                    }
                                                                >
                                                                    Definir como atual
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </article>
                            );
                        })}
                    </div>
                )}
            </section>
        </div>
    );
}

export default Templates;
