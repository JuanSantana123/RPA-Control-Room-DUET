import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

import {
    LayoutDashboard,
    Monitor,
    Code2,
    Bot,
    PlayCircle,
    History,
    CalendarClock,
    KeyRound,
    ShieldCheck,
    Users,
    FileText,
    LogOut,
} from "lucide-react";

/*
|--------------------------------------------------------------------------
| SIDEBAR
|--------------------------------------------------------------------------
| Responsável exclusivamente pela navegação lateral da aplicação.
|
| Mantém:
| - Logo
| - Menu principal
| - Identificação da rota ativa
| - Status do sistema
| - Logout
|--------------------------------------------------------------------------
*/

function Sidebar() {
    const { logout } = useAuth();

    const location = useLocation();

    /*
    |--------------------------------------------------------------------------
    | Verifica se a rota está ativa
    |--------------------------------------------------------------------------
    */

    const isActive = (path: string) => {
        if (path === "/") {
            return location.pathname === "/";
        }

        return location.pathname.startsWith(path);
    };

    return (
        <aside className="sidebar">

            {/* ============================================================
                LOGO
            ============================================================ */}

            <div className="logo">
                <div className="logo-main">
                    DUET CORE
                </div>

                <div className="logo-subtitle">
                    AUTOMATION & INTELLIGENCE
                </div>
            </div>


            {/* ============================================================
                MENU PRINCIPAL
            ============================================================ */}

            <nav className="sidebar-nav">

                {/* Dashboard */}

                <Link
                    to="/"
                    className={`nav-item ${isActive("/") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <LayoutDashboard
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Dashboard
                    </span>
                </Link>


                {/* Agents */}

                <Link
                    to="/agents"
                    className={`nav-item ${isActive("/agents") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <Monitor
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Devices
                    </span>
                </Link>

                {/* Desenvolvimento */}

                <Link
                    to="/development"
                    className={`nav-item ${isActive("/development") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <Code2
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Desenvolvimento
                    </span>
                </Link>


                {/* Robôs */}

                <Link
                    to="/robots"
                    className={`nav-item ${isActive("/robots") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <Bot
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Robôs
                    </span>
                </Link>


                {/* Execuções */}

                <Link
                    to="/executions"
                    className={`nav-item ${isActive("/executions") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <PlayCircle
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Execuções
                    </span>
                </Link>


                {/* Histórico */}

                <Link
                    to="/history"
                    className={`nav-item ${isActive("/history") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <History
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Histórico
                    </span>
                </Link>


                {/* Agendamentos */}

                <Link
                    to="/schedules"
                    className={`nav-item ${isActive("/schedules") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <CalendarClock
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Agendamentos
                    </span>
                </Link>


                {/* Credenciais / Vault */}

                <Link
                    to="/vault"
                    className={`nav-item ${isActive("/vault") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <KeyRound
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Credenciais
                    </span>
                </Link>


                {/* Roles */}

                <Link
                    to="/roles"
                    className={`nav-item ${isActive("/roles") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <ShieldCheck
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Roles
                    </span>
                </Link>


                {/* Usuários */}

                <Link
                    to="/users"
                    className={`nav-item ${isActive("/users") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <Users
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Usuários
                    </span>
                </Link>


                {/* Logs */}

                <Link
                    to="/logs"
                    className={`nav-item ${isActive("/logs") ? "active" : ""}`}
                >
                    <span className="nav-icon">
                        <FileText
                            size={18}
                            strokeWidth={1.8}
                        />
                    </span>

                    <span>
                        Logs
                    </span>
                </Link>

            </nav>


            {/* ============================================================
                RODAPÉ DA SIDEBAR
            ============================================================ */}

            <div className="sidebar-footer">

                {/* Status do sistema */}

                <div className="system-indicator">

                    <span className="status-dot"></span>

                    <div>
                        <strong>
                            Sistema Online
                        </strong>

                        <small>
                            Control Room
                        </small>
                    </div>

                </div>


                {/* Logout */}

                <button
                    type="button"
                    onClick={logout}
                    className="sidebar-logout"
                >
                    <LogOut
                        size={17}
                        strokeWidth={1.8}
                    />

                    <span>
                        Sair
                    </span>
                </button>

            </div>

        </aside>
    );
}

export default Sidebar;