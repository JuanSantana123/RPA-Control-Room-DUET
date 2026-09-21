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


interface RobotsGridProps {
    robots: Robot[];
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

    onExecuteRobot: (
        robot: Robot
    ) => void;
}


function RobotsGrid({
    robots,
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
    onExecuteRobot,
}: RobotsGridProps) {

    return (
        <div className="selected-robots-content">

            {loadingRobots ? (
                <div className="panel-loading">
                    Carregando robôs...
                </div>
            ) : robots.length === 0 ? (
                <div className="panel-empty-state">

                    <div className="panel-empty-icon">
                        <Package
                            size={22}
                            strokeWidth={1.6}
                        />
                    </div>

                    <h3>Nenhum robô nesta pasta</h3>

                    <p>
                        Faça upload de um pacote para disponibilizar
                        um robô nesta pasta.
                    </p>
                </div>
            ) : (
                <div className="robots-grid">

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