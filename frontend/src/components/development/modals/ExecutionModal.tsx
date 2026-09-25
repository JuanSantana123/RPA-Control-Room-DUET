// ============================================================
// EXECUTION MODAL
// ============================================================
//
// Responsabilidade:
//     Renderiza o modal utilizado para executar um projeto da
//     área de Desenvolvimento em um Agent do DUET CORE.
//
// O modal apresenta:
//     - projeto que será executado;
//     - Agents disponíveis;
//     - estado de disponibilidade do Agent;
//     - mensagens de erro;
//     - ação de cancelar;
//     - ação de executar.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// Ele NÃO deve:
//     - consultar Agents diretamente;
//     - chamar endpoints HTTP;
//     - montar snapshots;
//     - iniciar execuções;
//     - alterar estado global da página.
//
// Toda a lógica de execução continua pertencendo ao
// Development.tsx nesta etapa.
//
// Development.tsx:
//     - carrega os Agents;
//     - controla o Agent selecionado;
//     - executa o POST;
//     - controla loading e mensagens;
//
// ExecutionModal.tsx:
//     - recebe esses dados via props;
//     - apresenta a interface;
//     - encaminha as ações ao componente pai.
//
// Objetivo:
//     Remover o JSX do modal de execução de Development.tsx
//     sem alterar nenhuma regra funcional existente.
// ============================================================

import {
    createPortal,
} from "react-dom";


import {
    Play,
} from "lucide-react";


import type {
    DevelopmentProject,
    ExecutionAgent,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface ExecutionModalProps {

    // Projeto que será executado.
    //
    // null:
    //     modal fechado.
    project:
        DevelopmentProject | null;


    // Permissão efetiva do usuário para executar projetos.
    canExecute:
        boolean;


    // Agents retornados pelo backend.
    agents:
        ExecutionAgent[];


    // Agent atualmente selecionado.
    selectedAgentId:
        string;


    // Indica que os Agents ainda estão sendo consultados.
    loadingAgents:
        boolean;


    // ID do projeto atualmente sendo enviado para execução.
    //
    // null:
    //     nenhuma execução em andamento.
    executingProjectId:
        number | null;


    // Mensagem de erro apresentada dentro do modal.
    error:
        string;


    // ========================================================
    // CALLBACKS
    // ========================================================

    // Alteração do Agent selecionado.
    onAgentChange:
        (agentId: string) => void;


    // Fecha o modal.
    onClose:
        () => void;


    // Solicita a execução ao Development.tsx.
    onExecute:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionModal({
    project,
    canExecute,

    agents,
    selectedAgentId,

    loadingAgents,
    executingProjectId,

    error,

    onAgentChange,
    onClose,
    onExecute,
}: ExecutionModalProps) {

    // ========================================================
    // MODAL FECHADO / SEM PERMISSÃO
    // ========================================================

    if (
        !project ||
        !canExecute
    ) {
        return null;
    }

    // ========================================================
    // DISPONIBILIDADE DOS AGENTS
    // ========================================================
    //
    // Para iniciar uma execução, o Agent precisa estar ONLINE.
    //
    // A sessão Windows não precisa estar previamente "ready":
    //
    // - ready:
    //      a execução pode seguir diretamente;
    //
    // - not_ready:
    //      o backend tentará preparar/desbloquear a sessão
    //      automaticamente usando a credencial Windows vinculada
    //      ao dispositivo.
    //
    // Portanto, o frontend não deve impedir a seleção de um
    // Agent apenas porque a sessão Windows está bloqueada.
    // ========================================================

    const hasOnlineAgent =
        agents.some(
            (agent) =>
                agent.status === "online"
        );


    // ========================================================
    // INTERFACE
    // ========================================================

    return createPortal(

        <div
            role="presentation"

            onMouseDown={() => {
                onClose();
            }}

            style={{
                position:
                    "fixed",

                inset:
                    0,

                zIndex:
                    10000,

                display:
                    "flex",

                alignItems:
                    "center",

                justifyContent:
                    "center",

                padding:
                    20,

                background:
                    "rgba(15, 23, 42, 0.48)",

                boxSizing:
                    "border-box",
            }}
        >

            <div
                role="dialog"

                aria-modal="true"

                aria-labelledby="development-execution-title"

                onMouseDown={(event) => {
                    event.stopPropagation();
                }}

                style={{
                    width:
                        "100%",

                    maxWidth:
                        520,

                    padding:
                        22,

                    border:
                        "1px solid var(--border-color, #dfe3ea)",

                    borderRadius:
                        12,

                    background:
                        "var(--surface-color, #ffffff)",

                    boxShadow:
                        "0 24px 70px rgba(15, 23, 42, 0.28)",

                    boxSizing:
                        "border-box",
                }}
            >

                {/* =================================================
                    CABEÇALHO
                ================================================= */}

                <div>

                    <div
                        style={{
                            fontSize:
                                11,

                            fontWeight:
                                800,

                            letterSpacing:
                                "0.08em",

                            opacity:
                                0.58,
                        }}
                    >
                        EXECUÇÃO DE DESENVOLVIMENTO
                    </div>


                    <h2
                        id="development-execution-title"

                        style={{
                            margin:
                                "6px 0 0",

                            fontSize:
                                20,
                        }}
                    >
                        Executar projeto
                    </h2>

                </div>


                {/* =================================================
                    PROJETO
                ================================================= */}

                <div
                    style={{
                        marginTop:
                            18,

                        padding:
                            14,

                        border:
                            "1px solid var(--border-color, #dfe3ea)",

                        borderRadius:
                            8,

                        background:
                            "var(--surface-hover, rgba(100, 116, 139, 0.06))",
                    }}
                >

                    <strong
                        style={{
                            display:
                                "block",

                            marginBottom:
                                6,

                            fontSize:
                                13,
                        }}
                    >
                        {project.name}
                    </strong>


                    <p
                        style={{
                            margin:
                                0,

                            fontSize:
                                12,

                            lineHeight:
                                1.55,

                            opacity:
                                0.76,
                        }}
                    >
                        O DUET CORE montará um snapshot do workspace,
                        incluirá as versões fixadas das Libraries e
                        enviará o pacote para o Agent selecionado.
                    </p>

                </div>


                {/* =================================================
                    AGENT
                ================================================= */}

                <div
                    className="form-field"

                    style={{
                        marginTop:
                            18,
                    }}
                >

                    <label
                        htmlFor="development-execution-agent"
                    >
                        Agent
                    </label>


                    <select
                        id="development-execution-agent"

                        value={
                            selectedAgentId
                        }

                        disabled={
                            loadingAgents ||
                            executingProjectId !== null
                        }

                        onChange={(event) => {

                            onAgentChange(
                                event.target.value
                            );
                        }}
                    >

                        <option value="">

                            {loadingAgents
                                ? "Carregando Agents..."
                                : "Selecione um Agent"}

                        </option>


                        {agents.map(
                            (agent) => {

                                // ====================================================
                                // ESTADO DO AGENT PARA SELEÇÃO
                                // ====================================================
                                //
                                // ONLINE:
                                //     pode ser escolhido para execução.
                                //
                                // READY:
                                //     já possui sessão Windows utilizável.
                                //
                                // ONLINE + NOT_READY:
                                //     continua selecionável porque o Control Room
                                //     realizará a autenticação automática antes de
                                //     iniciar o robô.
                                // ====================================================

                                const online =
                                    agent.status === "online";

                                const ready =
                                    online &&
                                    agent.session_status === "ready";


                                return (

                                    <option
                                        key={
                                            agent.agent_id
                                        }

                                        value={
                                            agent.agent_id
                                        }

                                        // Somente Agents realmente offline ficam
                                        // indisponíveis no seletor.
                                        disabled={
                                            !online
                                        }
                                    >

                                        {agent.name}
                                        {" — "}
                                        {agent.agent_id}

                                        {ready
                                            ? " — pronto"
                                            : online
                                                ? " — sessão será preparada automaticamente"
                                                : ` — ${agent.status}`}

                                    </option>
                                );
                            }
                        )}

                    </select>

                </div>


                {/* =================================================
                    NENHUM AGENT PRONTO
                ================================================= */}

                {!loadingAgents &&
                    agents.length > 0 &&
                    !hasOnlineAgent && (

                    <div
                        className="alert alert-error"

                        style={{
                            marginTop:
                                14,

                            marginBottom:
                                0,
                        }}
                    >
                        Nenhum Agent está online.
                    </div>
                )}


                {/* =================================================
                    ERRO
                ================================================= */}

                {error && (

                    <div
                        className="alert alert-error"

                        style={{
                            marginTop:
                                14,

                            marginBottom:
                                0,
                        }}
                    >
                        {error}
                    </div>
                )}


                {/* =================================================
                    AÇÕES
                ================================================= */}

                <div
                    style={{
                        display:
                            "flex",

                        justifyContent:
                            "flex-end",

                        gap:
                            8,

                        marginTop:
                            20,
                    }}
                >

                    <button
                        type="button"

                        className="secondary-button"

                        disabled={
                            executingProjectId !== null
                        }

                        onClick={
                            onClose
                        }
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"

                        className="primary-button"

                        disabled={
                            !selectedAgentId ||
                            loadingAgents ||
                            executingProjectId !== null
                        }

                        onClick={
                            onExecute
                        }
                    >

                        <Play
                            size={15}
                            strokeWidth={1.9}
                        />


                        {executingProjectId ===
                            project.id
                            ? "Executando..."
                            : "Executar"}

                    </button>

                </div>

            </div>

        </div>,

        document.body
    );
}


export default ExecutionModal;