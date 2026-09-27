// ============================================================
// DUET CORE - ROBOTS - ROBOTS GRID
// ============================================================
//
// Responsabilidade:
// - renderizar a coleção de Robots da localização selecionada;
// - controlar somente os estados visuais de carregamento,
//   lista vazia e grid;
// - delegar cada Robot individual ao RobotCard.
//
// Este componente NÃO:
// - busca Robots;
// - altera pastas;
// - executa chamadas HTTP;
// - controla regras de Libraries;
// - executa automações.
//
// Dados e operações chegam por propriedades.
//
// Integrações:
// - RobotCard;
// - tipos Robot e RobotLibraryDependency;
// - página Robots / futuros hooks da área.
// ============================================================

import { Package } from "lucide-react";

import type {
    Robot,
    RobotLibraryDependency,
} from "../../types/robots";

import RobotCard from "./RobotCard";
import { CardGridSkeleton } from "../ui/Skeletons";
import { Button } from "../ui/Button";
import EmptyState from "../ui/EmptyState";


interface RobotsGridProps {
    robots: Robot[];
    totalRobotCount: number;
    viewMode: "grid" | "list";
    hasActiveFilter: boolean;
    loadingRobots: boolean;

    openRobotMenu: number | null;
    expandedRobotLibraries: number | null;
    loadingRobotLibraries: number | null;

    robotLibraries: Record<
        number,
        RobotLibraryDependency[]
    >;

    loadedRobotLibraries: Set<number>;

    selectedExecutionAgent: string;
    executingRobotId: number | null;

    onSetOpenRobotMenu: (
        robotId: number | null
    ) => void;

    onDownloadRobot: (
        robot: Robot
    ) => void;

    onDeleteRobot: (
        robot: Robot
    ) => void;

    onToggleLibraries: (
        robot: Robot
    ) => void;

    onCreateNewVersion: (
        robot: Robot
    ) => void;

    onOpenVersions: (
        robot: Robot
    ) => void;

    onExecuteRobot: (
        robot: Robot
    ) => void;

    onClearFilter: () => void;
}


function RobotsGrid({
    robots,
    totalRobotCount,
    viewMode,
    hasActiveFilter,
    loadingRobots,
    openRobotMenu,
    expandedRobotLibraries,
    loadingRobotLibraries,
    robotLibraries,
    loadedRobotLibraries,
    selectedExecutionAgent,
    executingRobotId,
    onSetOpenRobotMenu,
    onDownloadRobot,
    onDeleteRobot,
    onToggleLibraries,
    onCreateNewVersion,
    onOpenVersions,
    onExecuteRobot,
    onClearFilter,
}: RobotsGridProps) {

    return (
        <div className="selected-robots-content">

            {loadingRobots ? (
                <CardGridSkeleton count={3} />
            ) : robots.length === 0 ? (
                <EmptyState
                    icon={<Package />}
                    title={hasActiveFilter && totalRobotCount > 0 ? "Nenhum resultado encontrado" : "Nenhum robô nesta pasta"}
                    description={hasActiveFilter && totalRobotCount > 0
                        ? "Ajuste o termo de pesquisa ou a ordenação para localizar outra automação."
                        : "Envie um pacote para disponibilizar uma automação nesta localização."}
                    action={hasActiveFilter && totalRobotCount > 0 ? (
                        <Button size="sm" onClick={onClearFilter}>Limpar pesquisa</Button>
                    ) : undefined}
                />
            ) : (
                <div className={`robots-grid robots-grid--${viewMode}`}>

                    {robots.map((robot) => (
                        <RobotCard
                            key={robot.id}
                            robot={robot}
                            openRobotMenu={openRobotMenu}
                            expandedRobotLibraries={
                                expandedRobotLibraries
                            }
                            loadingRobotLibraries={
                                loadingRobotLibraries
                            }
                            robotLibraries={robotLibraries}
                            loadedRobotLibraries={
                                loadedRobotLibraries
                            }
                            selectedExecutionAgent={
                                selectedExecutionAgent
                            }
                            executingRobotId={
                                executingRobotId
                            }
                            onSetOpenRobotMenu={
                                onSetOpenRobotMenu
                            }
                            onDownloadRobot={
                                onDownloadRobot
                            }
                            onDeleteRobot={
                                onDeleteRobot
                            }
                            onToggleLibraries={
                                onToggleLibraries
                            }
                            onCreateNewVersion={
                                onCreateNewVersion
                            }
                            onOpenVersions={onOpenVersions}
                            onExecuteRobot={
                                onExecuteRobot
                            }
                        />
                    ))}
                </div>
            )}
        </div>
    );
}


export default RobotsGrid;
