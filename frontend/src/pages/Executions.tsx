import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

/**
 * ============================================================
 * INTERFACE DA EXECUÇÃO
 * ============================================================
 *
 * Representa exatamente os dados que o Control Room devolve
 * pelo endpoint GET /executions.
 */
interface Execution {
    id: number;
    robot_id: number;
    robot_name: string;
    filename: string;
    agent_id: string;
    agent_name: string;
    pid: number | null;
    status: string;
    started_at: string | null;
    finished_at: string | null;
    error_message: string | null;
}

/**
 * ============================================================
 * CALCULA DURAÇÃO
 * ============================================================
 *
 * Mantém a mesma lógica do executions.html:
 *
 * 1h 20m 35s
 * 20m 35s
 * 35s
 *
 * Se a execução ainda estiver rodando, utiliza a hora atual.
 */
function calcularDuracao(
    inicio: string | null,
    fim: string | null
): string {
    if (!inicio) {
        return "-";
    }

    const dataInicio = new Date(inicio);
    const dataFim = fim ? new Date(fim) : new Date();

    const diferenca = Math.floor(
        (dataFim.getTime() - dataInicio.getTime()) / 1000
    );

    if (diferenca < 0) {
        return "-";
    }

    const horas = Math.floor(diferenca / 3600);

    const minutos = Math.floor(
        (diferenca % 3600) / 60
    );

    const segundos = diferenca % 60;

    if (horas > 0) {
        return `${horas}h ${minutos}m ${segundos}s`;
    }

    if (minutos > 0) {
        return `${minutos}m ${segundos}s`;
    }

    return `${segundos}s`;
}

/**
 * ============================================================
 * FORMATA DATA
 * ============================================================
 */
function formatarData(data: string | null): string {
    if (!data) {
        return "-";
    }

    return new Date(data).toLocaleString("pt-BR");
}

/**
 * ============================================================
 * CONVERTE STATUS PARA TEXTO
 * ============================================================
 */
function formatarStatus(status: string): string {
    switch (status) {
        case "success":
            return "● Sucesso";

        case "error":
            return "● Erro";

        case "stopped":
            return "● Parado";

        case "running":
            return "● Executando";

        default:
            return `● ${status || "Desconhecido"}`;
    }
}

/**
 * ============================================================
 * ESTILO DO STATUS
 * ============================================================
 */
function estiloStatus(status: string): React.CSSProperties {
    switch (status) {
        case "success":
            return {
                color: "#16a34a",
                fontWeight: 600,
            };

        case "error":
        case "stopped":
            return {
                color: "#dc2626",
                fontWeight: 600,
            };

        case "running":
            return {
                fontWeight: 600,
            };

        default:
            return {
                fontWeight: 600,
            };
    }
}

/**
 * ============================================================
 * PÁGINA DE EXECUÇÕES
 * ============================================================
 */
function Executions() {

    /**
     * Todas as execuções recebidas da API.
     */
    const [executions, setExecutions] = useState<Execution[]>([]);

    /**
     * Filtros selecionados.
     */
    const [filtroRobo, setFiltroRobo] = useState("");
    const [filtroAgent, setFiltroAgent] = useState("");

    /**
     * Execução atualmente selecionada no modal.
     */
    const [execucaoSelecionada, setExecucaoSelecionada] =
        useState<Execution | null>(null);

    /**
     * Controle de carregamento.
     */
    const [loading, setLoading] = useState(true);

    /**
     * Mensagem de erro da API.
     */
    const [error, setError] = useState("");

    /**
     * Guarda qual execução está sendo parada.
     *
     * Isso evita clicar várias vezes no botão enquanto
     * a requisição ainda está sendo processada.
     */
    const [parandoExecucao, setParandoExecucao] =
        useState<number | null>(null);

    /**
     * ============================================================
     * CARREGA EXECUÇÕES
     * ============================================================
     *
     * Equivale à função carregarExecucoes() do HTML antigo.
     */
    const carregarExecucoes = async () => {

        try {

            const response = await api.get("/executions");

            /**
             * O backend retorna:
             *
             * {
             *     status: "success",
             *     executions: [...]
             * }
             */
            setExecutions(
                response.data.executions ?? []
            );

            setError("");

        } catch (err) {

            console.error(
                "Erro ao carregar execuções:",
                err
            );

            setError(
                "Não foi possível carregar as execuções."
            );

        } finally {

            setLoading(false);
        }
    };

    /**
     * ============================================================
     * PRIMEIRA CARGA + ATUALIZAÇÃO AUTOMÁTICA
     * ============================================================
     *
     * O executions.html fazia:
     *
     * setInterval(carregarExecucoes, 5000)
     *
     * Aqui fazemos a mesma coisa, mas também limpamos o
     * intervalo quando o componente é desmontado.
     */
    useEffect(() => {

        carregarExecucoes();

        const intervalo = window.setInterval(
            carregarExecucoes,
            5000
        );

        return () => {
            window.clearInterval(intervalo);
        };

    }, []);

    /**
     * ============================================================
     * LISTA DE ROBÔS PARA O FILTRO
     * ============================================================
     *
     * Equivale ao popularFiltros() do HTML.
     */
    const robos = useMemo(() => {

        return Array.from(
            new Set(
                executions
                    .map((execution) => execution.robot_name)
                    .filter(Boolean)
            )
        );

    }, [executions]);

    /**
     * ============================================================
     * LISTA DE AGENTS PARA O FILTRO
     * ============================================================
     */
    const agents = useMemo(() => {

        return Array.from(
            new Set(
                executions
                    .map((execution) => execution.agent_name)
                    .filter(Boolean)
            )
        );

    }, [executions]);

    /**
     * ============================================================
     * APLICA FILTROS
     * ============================================================
     *
     * Mantém a mesma regra do HTML:
     *
     * - sem robô selecionado = todos
     * - sem Agent selecionado = todos
     * - os dois selecionados = precisa atender aos dois
     */
    const execucoesFiltradas = useMemo(() => {

        return executions.filter((execution) => {

            const correspondeRobo =
                !filtroRobo ||
                execution.robot_name === filtroRobo;

            const correspondeAgent =
                !filtroAgent ||
                execution.agent_name === filtroAgent;

            return (
                correspondeRobo &&
                correspondeAgent
            );
        });

    }, [
        executions,
        filtroRobo,
        filtroAgent
    ]);

    /**
     * ============================================================
     * LIMPA FILTROS
     * ============================================================
     */
    const limparFiltros = () => {

        setFiltroRobo("");
        setFiltroAgent("");
    };

    /**
     * ============================================================
     * ABRE MODAL DE DETALHES
     * ============================================================
     */
    const abrirDetalhes = (execution: Execution) => {

        setExecucaoSelecionada(execution);
    };

    /**
     * ============================================================
     * FECHA MODAL
     * ============================================================
     */
    const fecharDetalhes = () => {

        setExecucaoSelecionada(null);
    };

    /**
     * ============================================================
     * PARA EXECUÇÃO
     * ============================================================
     *
     * IMPORTANTE:
     *
     * O endpoint atual do Control Room é:
     *
     * POST /agents/{agent_id}/execution/stop
     *
     * Portanto NÃO vamos inventar outro endpoint.
     */
    const pararExecucao = async (
        executionId: number,
        agentId: string
    ) => {

        const confirmar = window.confirm(
            `Deseja realmente parar a execução #${executionId}?`
        );

        if (!confirmar) {
            return;
        }

        try {

            setParandoExecucao(executionId);

            const response = await api.post(
                `/agents/${agentId}/execution/stop`
            );

            const data = response.data;

            if (
                response.status < 200 ||
                response.status >= 300 ||
                data.status !== "success"
            ) {

                console.error(
                    "Erro ao parar execução:",
                    data
                );

                window.alert(
                    data.message ||
                    data.error ||
                    JSON.stringify(data) ||
                    "Não foi possível parar a execução."
                );

                return;
            }

            window.alert(
                "Comando de parada enviado para o Agent."
            );

            /**
             * Atualiza a tabela imediatamente depois
             * de enviar o comando de parada.
             */
            await carregarExecucoes();

        } catch (err) {

            console.error(
                "Erro ao enviar comando de stop:",
                err
            );

            window.alert(
                "Não foi possível comunicar com o Control Room."
            );

        } finally {

            setParandoExecucao(null);
        }
    };

    return (
        <section
            style={{
                padding: "24px",
            }}
        >

            {/* ======================================================
                CABEÇALHO
            ====================================================== */}

            <div
                style={{
                    marginBottom: "24px",
                }}
            >
                <h2
                    style={{
                        margin: 0,
                    }}
                >
                    Execuções
                </h2>

                <p
                    style={{
                        marginTop: "5px",
                        color: "#6b7280",
                    }}
                >
                    Execuções em andamento
                </p>
            </div>


            {/* ======================================================
                FILTROS
            ====================================================== */}

            <div
                style={{
                    display: "flex",
                    alignItems: "end",
                    gap: "16px",
                    marginBottom: "24px",
                    flexWrap: "wrap",
                }}
            >

                {/* FILTRO ROBÔ */}

                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "6px",
                    }}
                >

                    <label htmlFor="filtro-robo">
                        Robô
                    </label>

                    <select
                        id="filtro-robo"
                        value={filtroRobo}
                        onChange={(event) =>
                            setFiltroRobo(event.target.value)
                        }
                        style={{
                            minWidth: "180px",
                            padding: "8px",
                        }}
                    >

                        <option value="">
                            Todos
                        </option>

                        {robos.map((robo) => (
                            <option
                                key={robo}
                                value={robo}
                            >
                                {robo}
                            </option>
                        ))}

                    </select>

                </div>


                {/* FILTRO AGENT */}

                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "6px",
                    }}
                >

                    <label htmlFor="filtro-agent">
                        Agent
                    </label>

                    <select
                        id="filtro-agent"
                        value={filtroAgent}
                        onChange={(event) =>
                            setFiltroAgent(event.target.value)
                        }
                        style={{
                            minWidth: "180px",
                            padding: "8px",
                        }}
                    >

                        <option value="">
                            Todos
                        </option>

                        {agents.map((agent) => (
                            <option
                                key={agent}
                                value={agent}
                            >
                                {agent}
                            </option>
                        ))}

                    </select>

                </div>


                {/* BOTÃO FILTRAR */}

                <button
                    type="button"
                    onClick={() => {
                        /**
                         * Os filtros já são aplicados automaticamente
                         * pelo useMemo.
                         *
                         * O botão existe para manter a mesma experiência
                         * da tela antiga.
                         */
                    }}
                    style={{
                        padding: "9px 16px",
                        cursor: "pointer",
                    }}
                >
                    🔍 Filtrar
                </button>


                {/* BOTÃO LIMPAR */}

                <button
                    type="button"
                    onClick={limparFiltros}
                    style={{
                        padding: "9px 16px",
                        cursor: "pointer",
                    }}
                >
                    Limpar
                </button>

            </div>


            {/* ======================================================
                MENSAGEM DE ERRO
            ====================================================== */}

            {error && (
                <div
                    style={{
                        padding: "12px",
                        marginBottom: "16px",
                        border: "1px solid #fca5a5",
                        borderRadius: "8px",
                    }}
                >
                    {error}
                </div>
            )}


            {/* ======================================================
                TABELA
            ====================================================== */}

            <div
                style={{
                    width: "100%",
                    overflowX: "auto",
                }}
            >

                <table
                    style={{
                        width: "100%",
                        borderCollapse: "collapse",
                    }}
                >

                    <thead>

                        <tr>

                            <th style={thStyle}>
                                ID
                            </th>

                            <th style={thStyle}>
                                Robô
                            </th>

                            <th style={thStyle}>
                                Agent
                            </th>

                            <th style={thStyle}>
                                PID
                            </th>

                            <th style={thStyle}>
                                Início
                            </th>

                            <th style={thStyle}>
                                Fim
                            </th>

                            <th style={thStyle}>
                                Duração
                            </th>

                            <th style={thStyle}>
                                Status
                            </th>

                            <th style={thStyle}>
                                Erro
                            </th>

                            <th style={thStyle}>
                                Ações
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        {loading ? (

                            <tr>

                                <td
                                    colSpan={10}
                                    style={tdStyle}
                                >
                                    Carregando execuções...
                                </td>

                            </tr>

                        ) : execucoesFiltradas.length === 0 ? (

                            <tr>

                                <td
                                    colSpan={10}
                                    style={tdStyle}
                                >
                                    Nenhuma execução encontrada.
                                </td>

                            </tr>

                        ) : (

                            execucoesFiltradas.map(
                                (execution) => (

                                    <tr key={execution.id}>

                                        <td style={tdStyle}>
                                            {execution.id}
                                        </td>

                                        <td style={tdStyle}>
                                            {execution.robot_name}
                                        </td>

                                        <td style={tdStyle}>
                                            {execution.agent_name}
                                        </td>

                                        <td style={tdStyle}>
                                            {execution.pid ?? "-"}
                                        </td>

                                        <td style={tdStyle}>
                                            {formatarData(
                                                execution.started_at
                                            )}
                                        </td>

                                        <td style={tdStyle}>
                                            {formatarData(
                                                execution.finished_at
                                            )}
                                        </td>

                                        <td style={tdStyle}>
                                            {calcularDuracao(
                                                execution.started_at,
                                                execution.finished_at
                                            )}
                                        </td>

                                        <td
                                            style={{
                                                ...tdStyle,
                                                ...estiloStatus(
                                                    execution.status
                                                ),
                                            }}
                                        >
                                            {formatarStatus(
                                                execution.status
                                            )}
                                        </td>

                                        <td
                                            style={{
                                                ...tdStyle,
                                                maxWidth: "300px",
                                                wordBreak: "break-word",
                                            }}
                                        >
                                            {execution.error_message || "-"}
                                        </td>

                                        <td style={tdStyle}>

                                            <button
                                                type="button"
                                                onClick={() =>
                                                    abrirDetalhes(
                                                        execution
                                                    )
                                                }
                                                style={{
                                                    padding: "6px 10px",
                                                    cursor: "pointer",
                                                }}
                                            >
                                                Detalhes
                                            </button>


                                            {execution.status === "running" && (

                                                <button
                                                    type="button"
                                                    disabled={
                                                        parandoExecucao ===
                                                        execution.id
                                                    }
                                                    onClick={() =>
                                                        pararExecucao(
                                                            execution.id,
                                                            execution.agent_id
                                                        )
                                                    }
                                                    style={{
                                                        marginLeft: "6px",
                                                        padding: "6px 10px",
                                                        cursor:
                                                            parandoExecucao ===
                                                            execution.id
                                                                ? "default"
                                                                : "pointer",
                                                    }}
                                                >

                                                    {parandoExecucao ===
                                                    execution.id
                                                        ? "Parando..."
                                                        : "⏹ Parar"}

                                                </button>

                                            )}

                                        </td>

                                    </tr>

                                )
                            )

                        )}

                    </tbody>

                </table>

            </div>


            {/* ======================================================
                MODAL DE DETALHES
            ====================================================== */}

            {execucaoSelecionada && (

                <div
                    onClick={fecharDetalhes}
                    style={{
                        position: "fixed",
                        inset: 0,
                        width: "100vw",
                        height: "100vh",
                        zIndex: 99999,
                        background: "rgba(0, 0, 0, 0.6)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        padding: "20px",
                        boxSizing: "border-box",
                    }}
                >

                    <div
                        onClick={(event) =>
                            event.stopPropagation()
                        }
                        style={{
                            position: "relative",
                            width: "650px",
                            maxWidth: "90vw",
                            maxHeight: "90vh",
                            background: "white",
                            borderRadius: "12px",
                            overflow: "hidden",
                            boxShadow:
                                "0 20px 50px rgba(0, 0, 0, 0.30)",
                        }}
                    >

                        {/* CABEÇALHO DO MODAL */}

                        <div
                            style={{
                                padding: "20px 24px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                borderBottom:
                                    "1px solid #e5e7eb",
                            }}
                        >

                            <div>

                                <h2
                                    style={{
                                        margin: 0,
                                    }}
                                >
                                    Execução #
                                    {execucaoSelecionada.id}
                                </h2>

                                <p
                                    style={{
                                        margin: "5px 0 0",
                                        color: "#6b7280",
                                    }}
                                >
                                    Detalhes da execução
                                </p>

                            </div>

                            <button
                                type="button"
                                onClick={fecharDetalhes}
                                style={{
                                    border: "none",
                                    background: "transparent",
                                    fontSize: "20px",
                                    cursor: "pointer",
                                }}
                            >
                                ✕
                            </button>

                        </div>


                        {/* CORPO DO MODAL */}

                        <div
                            style={{
                                maxHeight:
                                    "calc(90vh - 90px)",
                                overflowY: "auto",
                                padding: "24px",
                                boxSizing: "border-box",
                            }}
                        >

                            {/* INFORMAÇÕES PRINCIPAIS */}

                            <div
                                style={{
                                    display: "grid",
                                    gridTemplateColumns:
                                        "1fr 1fr",
                                    gap: "16px",
                                }}
                            >

                                <Detalhe
                                    label="Robô"
                                    value={
                                        execucaoSelecionada.robot_name
                                    }
                                />

                                <Detalhe
                                    label="Agent"
                                    value={
                                        execucaoSelecionada.agent_name
                                    }
                                />

                                <Detalhe
                                    label="Status"
                                    value={formatarStatus(
                                        execucaoSelecionada.status
                                    )}
                                />

                                <Detalhe
                                    label="Duração"
                                    value={calcularDuracao(
                                        execucaoSelecionada.started_at,
                                        execucaoSelecionada.finished_at
                                    )}
                                />

                                <Detalhe
                                    label="Início"
                                    value={formatarData(
                                        execucaoSelecionada.started_at
                                    )}
                                />

                                <Detalhe
                                    label="Fim"
                                    value={formatarData(
                                        execucaoSelecionada.finished_at
                                    )}
                                />

                            </div>


                            {/* IDENTIFICAÇÃO */}

                            <div
                                style={{
                                    marginTop: "20px",
                                    paddingTop: "20px",
                                    borderTop:
                                        "1px solid #e5e7eb",
                                }}
                            >

                                <h3
                                    style={{
                                        margin:
                                            "0 0 15px",
                                    }}
                                >
                                    Identificação
                                </h3>

                                <Detalhe
                                    label="Robot ID"
                                    value={
                                        String(
                                            execucaoSelecionada.robot_id
                                        )
                                    }
                                />

                                <div
                                    style={{
                                        marginTop: "12px",
                                    }}
                                >

                                    <Detalhe
                                        label="Agent ID"
                                        value={
                                            execucaoSelecionada.agent_id
                                        }
                                        breakWord
                                    />

                                </div>

                            </div>


                            {/* ERRO */}

                            <div
                                style={{
                                    marginTop: "20px",
                                    paddingTop: "20px",
                                    borderTop:
                                        "1px solid #e5e7eb",
                                }}
                            >

                                <h3
                                    style={{
                                        margin:
                                            "0 0 15px",
                                    }}
                                >
                                    Erro
                                </h3>

                                <div
                                    style={{
                                        minHeight: "45px",
                                        padding: "14px",
                                        background:
                                            "#f8fafc",
                                        border:
                                            "1px solid #e5e7eb",
                                        borderRadius: "8px",
                                        wordBreak:
                                            "break-word",
                                    }}
                                >
                                    {execucaoSelecionada.error_message ||
                                        "-"}
                                </div>

                            </div>

                        </div>

                    </div>

                </div>

            )}

        </section>
    );
}


/**
 * ============================================================
 * COMPONENTE PARA OS CAMPOS DO MODAL
 * ============================================================
 */
interface DetalheProps {
    label: string;
    value: string;
    breakWord?: boolean;
}

function Detalhe({
    label,
    value,
    breakWord = false,
}: DetalheProps) {

    return (
        <div
            style={{
                padding: "14px",
                background: "#f8fafc",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                boxSizing: "border-box",
            }}
        >

            <span
                style={{
                    display: "block",
                    marginBottom: "5px",
                    color: "#6b7280",
                    fontSize: "14px",
                }}
            >
                {label}
            </span>

            <strong
                style={{
                    display: "block",
                    wordBreak: breakWord
                        ? "break-all"
                        : "normal",
                }}
            >
                {value || "-"}
            </strong>

        </div>
    );
}


/**
 * ============================================================
 * ESTILOS DA TABELA
 * ============================================================
 */

const thStyle: React.CSSProperties = {
    textAlign: "left",
    padding: "12px",
    borderBottom: "1px solid #e5e7eb",
    whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
    padding: "12px",
    borderBottom: "1px solid #e5e7eb",
    verticalAlign: "top",
};


export default Executions;
