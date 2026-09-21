import { Bell, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

// Define o título e subtítulo de cada rota da aplicação.
const pageMetadata: Record<
    string,
    { title: string; subtitle: string }
> = {
    "/": {
        title: "Dashboard",
        subtitle: "Visão geral do RPA Control Room",
    },
    "/agents": {
        title: "Agents",
        subtitle: "Gerencie os agentes de execução",
    },
    "/robots": {
        title: "Robôs",
        subtitle: "Gerencie suas automações",
    },
    "/executions": {
        title: "Execuções",
        subtitle: "Acompanhe as execuções em andamento",
    },
    "/history": {
        title: "Histórico",
        subtitle: "Consulte o histórico de execuções",
    },
    "/schedules": {
        title: "Agendamentos",
        subtitle: "Configure a execução programada dos robôs",
    },
    "/vault": {
        title: "Credenciais",
        subtitle: "Gerencie credenciais e segredos",
    },
    "/roles": {
        title: "Roles",
        subtitle: "Gerencie os perfis de acesso",
    },
    "/users": {
        title: "Usuários",
        subtitle: "Gerencie os usuários da plataforma",
    },
    "/logs": {
        title: "Logs",
        subtitle: "Consulte os registros da plataforma",
    },
};

function Header() {
    // Obtém a rota atual do navegador.
    const location = useLocation();
    // Recupera os dados do usuário autenticado pelo contexto de autenticação.
    const { user } = useAuth();

    // Busca os dados da página atual.
    // Caso a rota não esteja cadastrada, usa um título genérico.
    const metadata = pageMetadata[location.pathname] ?? {
        title: "DUET CORE",
        subtitle: "Automation & Intelligence Platform",
    };

    return (
        <header className="app-header">
            <div className="header-brand">
                <div className="header-product-name">
                    {metadata.title}
                </div>

                <div className="header-product-subtitle">
                    {metadata.subtitle}
                </div>
            </div>



            <div className="header-actions">
                <button
                    type="button"
                    className="header-search"
                    aria-label="Buscar"
                >
                    <Search size={18} strokeWidth={1.8} />

                    <span>Buscar</span>

                    <kbd>Ctrl K</kbd>
                </button>

                <button
                    type="button"
                    className="header-icon-button"
                    aria-label="Notificações"
                >
                    <Bell size={19} strokeWidth={1.8} />
                </button>

                {/* Exibe o usuário atualmente autenticado na plataforma. */}
                <div className="header-user">
                    <div className="header-user-avatar">
                        {(user?.name || user?.username || "U")
                            .charAt(0)
                            .toUpperCase()}
                    </div>

                    <div className="header-user-info">
                        <span className="header-user-name">
                            {user?.name || user?.username || "Usuário"}
                        </span>

                        <span className="header-user-role">
                            {user?.username || ""}
                        </span>
                    </div>
                </div>
            </div>
        </header>
    );
}

export default Header;