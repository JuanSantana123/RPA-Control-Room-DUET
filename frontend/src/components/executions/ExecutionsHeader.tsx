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
import PageHeader from "../ui/PageHeader";


// ============================================================
// PROPS
// ============================================================

interface ExecutionsHeaderProps {

    // Solicita uma atualização manual das execuções.
    onRefresh: () => void | Promise<void>;
    refreshing?: boolean;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionsHeader({
    onRefresh,
    refreshing = false,
}: ExecutionsHeaderProps) {

    return <PageHeader
        eyebrow="MONITORAMENTO OPERACIONAL"
        title="Execuções"
        description="Acompanhe as automações em andamento e intervenha quando necessário."
        actions={<Button
                onClick={onRefresh}
                title="Atualizar execuções"
                busy={refreshing}
                loadingLabel="Atualizando execuções"
            >
                <RefreshCw size={16} />

                Atualizar
            </Button>}
    />;
}


export default ExecutionsHeader;
