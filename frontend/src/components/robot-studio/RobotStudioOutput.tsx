// ============================================================
// DUET CORE - ROBOT STUDIO - OUTPUT
// ============================================================
//
// Responsabilidade:
// - renderizar o painel OUTPUT do Robot Studio;
// - apresentar as mensagens já produzidas pelo Studio;
// - permitir recolher e reabrir visualmente o painel.
//
// IMPORTANTE:
// Nenhuma lógica responsável por produzir mensagens é movida
// para este componente.
//
// Este componente NÃO deve:
// - executar comandos;
// - executar chamadas HTTP;
// - interpretar mensagens;
// - controlar processos;
// - alterar estado do workspace.
//
// O componente apenas apresenta outputLines e comunica a
// abertura/fechamento através de callbacks.
// ============================================================

import type {
    CSSProperties,
} from "react";

import {
    Terminal,
    X,
} from "lucide-react";


interface RobotStudioOutputStyles {
    output: CSSProperties;
    outputHeader: CSSProperties;
    outputTitle: CSSProperties;
    smallIconButton: CSSProperties;
    outputBody: CSSProperties;
    outputCollapsed: CSSProperties;
}


interface RobotStudioOutputProps {
    showOutput: boolean;
    outputLines: string[];

    styles: RobotStudioOutputStyles;

    onShowOutput: () => void;
    onHideOutput: () => void;
}


function RobotStudioOutput({
    showOutput,
    outputLines,
    styles,
    onShowOutput,
    onHideOutput,
}: RobotStudioOutputProps) {

    if (showOutput) {
        return (
            <section style={styles.output}>

                <div style={styles.outputHeader}>

                    <div style={styles.outputTitle}>
                        <Terminal size={15} />
                        OUTPUT
                    </div>

                    <button
                        type="button"
                        onClick={onHideOutput}
                        style={styles.smallIconButton}
                        title="Fechar output"
                    >
                        <X size={14} />
                    </button>

                </div>


                <div style={styles.outputBody}>
                    {outputLines.map(
                        (line, index) => (
                            <div
                                key={`${index}-${line}`}
                            >
                                {line}
                            </div>
                        )
                    )}
                </div>

            </section>
        );
    }


    return (
        <button
            type="button"
            onClick={onShowOutput}
            style={styles.outputCollapsed}
        >
            <Terminal size={14} />
            OUTPUT
        </button>
    );
}


export default RobotStudioOutput;