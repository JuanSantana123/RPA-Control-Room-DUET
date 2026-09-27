import { Activity, ArrowUpRight, Bot, CalendarClock, Code2, MonitorCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/useAuth";
import type { DashboardStats } from "../../types/dashboard";

interface DashboardCommandCenterProps {
  stats: DashboardStats | null;
  activeExecutions: number;
}

const shortcuts = [
  { to: "/automations/build?action=new", label: "Criar automação", description: "Abrir construção e publicação", permission: "Development:create", icon: Code2 },
  { to: "/agents", label: "Gerenciar dispositivos", description: "Revisar capacidade de execução", permission: "Agents:view", icon: MonitorCheck },
  { to: "/schedules", label: "Planejar execuções", description: "Acessar agendamentos", permission: "Schedules:view", icon: CalendarClock },
];

export default function DashboardCommandCenter({ stats, activeExecutions }: DashboardCommandCenterProps) {
  const { can } = useAuth();
  const totalAgents = stats?.total_agents ?? 0;
  const onlineAgents = stats?.agents_online ?? 0;
  const availability = totalAgents > 0 ? Math.round((onlineAgents / totalAgents) * 100) : 0;

  return (
    <section className="command-center" aria-labelledby="command-center-title">
      <div className="command-center__signal" aria-hidden="true"><span /><span /><span /></div>

      <div className="command-center__overview">
        <div className="command-center__copy">
          <div className="command-center__eyebrow"><Activity size={14} /> Centro de comando</div>
          <h2 id="command-center-title">Sua operação, em uma única perspectiva.</h2>
          <p>Capacidade, automações e atividade atual consolidadas sem perder o contexto operacional.</p>

          <div className="command-center__metrics" aria-label="Resumo operacional">
            <div><strong>{onlineAgents}</strong><span>dispositivos prontos</span></div>
            <div><strong>{stats?.total_robots ?? 0}</strong><span>automações catalogadas</span></div>
            <div><strong>{activeExecutions}</strong><span>em processamento</span></div>
          </div>
        </div>

        <div className="command-center__availability">
          <div className="availability-ring" style={{ background: `conic-gradient(var(--color-primary) ${availability}%, var(--color-surface-subtle) ${availability}% 100%)` }}>
            <div><strong>{availability}%</strong><span>disponível</span></div>
          </div>
          <p>{totalAgents > 0 ? `${onlineAgents} de ${totalAgents} dispositivos conectados` : "Nenhum dispositivo cadastrado"}</p>
        </div>
      </div>

      <nav className="command-center__shortcuts" aria-label="Atalhos operacionais">
        {shortcuts.filter(({ permission }) => can(permission)).map(({ to, label, description, icon: Icon }) => (
          <Link to={to} className="command-shortcut" key={to}>
            <span className="command-shortcut__icon"><Icon size={17} /></span>
            <span><strong>{label}</strong><small>{description}</small></span>
            <ArrowUpRight className="command-shortcut__arrow" size={16} />
          </Link>
        ))}
      </nav>

      <Bot className="command-center__watermark" size={180} strokeWidth={.65} aria-hidden="true" />
    </section>
  );
}
