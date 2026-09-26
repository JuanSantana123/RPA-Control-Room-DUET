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

// ============================================================
// COMPONENTE
// ============================================================

interface HistoryHeaderProps {
    refreshing?: boolean;
    onRefresh: () => void | Promise<void>;
}

function HistoryHeader({ refreshing = false, onRefresh }: HistoryHeaderProps) {

    return (
        <section className="page-heading">

            <div>

                <div className="page-eyebrow">
                    HISTÓRICO DE EXECUÇÕES
                </div>

                <h1>
                    Histórico
                </h1>

                <p>
                    Histórico das execuções finalizadas
                </p>

            </div>

            <Button
                onClick={onRefresh}
                busy={refreshing}
                loadingLabel="Atualizando histórico"
            >
                <RefreshCw size={16} aria-hidden="true" />
                Atualizar
            </Button>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default HistoryHeader;
