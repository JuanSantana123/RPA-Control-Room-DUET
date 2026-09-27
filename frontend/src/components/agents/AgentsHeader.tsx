// ============================================================
// DUET CORE - AGENTS - HEADER
// ============================================================
//
// Cabeçalho visual da área de Devices/Agents.
//
// Responsabilidade:
// - identificar a área de infraestrutura;
// - exibir o título "Devices";
// - exibir a descrição da página;
// - apresentar o ícone visual da feature.
//
// Este componente NÃO:
// - executa chamadas HTTP;
// - possui estado;
// - cadastra ou remove Agents;
// - conhece regras operacionais.
//
// Toda a lógica permanece fora da camada visual.
// ============================================================

import PageHeader from "../ui/PageHeader";

function AgentsHeader() {

    return <PageHeader eyebrow="INFRAESTRUTURA" title="Dispositivos" description="Gerencie os Devices responsáveis pela execução das automações." />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentsHeader;
