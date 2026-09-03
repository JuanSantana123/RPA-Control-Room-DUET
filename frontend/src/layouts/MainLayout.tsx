import { Link, Outlet, useLocation } from "react-router-dom";

/**
 * ============================================================
 * MAIN LAYOUT
 * ============================================================
 *
 * Layout principal do RPA Control Room.
 *
 * Esta estrutura substitui o antigo base.html.
 *
 * O layout possui:
 *
 * - Sidebar fixa
 * - Logo RPA / CONTROL ROOM
 * - Menu de navegação
 * - Identificação visual da página atual
 * - Indicador de sistema online
 * - Área principal onde as páginas React são renderizadas
 *
 * O <Outlet /> é responsável por renderizar:
 *
 * Dashboard
 * Agents
 * Robôs
 * Execuções
 * Histórico
 * Agendamentos
 *
 * conforme a rota acessada.
 * ============================================================
 */

function MainLayout() {

    /**
     * Obtém a rota atual do navegador.
     *
     * Usaremos isso para aplicar a classe "active"
     * no item correspondente do menu.
     */
    const location = useLocation();

    /**
     * Verifica se uma determinada rota está ativa.
     *
     * A função "/" precisa de um tratamento separado,
     * pois todas as outras páginas também começam com "/".
     */
    const isActive = (path: string) => {

        if (path === "/") {
            return location.pathname === "/";
        }

        return location.pathname.startsWith(path);
    };

    return (

        <div className="layout">

            {/* ====================================================
                SIDEBAR
                ==================================================== */}

            <aside className="sidebar">

                {/* =================================================
                    LOGO
                    ================================================= */}

                <div className="logo">

                    <div className="logo-main">
                        RPA
                    </div>

                    <div className="logo-subtitle">
                        CONTROL ROOM
                    </div>

                </div>


                {/* =================================================
                    MENU PRINCIPAL
                    ================================================= */}

                <nav className="sidebar-nav">

                    {/* Dashboard */}

                    <Link
                        to="/"
                        className={`nav-item ${isActive("/") ? "active" : ""}`}
                    >

                        <span className="nav-icon">
                            🏠
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
                            🖥️
                        </span>

                        <span>
                            Agents
                        </span>

                    </Link>


                    {/* Robôs */}

                    <Link
                        to="/robots"
                        className={`nav-item ${isActive("/robots") ? "active" : ""}`}
                    >

                        <span className="nav-icon">
                            🤖
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
                            ▶️
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
                            🕘
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
                            📅
                        </span>

                        <span>
                            Agendamentos
                        </span>

                    </Link>


                    {/* Logs

                        O antigo base.html possuía este item,
                        mas ainda não existe uma tela de Logs
                        implementada no React.

                        Por isso ele permanece visualmente no menu,
                        porém sem navegação por enquanto.
                    */}

                    <Link
                        to="/logs"
                        className={`nav-item ${isActive("/logs") ? "active" : ""}`}
                    >

                        <span className="nav-icon">
                            📋
                        </span>

                        <span>
                            Logs
                        </span>

                    </Link>

                </nav>


                {/* =================================================
                    RODAPÉ DA SIDEBAR
                    ================================================= */}

                <div className="sidebar-footer">

                    <div className="system-indicator">

                        {/* Bolinha verde de sistema online */}

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

                </div>

            </aside>


            {/* ====================================================
                CONTEÚDO PRINCIPAL
                ==================================================== */}

            <main className="content">

                {/*
                    O React Router coloca aqui a página correspondente
                    à rota atual.

                    Exemplo:

                    "/"              → Dashboard
                    "/agents"        → Agents
                    "/robots"        → Robots
                    "/executions"    → Executions
                    "/history"       → History
                    "/schedules"     → Schedules
                */}

                <Outlet />

            </main>

        </div>
    );
}

export default MainLayout;
