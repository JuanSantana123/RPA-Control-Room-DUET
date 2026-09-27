// ============================================================
// DUET CORE - HISTORY - HEADER
// ============================================================
//
// Cabeçalho visual da página de histórico.
//
// Responsabilidade:
// - identificar a área de histórico;
// - apresentar título;
// - apresentar descrição.
//
// Este componente NÃO:
// - carrega execuções;
// - controla estado;
// - executa chamadas HTTP;
// - possui regras de histórico.
// ============================================================


import { RefreshCw } from "lucide-react";
import { Button } from "../ui/Button";
import PageHeader from "../ui/PageHeader";

// ============================================================
// COMPONENTE
// ============================================================

interface HistoryHeaderProps {
    refreshing?: boolean;
    onRefresh: () => void | Promise<void>;
}

function HistoryHeader({ refreshing = false, onRefresh }: HistoryHeaderProps) {

    return <PageHeader
        eyebrow="HISTÓRICO DE EXECUÇÕES"
        title="Histórico"
        description="Consulte as automações finalizadas e investigue seus resultados."
        actions={<Button
                onClick={onRefresh}
                busy={refreshing}
                loadingLabel="Atualizando histórico"
            >
                <RefreshCw size={16} aria-hidden="true" />
                Atualizar
            </Button>}
    />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default HistoryHeader;
