// ============================================================
// DUET CORE - ROBOTS - ROBOT CARD
// ============================================================
//
// Responsabilidade:
// - renderizar um Robot publicado;
// - apresentar nome, arquivo e versão;
// - apresentar o menu contextual do Robot;
// - permitir abrir/fechar o snapshot de Libraries;
// - disponibilizar visualmente as ações Nova versão e Executar.
//
// Este componente NÃO:
// - realiza download diretamente;
// - exclui Robots diretamente;
// - executa Robots diretamente;
// - cria AutomationProjects;
// - consulta Libraries;
// - contém chamadas HTTP.
//
// Todas as operações são recebidas por callbacks.
//
// Integrações:
// - RobotsGrid;
// - RobotLibrariesSnapshot;
// - tipos Robot e RobotLibraryDependency.
//
// IMPORTANTE:
// A estrutura e as ações correspondem ao card existente
// atualmente no Robots.tsx.
// ============================================================

import {
    ChevronDown,
    ChevronRight,
    CirclePlay,
    Code2,
    Download,
    MoreVertical,
    Package,
    Trash2,
} from "lucide-react";

import type {
    Robot,
    RobotLibraryDependency,
} from "../../types/robots";

import RobotLibrariesSnapshot from "./RobotLibrariesSnapshot";


interface RobotCardProps {
    robot: Robot;

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


function RobotCard({
    robot,
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
}: RobotCardProps) {

    const libraries =
        robotLibraries[robot.id] || [];

    const librariesExpanded =
        expandedRobotLibraries === robot.id;

    const librariesLoading =
        loadingRobotLibraries === robot.id;


    return (
        <article className="robot-card">

            <div className="robot-card-top">
                <div className="robot-card-icon">
                    <Package
                        size={20}
                        strokeWidth={1.7}
                    />
                </div>


                {/* Botão que abre o menu contextual do Robot. */}
                <button
                    type="button"
                    className="robot-card-menu"
                    title="Opções do robô"
                    aria-label="Opções do robô"
                    onClick={(event) => {
                        event.stopPropagation();

                        onSetOpenRobotMenu(
                            openRobotMenu === robot.id
                                ? null
                                : robot.id
                        );
                    }}
                >
                    <MoreVertical
                        size={17}
                        strokeWidth={1.8}
                    />
                </button>


                {/* Menu contextual do Robot. */}
                {openRobotMenu === robot.id && (
                    <div className="robot-card-context-menu">

                        {/* Baixa o arquivo da versão atual. */}
                        <button
                            type="button"
                            onClick={(event) => {
                                event.stopPropagation();

                                onDownloadRobot(robot);
                            }}
                        >
                            <Download
                                size={15}
                                strokeWidth={1.8}
                            />

                            <span>
                                Baixar versão atual
                            </span>
                        </button>


                        {/* Solicita a exclusão do Robot. */}
                        <button
                            type="button"
                            className="robot-card-context-danger"
                            onClick={(event) => {
                                event.stopPropagation();

                                // Preserva o comportamento atual:
                                // fecha o menu antes da confirmação.
                                onSetOpenRobotMenu(null);

                                onDeleteRobot(robot);
                            }}
                        >
                            <Trash2
                                size={15}
                                strokeWidth={1.8}
                            />

                            <span>Excluir</span>
                        </button>
                    </div>
                )}
            </div>


            <div className="robot-card-body">
                <h3>{robot.name}</h3>

                <p className="robot-filename">
                    {robot.filename}
                </p>

                <div className="robot-card-meta">
                    <span>Versão</span>

                    <strong>
                        {robot.version}
                    </strong>
                </div>
            </div>


            {/* ====================================================
                BIBLIOTECAS DO RELEASE

                O clique abre/consulta o snapshot exato das
                Libraries utilizadas por esta versão do Robot.
            ==================================================== */}

            <button
                type="button"
                className="robot-card-libraries-button"
                onClick={() =>
                    onToggleLibraries(robot)
                }
            >
                <span>
                    Bibliotecas
                </span>

                <strong>
                    {librariesLoading
                        ? "..."
                        : loadedRobotLibraries.has(robot.id)
                            ? libraries.length
                            : "Ver"}
                </strong>

                {librariesExpanded ? (
                    <ChevronDown
                        size={15}
                        strokeWidth={1.8}
                    />
                ) : (
                    <ChevronRight
                        size={15}
                        strokeWidth={1.8}
                    />
                )}
            </button>


            {/* Snapshot das Libraries do Release. */}
            {librariesExpanded && (
                <RobotLibrariesSnapshot
                    libraries={libraries}
                    loading={librariesLoading}
                />
            )}


            <div className="robot-card-actions">

                {/* Cria uma nova versão editável a partir do Robot. */}
                <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                        onCreateNewVersion(robot)
                    }
                >
                    <Code2
                        size={15}
                        strokeWidth={1.9}
                    />

                    Nova versão
                </button>


                {/* Executa o Robot no Agent selecionado. */}
                <button
                    type="button"
                    className="secondary-button"
                    onClick={() =>
                        onExecuteRobot(robot)
                    }
                    disabled={
                        !selectedExecutionAgent ||
                        executingRobotId === robot.id
                    }
                >
                    <CirclePlay
                        size={15}
                        strokeWidth={1.9}
                    />

                    {executingRobotId === robot.id
                        ? "Executando..."
                        : "Executar"}
                </button>
            </div>
        </article>
    );
}


export default RobotCard;