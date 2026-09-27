// ============================================================

import { CalendarPlus } from "lucide-react";
import { Button } from "../ui/Button";
import AccessModeBadge from "../ui/AccessModeBadge";
import PageHeader from "../ui/PageHeader";
// DUET CORE - SCHEDULES - HEADER
// ============================================================
//
// Cabeçalho visual da página de Agendamentos.
//
// Responsabilidade:
// - exibir título e descrição da área;
// - disponibilizar a ação "Novo Agendamento".
//
// A ação é recebida da página através de callback.
//
// Este componente NÃO:
// - abre modal diretamente;
// - executa chamadas HTTP;
// - possui regras de Scheduler;
// - controla estado de formulário.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface SchedulesHeaderProps {
    canCreate: boolean;
    onNewSchedule: () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function SchedulesHeader({
    canCreate,
    onNewSchedule,
}: SchedulesHeaderProps) {

    return <PageHeader
        eyebrow="AGENDAMENTOS DE AUTOMAÇÃO"
        title="Agendamentos"
        description="Programe execuções recorrentes ou pontuais com controle operacional."
        actions={canCreate ? <Button
                variant="primary"
                onClick={onNewSchedule}
            >
                <CalendarPlus size={17} strokeWidth={1.9} aria-hidden="true" />
                Novo agendamento
            </Button> : <AccessModeBadge />}
    />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default SchedulesHeader;
