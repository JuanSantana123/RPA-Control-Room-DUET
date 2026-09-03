import { useEffect, useState } from "react";
import api from "../services/api";

/**
 * ============================================================
 * TIPOS
 * ============================================================
 *
 * Representa os dados retornados pelo endpoint:
 *
 * GET /dashboard/stats
 */
interface DashboardStats {
    total_agents: number;
    agents_online: number;
    total_robots: number;
}


/**
 * Representa uma execução retornada pelo endpoint:
 *
 * GET /executions
 */
interface Execution {
    id: number;
    robot_id: number;
    robot_name: string;
    filename: string;
    agent_id: string;
    agent_name: string;
    status: string;
    started_at: string | null;
    finished_at: string | null;
    error_message: string | null;
}


/**
 * ============================================================
 * DASHBOARD
 * ============================================================
 */
function Dashboard() {

    /**
     * Estatísticas gerais do Control Room.
     */
    const [stats, setStats] = useState<DashboardStats | null>(null);

    /**
     * Lista de execuções atualmente em andamento.
     */
    const [executions, setExecutions] = useState<Execution[]>([]);

    /**
     * Controle de carregamento inicial.
     */
    const [loading, setLoading] = useState(true);

    /**
     * Mensagem de erro da API.
     */
    const [error, setError] = useState("");


    /**
     * ========================================================
     * CARREGAR ESTATÍSTICAS
     * ========================================================
     *
     * Busca:
     *
     * - Total de Agents
     * - Agents online
     * - Total de Robôs
     */
    useEffect(() => {

        api.get("/dashboard/stats")
            .then((response) => {

                setStats(response.data);

            })
            .catch((err) => {

                console.error(
                    "Erro ao buscar estatísticas do Dashboard:",
                    err
                );

                setError(
                    "Não foi possível carregar as estatísticas do Dashboard."
                );

            })
            .finally(() => {

                setLoading(false);

            });

    }, []);


    /**
     * ========================================================
     * CARREGAR EXECUÇÕES
     * ========================================================
     *
     * O endpoint /executions atualmente retorna as execuções
     * que estão em andamento.
     */
    useEffect(() => {

        api.get("/executions")
            .then((response) => {

                setExecutions(response.data.executions);

            })
            .catch((err) => {

                console.error(
                    "Erro ao buscar execuções:",
                    err
                );

            });

    }, []);


    /**
     * ========================================================
     * ESTADO DE CARREGAMENTO
     * ========================================================
     */
    if (loading) {

        return (
            <div className="empty-state">

                <div className="empty-icon">
                    ⏳
                </div>

                <h3>
                    Carregando Dashboard...
                </h3>

                <p>
                    Buscando informações do Control Room.
                </p>

            </div>
        );
    }


    /**
     * ========================================================
     * ESTADO DE ERRO
     * ========================================================
     */
    if (error) {

        return (
            <div className="empty-state">

                <div className="empty-icon">
                    ⚠️
                </div>

                <h3>
                    Erro ao carregar Dashboard
                </h3>

                <p>
                    {error}
                </p>

            </div>
        );
    }


    return (
        <div>

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="panel-header">

                <div>

                    <h2>
                        Dashboard
                    </h2>

                    <p>
                        Visão geral do RPA Control Room
                    </p>

                </div>

            </div>


            {/* ==================================================
                CARDS DE RESUMO
                ================================================== */}

            <section className="cards">

                {/* ----------------------------------------------
                    TOTAL DE AGENTS
                    ---------------------------------------------- */}

                <div className="card">

                    <div className="card-title">
                        Agents
                    </div>

                    <div className="card-value">
                        {stats?.total_agents ?? 0}
                    </div>

                    <div className="card-info">
                        Agents cadastrados
                    </div>

                </div>


                {/* ----------------------------------------------
                    AGENTS ONLINE
                    ---------------------------------------------- */}

                <div className="card">

                    <div className="card-title">
                        Agents Online
                    </div>

                    <div className="card-value">
                        {stats?.agents_online ?? 0}
                    </div>

                    <div className="card-info">
                        Agents disponíveis
                    </div>

                </div>


                {/* ----------------------------------------------
                    TOTAL DE ROBÔS
                    ---------------------------------------------- */}

                <div className="card">

                    <div className="card-title">
                        Robôs
                    </div>

                    <div className="card-value">
                        {stats?.total_robots ?? 0}
                    </div>

                    <div className="card-info">
                        Robôs cadastrados
                    </div>

                </div>


                {/* ----------------------------------------------
                    EXECUÇÕES
                    ---------------------------------------------- */}

                <div className="card">

                    <div className="card-title">
                        Execuções
                    </div>

                    <div className="card-value">
                        {executions.length}
                    </div>

                    <div className="card-info">
                        Execuções em andamento
                    </div>

                </div>

            </section>


            {/* ==================================================
                PAINEL DE EXECUÇÕES
                ================================================== */}

            <section className="panel">

                <div className="panel-header">

                    <div>

                        <h2>
                            Execuções em andamento
                        </h2>

                        <p>
                            Execuções atualmente processadas pelos Agents
                        </p>

                    </div>

                </div>


                {/* =================================================
                    NENHUMA EXECUÇÃO
                    ================================================= */}

                {executions.length === 0 ? (

                    <div className="empty-state">

                        <div className="empty-icon">
                            ▶️
                        </div>

                        <h3>
                            Nenhuma execução em andamento
                        </h3>

                        <p>
                            Não existem robôs sendo executados neste momento.
                        </p>

                    </div>

                ) : (

                    /* ==============================================
                       TABELA DE EXECUÇÕES
                       ============================================== */

                    <div className="table-container">

                        <table>

                            <thead>

                                <tr>

                                    <th>
                                        ID
                                    </th>

                                    <th>
                                        Robô
                                    </th>

                                    <th>
                                        Agent
                                    </th>

                                    <th>
                                        Início
                                    </th>

                                    <th>
                                        Status
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {executions.map((execution) => (

                                    <tr key={execution.id}>

                                        <td>
                                            {execution.id}
                                        </td>

                                        <td>
                                            {execution.robot_name}
                                        </td>

                                        <td>

                                            <div className="agent-name">

                                                <strong>
                                                    {execution.agent_name}
                                                </strong>

                                                <small>
                                                    {execution.agent_id}
                                                </small>

                                            </div>

                                        </td>

                                        <td>
                                            {formatarData(execution.started_at)}
                                        </td>

                                        <td>
                                            {execution.status}
                                        </td>

                                    </tr>

                                ))}

                            </tbody>

                        </table>

                    </div>

                )}

            </section>

        </div>
    );
}


/**
 * ============================================================
 * FORMATAR DATA
 * ============================================================
 *
 * Converte a data retornada pela API para o formato
 * utilizado normalmente no Control Room.
 */
function formatarData(data: string | null): string {

    if (!data) {
        return "-";
    }

    const dataObj = new Date(data);

    if (Number.isNaN(dataObj.getTime())) {
        return "-";
    }

    return dataObj.toLocaleString("pt-BR");
}


export default Dashboard;