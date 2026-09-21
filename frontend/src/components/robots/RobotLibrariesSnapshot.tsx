// ============================================================
// DUET CORE - ROBOTS - LIBRARIES SNAPSHOT
// ============================================================
//
// Responsabilidade:
// - renderizar o snapshot de Libraries utilizado por uma
//   versão publicada de um Robot;
// - exibir nome, import_name, versão e situação da versão;
// - representar visualmente o snapshot imutável do Release.
//
// Este componente NÃO:
// - consulta Libraries no backend;
// - altera dependências;
// - escolhe versões;
// - modifica o catálogo global de Libraries;
// - mantém regras de negócio.
//
// Todos os dados são recebidos pelo RobotCard.
//
// Integrações:
// - RobotCard;
// - RobotLibraryDependency.
//
// IMPORTANTE:
// O conteúdo visual abaixo corresponde ao painel atualmente
// existente dentro dos cards da página Robots.
// ============================================================

import type {
    RobotLibraryDependency,
} from "../../types/robots";


interface RobotLibrariesSnapshotProps {
    libraries: RobotLibraryDependency[];
    loading: boolean;
}


function RobotLibrariesSnapshot({
    libraries,
    loading,
}: RobotLibrariesSnapshotProps) {

    return (
        <div className="robot-card-libraries-panel">

            {loading ? (
                <div className="robot-library-loading">
                    Carregando bibliotecas...
                </div>
            ) : (
                <>
                    {libraries.length === 0 ? (
                        <div className="robot-library-empty">
                            Este Release não possui bibliotecas vinculadas.
                        </div>
                    ) : (
                        <div className="robot-library-list">

                            {libraries.map((library) => (
                                <div
                                    key={library.library_id}
                                    className="robot-library-item"
                                >
                                    <div className="robot-library-main">
                                        <strong>
                                            {library.name}
                                        </strong>

                                        <span>
                                            {library.import_name}
                                        </span>
                                    </div>


                                    <div className="robot-library-version">
                                        <strong>
                                            {library.version}
                                        </strong>

                                        <span
                                            className={
                                                library.is_current_production
                                                    ? "robot-library-status-current"
                                                    : "robot-library-status-history"
                                            }
                                        >
                                            {library.is_current_production
                                                ? "Vigente em Produção"
                                                : "Versão histórica"}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}


export default RobotLibrariesSnapshot;