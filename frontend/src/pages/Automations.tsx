import {
  Blocks,
  Boxes,
  Code2,
  LayoutDashboard,
  Library,
} from "lucide-react";
import { Navigate, NavLink, useLocation, useSearchParams } from "react-router-dom";
import AutomationOverview from "../components/automations/AutomationOverview";
import LibrariesPanel from "../components/libraries/LibrariesPanel";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import PageHeader from "../components/ui/PageHeader";
import { useAuth } from "../context/useAuth";
import Development from "./Development";
import Robots from "./Robots";

type AutomationArea = "overview" | "build" | "robots" | "libraries";

const navigation = [
  { area: "overview" as const, to: "/automations/overview", label: "Visão geral", description: "Prioridades e capacidade", icon: LayoutDashboard },
  { area: "build" as const, to: "/automations/build", label: "Construção", description: "Projetos e workflow", icon: Code2 },
  { area: "robots" as const, to: "/automations/catalog/robots", label: "Publicados", description: "Pacotes e versões", icon: Boxes },
  { area: "libraries" as const, to: "/automations/catalog/libraries", label: "Bibliotecas", description: "Dependências reutilizáveis", icon: Library },
];

function areaFromPath(pathname: string): AutomationArea {
  if (pathname.includes("/catalog/libraries")) return "libraries";
  if (pathname.includes("/catalog/robots")) return "robots";
  if (pathname.includes("/build")) return "build";
  return "overview";
}

function AutomationLibraries() {
  return (
    <section className="automation-library-view" aria-labelledby="automation-library-title">
      <div className="automation-section-heading">
        <span className="automation-section-heading__icon" aria-hidden="true">
          <Blocks size={18} strokeWidth={1.8} />
        </span>
        <div>
          <span>Catálogo compartilhado</span>
          <h2 id="automation-library-title">Bibliotecas</h2>
          <p>Gerencie dependências reutilizáveis e versões aprovadas sem misturá-las aos pacotes de robôs.</p>
        </div>
      </div>
      <LibrariesPanel />
    </section>
  );
}

export default function Automations() {
  const { can } = useAuth();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const canBuild = can("Development:view");
  const canCreateProject = can("Development:create");
  const canUseCatalog = can("Robots:view");
  const canUseLibraries = can("Libraries:view");
  const requestedArea = areaFromPath(location.pathname);

  if (requestedArea === "build" && !canBuild) return <Navigate replace to="/automations/overview" />;
  if (requestedArea === "robots" && !canUseCatalog) return <Navigate replace to="/automations/overview" />;
  if (requestedArea === "libraries" && !canUseLibraries) return <Navigate replace to="/automations/overview" />;

  const visibleNavigation = navigation.filter(({ area }) => {
    if (area === "build") return canBuild;
    if (area === "robots") return canUseCatalog;
    if (area === "libraries") return canUseLibraries;
    return true;
  });
  const noModuleAccess = !canBuild && !canUseCatalog && !canUseLibraries;

  return (
    <div className="page-container automation-hub">
      <PageHeader eyebrow="CENTRAL DE AUTOMAÇÕES" title="Automações" description="Crie, publique e governe automações em uma jornada única." />

      <nav className="automation-hub__navigation" aria-label="Áreas de Automações">
        {visibleNavigation.map(({ to, label, description, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `automation-hub__nav-item${isActive ? " is-active" : ""}`}>
            <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
            <span><strong>{label}</strong><small>{description}</small></span>
          </NavLink>
        ))}
      </nav>

      {noModuleAccess ? (
        <FeedbackBanner
          tone="error"
          title="Acesso ao módulo de automações restrito"
          message="Seu perfil não possui acesso à construção, aos robôs publicados ou às bibliotecas."
          hint="Solicite as permissões necessárias ao administrador do Control Room."
        />
      ) : (
        <main className="automation-hub__workspace">
          {requestedArea === "overview" && (
            <AutomationOverview
              canBuild={canBuild}
              canCreateProject={canCreateProject}
              canUseCatalog={canUseCatalog}
              canUseLibraries={canUseLibraries}
              canViewAgents={can("Executions:execute")}
            />
          )}
          {requestedArea === "build" && (
            <Development embedded initialAction={searchParams.get("action") === "new" ? "new-project" : undefined} />
          )}
          {requestedArea === "robots" && <Robots embedded />}
          {requestedArea === "libraries" && <AutomationLibraries />}
        </main>
      )}
    </div>
  );
}
