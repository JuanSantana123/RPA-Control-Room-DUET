import { ArrowRight, Blocks, Boxes, Code2, FolderTree, PencilLine, RefreshCw, Server } from "lucide-react";
import { Link } from "react-router-dom";
import useAutomationOverview from "../../hooks/automations/useAutomationOverview";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import FeedbackBanner from "../ui/FeedbackBanner";
import { Skeleton } from "../ui/Skeletons";

interface AutomationOverviewProps {
  canBuild: boolean;
  canCreateProject: boolean;
  canUseCatalog: boolean;
  canUseLibraries: boolean;
  canViewAgents: boolean;
}

function formatUpdatedAt(value: string | null): string {
  if (!value) return "Sem atualização registrada";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Atualização registrada";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(parsed);
}

export default function AutomationOverview({ canBuild, canCreateProject, canUseCatalog, canUseLibraries, canViewAgents }: AutomationOverviewProps) {
  const overview = useAutomationOverview({ canBuild, canUseCatalog, canViewAgents });
  const inCheckout = overview.projects.filter((project) => project.hasCheckout).length;

  if (overview.loading) {
    return (
      <div className="automation-overview" aria-label="Carregando visão geral de automações">
        <Skeleton className="automation-overview__welcome-skeleton" />
        <div className="automation-overview__metrics">
          {[0, 1, 2, 3].map((item) => <Skeleton key={item} className="automation-overview__metric-skeleton" />)}
        </div>
        <div className="automation-overview__columns">
          <Skeleton className="automation-overview__panel-skeleton" />
          <Skeleton className="automation-overview__panel-skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="automation-overview">
      {overview.warnings.length > 0 && (
        <FeedbackBanner
          tone="info"
          title="Parte do resumo não pôde ser atualizada"
          message={overview.warnings.join(" ")}
          hint="O restante do módulo continua disponível. Tente atualizar somente este resumo."
          action={{ label: "Atualizar resumo", onClick: overview.reload }}
        />
      )}

      <section className="automation-overview__welcome" aria-labelledby="automation-overview-title">
        <div>
          <span className="automation-overview__eyebrow">Seu ponto de partida</span>
          <h2 id="automation-overview-title">O que você quer fazer agora?</h2>
          <p>Continue um trabalho em andamento ou avance diretamente para o catálogo operacional.</p>
        </div>
        <div className="automation-overview__welcome-actions">
          {canCreateProject && <Link className="ui-button ui-button--primary ui-button--md" to="/automations/build?action=new"><span className="ui-button__content"><PencilLine size={16} aria-hidden="true" />Criar projeto</span></Link>}
          {canUseCatalog && <Link className="ui-button ui-button--secondary ui-button--md" to="/automations/catalog/robots"><span className="ui-button__content">Abrir publicados<ArrowRight size={16} aria-hidden="true" /></span></Link>}
        </div>
      </section>

      <section className="automation-overview__metrics" aria-label="Indicadores do ciclo de automação">
        <article><span><Code2 size={17} aria-hidden="true" /></span><strong>{overview.projects.length}</strong><p>Projetos ativos</p></article>
        <article><span><PencilLine size={17} aria-hidden="true" /></span><strong>{inCheckout}</strong><p>Em edição</p></article>
        <article><span><Boxes size={17} aria-hidden="true" /></span><strong>{overview.robotCount}</strong><p>Robôs na raiz</p></article>
        <article><span><Server size={17} aria-hidden="true" /></span><strong>{overview.availableAgentCount}</strong><p>Dispositivos disponíveis</p></article>
      </section>

      <div className="automation-overview__columns">
        <section className="automation-overview__panel" aria-labelledby="recent-projects-title">
          <div className="automation-overview__panel-header">
            <div><span>Continuidade</span><h3 id="recent-projects-title">Projetos recentes</h3></div>
            {canBuild && <Link to="/automations/build">Ver todos <ArrowRight size={14} aria-hidden="true" /></Link>}
          </div>
          {overview.projects.length > 0 ? (
            <ul className="automation-overview__project-list">
              {overview.projects.slice(0, 4).map((project) => (
                <li key={project.id}>
                  <span className="automation-overview__project-mark" aria-hidden="true" />
                  <div><strong>{project.name}</strong><small>{project.hasCheckout ? "Em edição" : "Disponível"} · {formatUpdatedAt(project.updatedAt)}</small></div>
                  <Link
                    to={`/development/${project.id}/studio`}
                    state={{ projectName: project.name }}
                    aria-label={`Abrir ${project.name} no Studio`}
                  >
                    <ArrowRight size={16} aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={<Code2 />}
              title="Nenhum projeto em andamento"
              description="Inicie uma automação do zero ou a partir de um robô já publicado."
              action={canCreateProject ? <Link className="ui-button ui-button--secondary ui-button--sm" to="/automations/build?action=new"><span className="ui-button__content">Criar primeiro projeto</span></Link> : undefined}
            />
          )}
        </section>

        <section className="automation-overview__panel" aria-labelledby="catalog-access-title">
          <div className="automation-overview__panel-header">
            <div><span>Operação e governança</span><h3 id="catalog-access-title">Catálogo</h3></div>
            <Button variant="ghost" size="sm" busy={overview.refreshing} loadingLabel="Atualizando resumo" onClick={overview.reload} aria-label="Atualizar resumo"><RefreshCw size={15} aria-hidden="true" />Atualizar</Button>
          </div>
          <div className="automation-overview__catalog-links">
            {canUseCatalog && <Link to="/automations/catalog/robots"><span><Boxes size={18} aria-hidden="true" /></span><div><strong>Robôs publicados</strong><small>{overview.folderCount} pastas organizacionais</small></div><ArrowRight size={16} aria-hidden="true" /></Link>}
            {canUseLibraries && <Link to="/automations/catalog/libraries"><span><Blocks size={18} aria-hidden="true" /></span><div><strong>Bibliotecas</strong><small>Versões e dependências compartilhadas</small></div><ArrowRight size={16} aria-hidden="true" /></Link>}
            {!canUseCatalog && !canUseLibraries && <EmptyState icon={<FolderTree />} title="Catálogo não disponível" description="Seu perfil possui acesso somente à construção de automações." />}
          </div>
        </section>
      </div>
    </div>
  );
}
