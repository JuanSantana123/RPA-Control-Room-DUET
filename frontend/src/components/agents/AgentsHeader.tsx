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

import {
    Bot,
} from "lucide-react";


// ============================================================
// COMPONENTE
// ============================================================

function AgentsHeader() {

    return (
        <div className="page-heading">

            <div>

                <div className="page-eyebrow">
                    INFRAESTRUTURA
                </div>

                <h1>
                    Devices
                </h1>

                <p>
                    Gerencie os devices responsáveis pela execução das automações.
                </p>

            </div>


            <div className="page-heading-icon">
                <Bot
                    size={22}
                    strokeWidth={1.7}
                />
            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentsHeader;