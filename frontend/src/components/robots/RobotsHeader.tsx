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

function RobotsHeader() {

    return (
        <div className="page-heading">
            <div>
                <div className="page-eyebrow">
                    GESTÃO DE AUTOMAÇÕES
                </div>

                <h1>Robôs</h1>

                <p>
                    Gerencie os robôs disponíveis, organize suas pastas e
                    execute automações nos dispositivos conectados.
                </p>
            </div>

        </div>
    );
}


export default RobotsHeader;
