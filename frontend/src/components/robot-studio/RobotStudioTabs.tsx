// ============================================================
// DUET CORE - ROBOT STUDIO - TABS
// ============================================================
//
// Responsabilidade:
// - renderizar as abas de arquivos abertas no Robot Studio;
// - indicar a aba ativa;
// - indicar arquivos com alterações não salvas;
// - permitir selecionar e fechar abas.
//
// IMPORTANTE:
// Este componente faz parte de uma refatoração estrutural.
// Nenhuma regra funcional existente deve ser alterada.
//
// Este componente NÃO deve:
// - carregar arquivos;
// - salvar arquivos;
// - alterar o workspace;
// - executar chamadas HTTP.
//
// Toda ação continua sendo delegada ao Robot Studio.
// ============================================================

import type {
    CSSProperties,
    ReactNode,
} from "react";

import {
    FileCode2,
    FileJson,
    X,
} from "lucide-react";

import type {
    OpenTab,
} from "../../types/robotStudio";


interface RobotStudioTabsStyles {
    tabs: CSSProperties;
    tab: CSSProperties;
    tabMain: CSSProperties;
    dirtyDot: CSSProperties;
    tabClose: CSSProperties;
}


interface RobotStudioTabsProps {
    openTabs: OpenTab[];
    activeFileId: string;
    dirtyFiles: Set<string>;

    styles: RobotStudioTabsStyles;

    onSelectTab: (
        fileId: string
    ) => void;

    onCloseTab: (
        fileId: string
    ) => void;
}


// Mantém a mesma regra visual atualmente existente
// no helper fileIcon do RobotStudio.tsx.
const fileIcon = (
    filename: string,
    size = 15
): ReactNode => {

    if (
        filename
            .toLowerCase()
            .endsWith(".json")
    ) {
        return (
            <FileJson
                size={size}
                strokeWidth={1.7}
            />
        );
    }

    return (
        <FileCode2
            size={size}
            strokeWidth={1.7}
        />
    );
};


function RobotStudioTabs({
    openTabs,
    activeFileId,
    dirtyFiles,
    styles,
    onSelectTab,
    onCloseTab,
}: RobotStudioTabsProps) {

    return (
        <div style={styles.tabs}>
            {openTabs.map((tab) => {

                const active =
                    tab.id === activeFileId;

                return (
                    <div
                        key={tab.id}
                        style={{
                            ...styles.tab,

                            background:
                                active
                                    ? "#1e1e1e"
                                    : "#2d2d30",

                            borderTop:
                                active
                                    ? "1px solid #4c8bf5"
                                    : "1px solid transparent",
                        }}
                    >

                        <button
                            type="button"
                            onClick={() =>
                                onSelectTab(
                                    tab.id
                                )
                            }
                            style={styles.tabMain}
                        >
                            {fileIcon(
                                tab.name,
                                14
                            )}

                            <span>
                                {tab.name}
                            </span>

                            {dirtyFiles.has(tab.id) && (
                                <span style={styles.dirtyDot}>
                                    ●
                                </span>
                            )}
                        </button>


                        <button
                            type="button"
                            onClick={() =>
                                onCloseTab(
                                    tab.id
                                )
                            }
                            style={styles.tabClose}
                            title="Fechar"
                            aria-label={`Fechar ${tab.name}`}
                        >
                            <X size={13} />
                        </button>

                    </div>
                );
            })}
        </div>
    );
}


export default RobotStudioTabs;