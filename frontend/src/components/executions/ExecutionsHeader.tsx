// ============================================================
// DUET CORE - EXECUTIONS - HEADER
// ============================================================
//
// Cabeçalho visual da página de Execuções.
//
// Responsabilidade:
// - apresentar contexto da página;
// - apresentar título e descrição;
// - disponibilizar a ação manual de atualização.
//
// Origem das ações:
// - recebe onRefresh através de props.
//
// Este componente NÃO:
// - consulta a API;
// - controla polling;
// - mantém estado das execuções;
// - conhece filtros ou ações de stop/cancel.
//
// O componente preserva a estrutura e as classes CSS
// anteriormente existentes em pages/Executions.tsx.
// ============================================================

import {
    RefreshCw,
} from "lucide-react";
import { Button } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface ExecutionsHeaderProps {

    // Solicita uma atualização manual das execuções.
    onRefresh: () => void | Promise<void>;
}


// ============================================================
// INDICADOR VISUAL
// ============================================================
//
// Pequeno indicador utilizado no eyebrow do cabeçalho.
// Foi movido junto com o cabeçalho porque sua única
// responsabilidade é visual.
// ============================================================

function ActivityIndicator() {

    return (
        <span
            className="activity-indicator"
        />
    );
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionsHeader({
    onRefresh,
}: ExecutionsHeaderProps) {

    return (
        <header className="page-heading executions-page-header">

            <div>

                <div className="page-eyebrow">

                    <ActivityIndicator />

                    MONITORAMENTO OPERACIONAL

                </div>


                <h1>
                    Execuções
                </h1>


                <p>
                    Acompanhe em tempo real os robôs em execução no ambiente.
                </p>

            </div>


            <Button
                onClick={onRefresh}
                title="Atualizar execuções"
            >
                <RefreshCw size={16} />

                Atualizar
            </Button>

        </header>
    );
}


export default ExecutionsHeader;
