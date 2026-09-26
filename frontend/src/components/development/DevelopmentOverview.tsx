import { CircleDotDashed, GitBranch, MessagesSquare, UsersRound } from "lucide-react";
import type { DevelopmentProject, DevelopmentStage } from "../../types/development";

interface DevelopmentOverviewProps {
  projects: DevelopmentProject[];
  stages: DevelopmentStage[];
}

export default function DevelopmentOverview({ projects, stages }: DevelopmentOverviewProps) {
  const inCheckout = projects.filter((project) => project.checkout).length;
  const planned = projects.filter((project) => project.due_date || project.effort_hours).length;
  const comments = projects.reduce((total, project) => total + (project.comments_count || 0), 0);

  const metrics = [
    { label: "Projetos ativos", value: projects.length, icon: CircleDotDashed },
    { label: "Etapas do workflow", value: stages.length, icon: GitBranch },
    { label: "Em edição", value: inCheckout, icon: UsersRound },
    { label: "Comentários", value: comments, icon: MessagesSquare },
  ];

  return (
    <section className="development-overview" aria-label="Resumo do desenvolvimento">
      <div className="development-overview__intro">
        <small>Capacidade de entrega</small>
        <strong>{planned} de {projects.length} projetos possuem planejamento</strong>
        <span>Acompanhe demanda, edição, workflow e colaboração em uma única visão.</span>
      </div>
      <div className="development-overview__metrics">
        {metrics.map(({ label, value, icon: Icon }) => (
          <div className="development-overview__metric" key={label}>
            <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
