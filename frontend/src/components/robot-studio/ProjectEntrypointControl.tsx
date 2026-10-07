// ============================================================
// DUET CORE - ROBOT STUDIO - ENTRYPOINT CONTROL
// ============================================================
// Componente puramente visual. Usa somente tokens já existentes
// do Studio; não cria paleta própria.
// ============================================================

import type {
    ProjectEntrypointState,
} from "../../services/projectEntrypointApi";

interface ProjectEntrypointControlProps {
    state: ProjectEntrypointState | null;
    pythonFiles: string[];
    loading: boolean;
    saving: boolean;
    canWrite: boolean;
    onChange: (
        path: string
    ) => void | Promise<void>;
}

export default function ProjectEntrypointControl({
    state,
    pythonFiles,
    loading,
    saving,
    canWrite,
    onChange,
}: ProjectEntrypointControlProps) {
    const path =
        state?.entrypoint_path || "main.py";

    const missing = Boolean(
        state &&
        (!state.valid || !state.exists)
    );

    const hasCurrentOption =
        pythonFiles.includes(path);

    return (
        <label
            title={
                missing
                    ? "O arquivo de entrada configurado não existe. Selecione outro .py antes de executar ou publicar."
                    : "Arquivo Python usado na execução oficial do projeto"
            }
            style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                minWidth: 0,
                color: missing
                    ? "var(--studio-warning)"
                    : "var(--studio-text-secondary)",
                fontSize: 12,
            }}
        >
            <span
                style={{
                    whiteSpace: "nowrap",
                }}
            >
                Entrada
            </span>

            <select
                value={path}
                disabled={
                    loading ||
                    saving ||
                    !canWrite
                }
                onChange={(event) => {
                    void onChange(
                        event.target.value
                    );
                }}
                style={{
                    minWidth: 150,
                    maxWidth: 300,
                    height: 30,
                    padding: "0 28px 0 9px",
                    border: "1px solid var(--studio-border)",
                    borderRadius: 7,
                    background: "var(--studio-surface-raised)",
                    color: "var(--studio-text)",
                    fontSize: 12,
                    outline: "none",
                    cursor:
                        loading ||
                        saving ||
                        !canWrite
                            ? "not-allowed"
                            : "pointer",
                    opacity:
                        loading || saving
                            ? 0.65
                            : 1,
                    textOverflow: "ellipsis",
                }}
                aria-label="Arquivo de entrada do projeto"
            >
                {!hasCurrentOption && (
                    <option value={path}>
                        {path}
                        {missing
                            ? " (não encontrado)"
                            : ""}
                    </option>
                )}

                {pythonFiles.map((file) => (
                    <option
                        key={file}
                        value={file}
                    >
                        {file}
                    </option>
                ))}
            </select>
        </label>
    );
}
