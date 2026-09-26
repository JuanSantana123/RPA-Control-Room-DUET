import { Boxes, FolderTree, PackageCheck, Server } from "lucide-react";

interface RobotsOverviewProps {
  folderCount: number;
  robotCount: number;
  availableAgentCount: number;
  selectedLocation: string;
}

const metrics = [
  { key: "robots", label: "Robôs nesta localização", icon: PackageCheck },
  { key: "folders", label: "Pastas organizacionais", icon: FolderTree },
  { key: "agents", label: "Dispositivos disponíveis", icon: Server },
] as const;

export default function RobotsOverview({ folderCount, robotCount, availableAgentCount, selectedLocation }: RobotsOverviewProps) {
  const values = { robots: robotCount, folders: folderCount, agents: availableAgentCount };

  return (
    <section className="robots-overview" aria-label="Resumo do catálogo de automações">
      <div className="robots-overview__context">
        <span className="robots-overview__icon"><Boxes size={18} aria-hidden="true" /></span>
        <div>
          <small>Localização atual</small>
          <strong>{selectedLocation}</strong>
        </div>
      </div>
      <div className="robots-overview__metrics">
        {metrics.map(({ key, label, icon: Icon }) => (
          <div className="robots-overview__metric" key={key}>
            <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
            <strong>{values[key]}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
