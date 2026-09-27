// ============================================================
// DUET CORE - AGENTS - CARD
// ============================================================
//
// Card visual de um Device/Agent cadastrado.
//
// Responsabilidade:
// - apresentar identidade e status do Agent;
// - apresentar host, porta, usuário e diretório;
// - apresentar status da sessão Windows;
// - disponibilizar ações de download e exclusão.
//
// As operações são recebidas através de callbacks.
//
// Este componente NÃO:
// - chama endpoints;
// - exclui Agents diretamente;
// - executa download diretamente;
// - altera estado global;
// - determina regras de disponibilidade.
// ============================================================

// Estado local utilizado pelo editor de configuração do display.
import {
    useState,
} from "react";


// Ícones utilizados visualmente pelo card do Device.
import {
    Bot,
    Clock3,
    Download,
    FolderOpen,
    Monitor,
    Network,
    Settings2,
    Trash2,
    UserRound,
    Wrench,
} from "lucide-react";

import type {
    Agent,
    AgentEnvironment,
} from "../../types/agents";
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";
import { useInteraction } from "../../context/useInteraction";
import { Switch } from "../ui/Switch";
import { TextField } from "../ui/TextField";


// ============================================================
// PROPS
// ============================================================

interface AgentCardProps {
    agent: Agent;
    onEnvironmentChange:
        (
            agentId: string,
            environment: AgentEnvironment
        ) => void | Promise<void>;


    onDisplayChange:
        (
            agentId: string,
            width: number,
            height: number,
            scale: number
        ) => void | Promise<void>;
    availabilityBusy: boolean;
    onAvailabilityChange: (
        agentId: string,
        acceptingWork: boolean,
        reason: string | null,
    ) => Promise<boolean>;
    onDownload:
        (
            agentId: string
        ) => void | Promise<void>;

    onDelete:
        (
            agentId: string,
            agentName: string
        ) => void | Promise<void>;
}

const healthLabels: Record<Agent["health_state"], string> = {
    healthy: "Saudável",
    stale: "Heartbeat atrasado",
    offline: "Offline",
    never_seen: "Aguardando heartbeat",
};

function formatHeartbeatAge(ageSeconds: number | null) {
    if (ageSeconds === null) return "Nunca recebido";
    if (ageSeconds < 10) return "Agora";
    if (ageSeconds < 60) return `Há ${ageSeconds} s`;
    if (ageSeconds < 3600) return `Há ${Math.floor(ageSeconds / 60)} min`;
    return `Há ${Math.floor(ageSeconds / 3600)} h`;
}


// ============================================================
// COMPONENTE
// ============================================================
function AgentCard({
    agent,
    onEnvironmentChange,
    onDisplayChange,
    availabilityBusy,
    onAvailabilityChange,
    onDownload,
    onDelete,
}: AgentCardProps) {

    const { confirm } = useInteraction();

    const [editingAvailability, setEditingAvailability] = useState(false);
    const [maintenanceReason, setMaintenanceReason] = useState("");
    // Nome amigável apresentado ao usuário.
    const environmentLabel =
        agent.environment === "production"
            ? "Produção"
            : "Desenvolvimento / Homologação";

    // ========================================================
    // CONFIGURAÇÃO LOCAL DO DISPLAY
    // ========================================================
    //
    // O editor permanece fechado por padrão.
    //
    // Os valores iniciais sempre refletem a configuração
    // desejada atualmente persistida no Control Room.
    // ========================================================

    const [
        editingDisplay,
        setEditingDisplay,
    ] = useState(false);


    const [
        selectedResolution,
        setSelectedResolution,
    ] = useState(
        `${agent.display_width}x${agent.display_height}`
    );


    const [
        selectedScale,
        setSelectedScale,
    ] = useState(
        agent.display_scale
    );


    // Resolução realmente detectada no último heartbeat.
    const currentResolution =
        agent.display_current
            ? (
                `${agent.display_current.width}x` +
                `${agent.display_current.height}`
            )
            : "Não informada";


    // Configuração desejada atualmente persistida.
    const configuredResolution =
        `${agent.display_width}x${agent.display_height}`;

    const heartbeatLabel = agent.last_heartbeat
        ? new Date(agent.last_heartbeat).toLocaleString("pt-BR")
        : "Ainda não recebido";
    const heartbeatAgeLabel = formatHeartbeatAge(agent.heartbeat_age_seconds);
    const healthLabel = healthLabels[agent.health_state];

    return (
        <article className={`agent-card${agent.accepting_work ? "" : " agent-card--maintenance"}${agent.health_state === "healthy" ? "" : " agent-card--attention"}`}>

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="agent-card-header">

                <div className="agent-card-identity">

                    <div className="agent-avatar">

                        <Bot
                            size={20}
                            strokeWidth={1.7}
                        />

                    </div>


                    <div>

                        <h3>
                            {agent.name}
                        </h3>

                        <span className="agent-id">
                            {agent.agent_id}
                        </span>

                        <div
                            className={
                                agent.environment === "production"
                                    ? "agent-environment-badge agent-environment-production"
                                    : "agent-environment-badge agent-environment-development"
                            }
                        >
                            {environmentLabel}
                        </div>

                    </div>

                </div>


                <div
                    className={`agent-status agent-status-${agent.health_state}`}
                    title={agent.health_state === "healthy"
                        ? "Heartbeat dentro da janela operacional"
                        : "Verifique a conexão e o serviço do Agent"}
                >

                    <span className="status-dot"></span>

                    {healthLabel}

                </div>

            </div>

            <div className={`agent-availability${agent.accepting_work ? "" : " agent-availability--maintenance"}`}>
                <Switch
                    compact
                    checked={agent.accepting_work}
                    disabled={availabilityBusy}
                    label={agent.accepting_work ? "Novas reservas habilitadas" : "Device em manutenção"}
                    description={agent.accepting_work
                        ? agent.health_state === "healthy"
                            ? "O Device está apto para receber trabalho."
                            : "A fila aceita trabalho, mas o despacho aguarda a conexão normalizar."
                        : agent.maintenance_reason || "Novas reservas estão pausadas."}
                    onChange={async (event) => {
                        if (!event.target.checked) {
                            setMaintenanceReason("");
                            setEditingAvailability(true);
                            return;
                        }

                        const confirmed = await confirm({
                            title: "Liberar Device para novas execuções?",
                            description: `O Device "${agent.name}" voltará a aparecer nos seletores e poderá receber trabalho da fila.`,
                            confirmLabel: "Liberar Device",
                        });
                        if (confirmed) await onAvailabilityChange(agent.agent_id, true, null);
                    }}
                />
                {!agent.accepting_work && (
                    <span className="agent-maintenance-badge"><Wrench size={14} aria-hidden="true" /> Manutenção</span>
                )}
            </div>

            {editingAvailability && agent.accepting_work && (
                <div className="agent-maintenance-editor">
                    <TextField
                        label="Motivo da manutenção"
                        value={maintenanceReason}
                        maxLength={240}
                        placeholder="Ex.: atualização do Windows ou validação do ambiente"
                        description="O motivo ficará visível para quem administra e agenda automações."
                        onChange={(event) => setMaintenanceReason(event.target.value)}
                    />
                    <div className="agent-maintenance-editor__actions">
                        <Button size="sm" variant="ghost" onClick={() => setEditingAvailability(false)}>Cancelar</Button>
                        <Button
                            size="sm"
                            variant="primary"
                            busy={availabilityBusy}
                            loadingLabel="Pausando Device"
                            disabled={!maintenanceReason.trim()}
                            onClick={async () => {
                                const updated = await onAvailabilityChange(
                                    agent.agent_id,
                                    false,
                                    maintenanceReason.trim(),
                                );
                                if (updated) setEditingAvailability(false);
                            }}
                        >
                            <Wrench size={14} aria-hidden="true" /> Pausar novas execuções
                        </Button>
                    </div>
                </div>
            )}


            {/* ==================================================
                INFORMAÇÕES
                ================================================== */}

            <div className="agent-details">

                <div className="agent-detail">

                    <Monitor
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Host
                        </span>

                        <strong>
                            {agent.host || "-"}
                        </strong>

                    </div>

                </div>

                <div className="agent-detail">
                    <Clock3 size={15} strokeWidth={1.8} />
                    <div>
                        <span>Último heartbeat</span>
                        <strong title={heartbeatLabel}>{heartbeatAgeLabel}</strong>
                        <small>{heartbeatLabel}</small>
                    </div>
                </div>


                <div className="agent-detail">

                    <Network
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Porta
                        </span>

                        <strong>
                            {agent.port}
                        </strong>

                    </div>

                </div>


                <div className="agent-detail">

                    <UserRound
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Usuário da sessão
                        </span>

                        <strong>
                            {agent.username || "-"}
                        </strong>

                    </div>

                </div>


                <div className="agent-detail">

                    <FolderOpen
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Diretório dos robôs
                        </span>

                        <strong>
                            {agent.rpa_directory || "-"}
                        </strong>

                    </div>

                </div>


                {/* ==================================================
                    DISPLAY
                    ================================================== */}

                <div className="agent-detail">

                    <Monitor
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Resolução atual
                        </span>

                        <strong>
                            {currentResolution}
                        </strong>

                    </div>

                </div>


                <div className="agent-detail">

                    <Settings2
                        size={15}
                        strokeWidth={1.8}
                    />

                    <div>

                        <span>
                            Display configurado
                        </span>

                        <strong>
                            {configuredResolution}
                            {" · "}
                            {agent.display_scale}%
                        </strong>

                    </div>

                </div>

            </div>
            


            {/* ==================================================
                EDITOR DE DISPLAY
                ================================================== */}

            {editingDisplay && (

                <div className="agent-display-editor">

                    <div className="agent-display-field">

                        <label>
                            Resolução
                        </label>

                        <PremiumSelect
                            value={selectedResolution}
                            onChange={(event) => {
                                setSelectedResolution(
                                    event.target.value
                                );
                            }}
                        >

                            {agent.display_supported.map(
                                (resolution) => {

                                    const value =
                                        `${resolution.width}x${resolution.height}`;

                                    return (
                                        <option
                                            key={value}
                                            value={value}
                                        >
                                            {value}
                                        </option>
                                    );
                                }
                            )}

                        </PremiumSelect>

                    </div>


                    <div className="agent-display-field">

                        <label>
                            Escala
                        </label>

                        <PremiumSelect
                            value={selectedScale}
                            onChange={(event) => {
                                setSelectedScale(
                                    Number(
                                        event.target.value
                                    )
                                );
                            }}
                        >
                            <option value={100}>
                                100%
                            </option>

                            <option value={125}>
                                125%
                            </option>

                            <option value={150}>
                                150%
                            </option>

                            <option value={175}>
                                175%
                            </option>

                            <option value={200}>
                                200%
                            </option>
                        </PremiumSelect>

                    </div>


                    <div className="agent-display-editor-actions">

                        <Button
                            size="sm"
                            onClick={() => {
                                setEditingDisplay(false);
                            }}
                        >
                            Cancelar
                        </Button>


                        <Button
                            size="sm"
                            variant="primary"
                            disabled={
                                !selectedResolution
                            }
                            onClick={async () => {

                                const [
                                    width,
                                    height,
                                ] =
                                    selectedResolution
                                        .split("x")
                                        .map(Number);

                                if (
                                    width === undefined ||
                                    height === undefined ||
                                    !Number.isFinite(width) ||
                                    !Number.isFinite(height)
                                ) {
                                    return;
                                }


                                await onDisplayChange(
                                    agent.agent_id,
                                    width,
                                    height,
                                    selectedScale
                                );


                                setEditingDisplay(false);
                            }}
                        >
                            Salvar display
                        </Button>

                    </div>

                </div>

            )}

            {/* ==================================================
                RODAPÉ / AÇÕES
                ================================================== */}

            <div className="agent-card-footer">

                <div className="agent-session">

                    Sessão:{" "}

                    <strong>
                        {agent.session_status || "unknown"}
                    </strong>

                </div>


                <div className="agent-actions">

                    {/* ==================================================
                        ALTERAR AMBIENTE
                        ==================================================
                        Ação independente.

                        IMPORTANTE:
                        este botão não pode ficar dentro do botão de
                        download, pois isso provoca propagação do clique
                        e dispara as duas ações.
                        ================================================== */}

                    <Button
                        size="sm"
                        onClick={async () => {

                            const novoAmbiente:
                                AgentEnvironment =
                                    agent.environment === "production"
                                        ? "development"
                                        : "production";

                            const confirmar = await confirm({
                                title:
                                    novoAmbiente === "production"
                                        ? "Mover Device para Produção?"
                                        : "Mover Device para Desenvolvimento?",
                                description:
                                    novoAmbiente === "production"
                                        ? `“${agent.name}” ficará disponível para execuções no ambiente de Produção.`
                                        : `“${agent.name}” deixará o ambiente de Produção e voltará para Desenvolvimento / Homologação.`,
                                confirmLabel: "Confirmar ambiente",
                                tone:
                                    novoAmbiente === "production"
                                        ? "danger"
                                        : "default",
                            });

                            if (!confirmar) {
                                return;
                            }

                            onEnvironmentChange(
                                agent.agent_id,
                                novoAmbiente
                            );
                        }}
                    >
                        Alterar ambiente
                    </Button>
                    


                    {/* ==================================================
                        ALTERAR DISPLAY
                        ================================================== */}

                    <Button
                        size="sm"
                        onClick={() => {

                            // Sempre reabre o editor usando os valores
                            // atualmente persistidos no Control Room.
                            setSelectedResolution(
                                `${agent.display_width}x${agent.display_height}`
                            );

                            setSelectedScale(
                                agent.display_scale
                            );

                            setEditingDisplay(
                                (atual) => !atual
                            );
                        }}
                    >

                        <Settings2
                            size={15}
                            strokeWidth={1.8}
                        />

                        Alterar display

                    </Button>

                    {/* ==================================================
                        DOWNLOAD
                        ================================================== */}

                    <Button
                        size="sm"
                        onClick={() => {
                            onDownload(
                                agent.agent_id
                            );
                        }}
                    >

                        <Download
                            size={15}
                            strokeWidth={1.8}
                        />

                        Baixar

                    </Button>


                    {/* ==================================================
                        EXCLUSÃO
                        ================================================== */}

                    <Button
                        size="sm"
                        variant="danger"
                        onClick={() => {
                            onDelete(
                                agent.agent_id,
                                agent.name
                            );
                        }}
                    >

                        <Trash2
                            size={15}
                            strokeWidth={1.8}
                        />

                        Excluir

                    </Button>

                </div>

            </div>

        </article>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentCard;
