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
    Download,
    FolderOpen,
    Monitor,
    Network,
    Settings2,
    Trash2,
    UserRound,
} from "lucide-react";

import type {
    Agent,
    AgentEnvironment,
} from "../../types/agents";


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


// ============================================================
// COMPONENTE
// ============================================================
function AgentCard({
    agent,
    onEnvironmentChange,
    onDisplayChange,
    onDownload,
    onDelete,
}: AgentCardProps) {

    // Mantém exatamente a regra visual existente:
    // somente status "online", ignorando maiúsculas/minúsculas,
    // recebe a classe visual de Agent online.
    const isOnline =
        agent.status?.toLowerCase() ===
        "online";
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

    return (
        <article className="agent-card">

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
                    className={
                        isOnline
                            ? "agent-status agent-status-online"
                            : "agent-status agent-status-offline"
                    }
                >

                    <span className="status-dot"></span>

                    {agent.status || "Offline"}

                </div>

            </div>


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

                        <select
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

                        </select>

                    </div>


                    <div className="agent-display-field">

                        <label>
                            Escala
                        </label>

                        <select
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
                        </select>

                    </div>


                    <div className="agent-display-editor-actions">

                        <button
                            type="button"
                            className="secondary-button"
                            onClick={() => {
                                setEditingDisplay(false);
                            }}
                        >
                            Cancelar
                        </button>


                        <button
                            type="button"
                            className="primary-button"
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
                        </button>

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

                    <button
                        type="button"
                        className="secondary-button"
                        onClick={() => {

                            const novoAmbiente:
                                AgentEnvironment =
                                    agent.environment === "production"
                                        ? "development"
                                        : "production";

                            const confirmar =
                                window.confirm(
                                    novoAmbiente === "production"
                                        ? (
                                            `Deseja classificar "${agent.name}" ` +
                                            "como Device de Produção?"
                                        )
                                        : (
                                            `Deseja classificar "${agent.name}" ` +
                                            "como Device de Desenvolvimento / Homologação?"
                                        )
                                );

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
                    </button>
                    


                    {/* ==================================================
                        ALTERAR DISPLAY
                        ================================================== */}

                    <button
                        type="button"
                        className="secondary-button"
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

                    </button>

                    {/* ==================================================
                        DOWNLOAD
                        ================================================== */}

                    <button
                        type="button"
                        className="secondary-button"
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

                    </button>


                    {/* ==================================================
                        EXCLUSÃO
                        ================================================== */}

                    <button
                        type="button"
                        className="danger-button"
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

                    </button>

                </div>

            </div>

        </article>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentCard;