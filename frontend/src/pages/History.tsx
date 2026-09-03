import { useEffect, useState } from "react";

import api from "../services/api";

// ============================================================
// TIPO - EXECUÇÃO
// ============================================================
//
// Representa uma execução finalizada retornada pela API:
//
// GET /executions/history
// ============================================================

interface Execution {
    id: number;
    robot_name: string | null;
    agent_name: string | null;
    started_at: string | null;
    finished_at: string | null;
    status: string;
    error_message: string | null;
}


// ============================================================
// PÁGINA DE HISTÓRICO
// ============================================================
//
// Esta página substitui o antigo:
//
// history.html
//
// Funcionalidades:
// - Carregar histórico
// - Exibir execuções finalizadas
// - Calcular duração
// - Formatar datas
// - Traduzir status
// - Atualizar automaticamente a cada 5 segundos
// ============================================================

function History() {

    // ========================================================
    // ESTADO DO HISTÓRICO
    // ========================================================
    //
    // Guarda as execuções retornadas pelo backend.
    // ========================================================

    const [executions, setExecutions] = useState<Execution[]>([]);


    // ========================================================
    // ESTADO DE CARREGAMENTO
    // ========================================================
    //
    // Controla a mensagem exibida enquanto a API responde.
    // ========================================================

    const [loading, setLoading] = useState(true);


    // ========================================================
    // ESTADO DE ERRO
    // ========================================================
    //
    // Guarda uma mensagem caso a consulta ao backend falhe.
    // ========================================================

    const [error, setError] = useState("");


    // ========================================================
    // CARREGAR HISTÓRICO
    // ========================================================
    //
    // Consulta:
    //
    // GET /executions/history
    //
    // Esse endpoint já existe no Control Room.
    // ========================================================

    const carregarHistorico = async () => {

        try {

            // Faz a requisição para o Control Room.
            const response = await api.get(
                "/executions/history"
            );


            // Pega a lista de execuções retornada pela API.
            //
            // Caso executions não exista, utiliza uma lista vazia.
            const lista =
                response.data.executions || [];


            // Atualiza o estado do React.
            setExecutions(lista);


            // Remove qualquer erro anterior.
            setError("");

        } catch (err) {

            // Mostra o erro no console para facilitar diagnóstico.
            console.error(
                "Erro ao carregar histórico:",
                err
            );


            // Mostra mensagem na tela.
            setError(
                "Não foi possível carregar o histórico."
            );

        } finally {

            // Finaliza o estado de carregamento.
            setLoading(false);
        }
    };


    // ========================================================
    // PRIMEIRA CARGA + ATUALIZAÇÃO AUTOMÁTICA
    // ========================================================
    //
    // O history.html antigo fazia:
    //
    // setInterval(carregarHistorico, 5000)
    //
    // Aqui fazemos a mesma coisa utilizando useEffect.
    // ========================================================

    useEffect(() => {

        // Carrega imediatamente ao abrir a página.
        carregarHistorico();


        // Cria atualização automática a cada 5 segundos.
        const intervalo = setInterval(() => {

            carregarHistorico();

        }, 5000);


        // ====================================================
        // LIMPEZA
        // ====================================================
        //
        // Quando o usuário sair da página, removemos o
        // intervalo para evitar requisições desnecessárias.
        // ====================================================

        return () => {

            clearInterval(intervalo);

        };

    }, []);


    // ========================================================
    // FORMATAR DATA
    // ========================================================
    //
    // Equivalente ao:
    //
    // new Date(data).toLocaleString("pt-BR")
    //
    // utilizado no history.html.
    // ========================================================

    const formatarData = (
        data: string | null
    ) => {

        // Quando não existe data, mostra "-".
        if (!data) {
            return "-";
        }


        // Converte a data para o formato brasileiro.
        return new Date(data).toLocaleString(
            "pt-BR"
        );
    };


    // ========================================================
    // CALCULAR DURAÇÃO
    // ========================================================
    //
    // Calcula a diferença entre:
    //
    // finished_at - started_at
    //
    // Mantendo a mesma lógica do history.html.
    // ========================================================

    const calcularDuracao = (
        inicio: string | null,
        fim: string | null
    ) => {

        // Se uma das datas não existir,
        // não é possível calcular a duração.
        if (!inicio || !fim) {
            return "-";
        }


        // Converte as duas datas.
        const dataInicio = new Date(inicio);

        const dataFim = new Date(fim);


        // Calcula a diferença em segundos.
        const segundos = Math.floor(
            (
                dataFim.getTime() -
                dataInicio.getTime()
            ) / 1000
        );


        // Proteção contra valores inválidos.
        if (segundos < 0) {
            return "-";
        }


        // ====================================================
        // MENOS DE UM MINUTO
        // ====================================================

        if (segundos < 60) {

            return `${segundos}s`;

        }


        // ====================================================
        // UM MINUTO OU MAIS
        // ====================================================

        const minutos = Math.floor(
            segundos / 60
        );


        const resto = segundos % 60;


        return `${minutos}m ${resto}s`;
    };


    // ========================================================
    // CONVERTER STATUS
    // ========================================================
    //
    // Converte os status internos do banco/API para os textos
    // exibidos ao usuário.
    // ========================================================

    const formatarStatus = (
        status: string
    ) => {

        // Execução concluída com sucesso.
        if (status === "success") {
            return "Sucesso";
        }


        // Execução terminou com erro.
        if (status === "error") {
            return "Erro";
        }


        // Execução foi parada.
        if (status === "stopped") {
            return "Parado";
        }


        // Para qualquer outro status,
        // mantém o valor original.
        return status;
    };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <div>

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <section>

                <h1>
                    Histórico
                </h1>

                <p>
                    Histórico das execuções finalizadas
                </p>

            </section>


            {/* ==================================================
                TABELA
                ================================================== */}

            <section>

                <table>

                    {/* ==================================================
                        CABEÇALHO DA TABELA
                        ================================================== */}

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
                                Fim
                            </th>

                            <th>
                                Duração
                            </th>

                            <th>
                                Status
                            </th>

                            <th>
                                Erro
                            </th>

                        </tr>

                    </thead>


                    {/* ==================================================
                        CORPO DA TABELA
                        ================================================== */}

                    <tbody>

                        {/* ==================================================
                            CARREGANDO
                            ================================================== */}

                        {loading && (

                            <tr>

                                <td
                                    colSpan={8}
                                >
                                    Carregando histórico...
                                </td>

                            </tr>

                        )}


                        {/* ==================================================
                            ERRO
                            ================================================== */}

                        {!loading && error && (

                            <tr>

                                <td
                                    colSpan={8}
                                >
                                    {error}
                                </td>

                            </tr>

                        )}


                        {/* ==================================================
                            NENHUMA EXECUÇÃO
                            ================================================== */}

                        {!loading &&
                            !error &&
                            executions.length === 0 && (

                                <tr>

                                    <td
                                        colSpan={8}
                                    >
                                        Nenhuma execução finalizada.
                                    </td>

                                </tr>

                            )}


                        {/* ==================================================
                            EXECUÇÕES
                            ================================================== */}

                        {!loading &&
                            !error &&
                            executions.map(
                                (execution) => (

                                    <tr
                                        key={execution.id}
                                    >

                                        {/* ID */}
                                        <td>
                                            {execution.id}
                                        </td>


                                        {/* ROBÔ */}
                                        <td>
                                            {execution.robot_name || "-"}
                                        </td>


                                        {/* AGENT */}
                                        <td>
                                            {execution.agent_name || "-"}
                                        </td>


                                        {/* INÍCIO */}
                                        <td>
                                            {formatarData(
                                                execution.started_at
                                            )}
                                        </td>


                                        {/* FIM */}
                                        <td>
                                            {formatarData(
                                                execution.finished_at
                                            )}
                                        </td>


                                        {/* DURAÇÃO */}
                                        <td>
                                            {calcularDuracao(
                                                execution.started_at,
                                                execution.finished_at
                                            )}
                                        </td>


                                        {/* STATUS */}
                                        <td>
                                            {formatarStatus(
                                                execution.status
                                            )}
                                        </td>


                                        {/* ERRO */}
                                        <td>
                                            {execution.error_message || "-"}
                                        </td>

                                    </tr>

                                )
                            )}

                    </tbody>

                </table>

            </section>

        </div>

    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================
//
// Permite que o App.tsx importe:
//
// import History from "./pages/History";
// ============================================================

export default History;