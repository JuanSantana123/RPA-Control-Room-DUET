import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/useAuth";
import { LayoutDashboard, Monitor, Code2, Bot, PlayCircle, History, CalendarClock, KeyRound, ShieldCheck, Users, FileText, LogOut, X, type LucideIcon } from "lucide-react";
import { BrandMark } from "../brand/BrandMark";
import { Button, IconButton } from "../ui/Button";

interface NavigationItem {
  to: string;
  label: string;
  permission: string;
  icon: LucideIcon;
  end?: boolean;
}

const navigationGroups: Array<{ label: string; items: NavigationItem[] }> = [
  { label: "Operação", items: [
    { to: "/", label: "Visão geral", permission: "Dashboard:view", icon: LayoutDashboard, end: true },
    { to: "/agents", label: "Dispositivos", permission: "Agents:view", icon: Monitor },
    { to: "/robots", label: "Robôs", permission: "Robots:view", icon: Bot },
    { to: "/executions", label: "Execuções", permission: "Executions:view", icon: PlayCircle },
    { to: "/history", label: "Histórico", permission: "History:view", icon: History },
    { to: "/schedules", label: "Agendamentos", permission: "Schedules:view", icon: CalendarClock },
  ]},
  { label: "Construção", items: [
    { to: "/development", label: "Desenvolvimento", permission: "Development:view", icon: Code2 },
  ]},
  { label: "Administração", items: [
    { to: "/vault", label: "Credenciais", permission: "Vault:view", icon: KeyRound },
    { to: "/roles", label: "Perfis de acesso", permission: "Roles:view", icon: ShieldCheck },
    { to: "/users", label: "Usuários", permission: "Users:view", icon: Users },
    { to: "/logs", label: "Logs do sistema", permission: "Logs:view", icon: FileText },
  ]},
];

function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { logout, can } = useAuth();
  return (
    <aside id="primary-navigation" className={`sidebar${open ? " sidebar--open" : ""}`} aria-label="Navegação principal">
      <div className="sidebar-brand">
        <BrandMark />
        <IconButton className="sidebar-close" label="Fechar navegação" icon={<X size={20} aria-hidden="true" />} onClick={onClose} />
      </div>
      <nav className="sidebar-nav">
        {navigationGroups.map((group) => {
          const allowedItems = group.items.filter((item) => can(item.permission));
          if (!allowedItems.length) return null;
          return (
            <div className="nav-group" key={group.label}>
              <span className="nav-group-label">{group.label}</span>
              {allowedItems.map(({ to, label, icon: Icon, end }) => (
                <NavLink key={to} to={to} end={end} onClick={onClose} className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
                  <span className="nav-icon"><Icon size={18} strokeWidth={1.8} /></span>
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
      <div className="sidebar-footer">
        <div className="system-indicator">
          <span className="status-dot" aria-hidden="true" />
          <div><strong>Control Room</strong><small>Sessão conectada</small></div>
        </div>
        <Button variant="ghost" onClick={() => void logout()} className="sidebar-logout"><LogOut size={17} aria-hidden="true" /><span>Sair</span></Button>
      </div>
    </aside>
  );
}

export default Sidebar;
