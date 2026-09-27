// ============================================================
// DUET CORE - ROBOTS - PAGE HEADER
// ============================================================
//
// Responsabilidade:
// - renderizar exclusivamente o cabeçalho visual da página
//   de gerenciamento de Robots.
//
// Este componente NÃO:
// - mantém estado;
// - realiza chamadas HTTP;
// - conhece pastas, Robots ou Agents;
// - contém regras de negócio.
//
// A separação permite que Robots.tsx permaneça responsável
// apenas pela composição da página e coordenação dos módulos.
// ============================================================

import PageHeader from "../ui/PageHeader";

function RobotsHeader() {

    return <PageHeader eyebrow="GESTÃO DE AUTOMAÇÕES" title="Robôs" description="Gerencie pacotes publicados, versões e execução nos Devices conectados." />;
}


export default RobotsHeader;
