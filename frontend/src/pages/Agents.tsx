// ============================================================
// DUET CORE - AGENTS PAGE
// ============================================================
//
// Página principal da área de Devices/Agents.
//
// Responsabilidade:
// - compor a interface da feature;
// - conectar os dados aos componentes visuais;
// - encaminhar as operações fornecidas pelo hook;
// - apresentar mensagens globais de erro.
//
// A lógica operacional foi distribuída para:
//
// useAgentsData
// - carregamento dos Agents;
// - cadastro;
// - exclusão;
// - download;
// - estado do formulário;
// - loading e erros.
//
// Componentes:
// - AgentsHeader;
// - AgentCreatePanel;
// - AgentsList;
// - AgentCard.
//
// Esta página NÃO deve concentrar:
// - chamadas HTTP;
// - implementação de cards;
// - implementação do formulário;
// - regras de cadastro;
// - manipulação do download;
// - regras de exclusão.
//
// Dessa forma, Agents.tsx permanece como camada de
// composição/orquestração da feature.
// ============================================================

import AgentsHeader
    from "../components/agents/AgentsHeader";

import AgentCreatePanel
    from "../components/agents/AgentCreatePanel";

import AgentsList
    from "../components/agents/AgentsList";

import {
    useAgentsData,
} from "../hooks/agents/useAgentsData";


// ============================================================
// PÁGINA DE AGENTS
// ============================================================

function Agents() {

    // ========================================================
    // DADOS / OPERAÇÕES
    // ========================================================
    //
    // Toda a responsabilidade operacional da feature fica
    // encapsulada no hook.
    //
    // A página apenas distribui estado e callbacks para os
    // componentes responsáveis pela apresentação.
    // ========================================================

    const {
        agents,
        loading,
        error,

        newAgent,
        setNewAgent,

        creatingAgent,

        cadastrarAgent,
        alterarAmbienteAgent,
        excluirAgent,
        baixarAgent,
    } = useAgentsData();


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container agents-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <AgentsHeader />


            {/* ==================================================
                MENSAGEM DE ERRO
                ================================================== */}

            {error && (

                <div className="alert alert-error">
                    {error}
                </div>

            )}


            {/* ==================================================
                CADASTRO
                ================================================== */}

            <AgentCreatePanel
                newAgent={
                    newAgent
                }
                setNewAgent={
                    setNewAgent
                }
                creatingAgent={
                    creatingAgent
                }
                onCreate={
                    cadastrarAgent
                }
            />


            {/* ==================================================
                LISTAGEM
                ================================================== */}

            <AgentsList
                agents={
                    agents
                }
                loading={
                    loading
                }
                error={
                    error
                }
                onEnvironmentChange={
                    alterarAmbienteAgent
                }
                onDownload={
                    baixarAgent
                }
                onDelete={
                    excluirAgent
                }
            />

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Agents;