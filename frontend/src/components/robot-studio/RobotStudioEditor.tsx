// ============================================================
// DUET CORE - ROBOT STUDIO - EDITOR
// ============================================================
//
// Responsabilidade:
// - renderizar o Monaco Editor utilizado pelo Robot Studio;
// - apresentar o estado vazio quando nenhum arquivo estiver
//   aberto;
// - respeitar o modo de leitura já calculado pelo Studio.
//
// IMPORTANTE:
// Este componente reproduz a configuração atual do Monaco.
// Nenhuma opção, regra de edição ou comportamento está sendo
// alterado nesta refatoração.
//
// Este componente NÃO deve:
// - carregar arquivos;
// - salvar arquivos;
// - controlar Checkout;
// - executar chamadas HTTP;
// - alterar diretamente o workspace.
//
// O conteúdo e as alterações continuam sendo controlados pelo
// componente proprietário através das propriedades.
// ============================================================

import type {
    CSSProperties,
} from "react";

import Editor
    from "@monaco-editor/react";

import {
    FileCode2,
} from "lucide-react";

import type {
    StudioNode,
} from "../../types/robotStudio";


interface RobotStudioEditorStyles {
    editorArea: CSSProperties;
    editorEmpty: CSSProperties;
}


interface RobotStudioEditorProps {
    activeFile: StudioNode | null;
    canWriteWorkspace: boolean;
    workspaceReadOnlyMessage: string;

    styles: RobotStudioEditorStyles;

    onChange: (
        value: string | undefined
    ) => void;
}


// ============================================================
// LINGUAGEM DO MONACO
// ============================================================
//
// Mantém exatamente o mapeamento existente atualmente no
// RobotStudio.tsx.
// ============================================================

const languageFromFilename = (
    filename: string
): string => {

    const lower =
        filename.toLowerCase();

    if (lower.endsWith(".py")) {
        return "python";
    }

    if (lower.endsWith(".json")) {
        return "json";
    }

    if (
        lower.endsWith(".ts") ||
        lower.endsWith(".tsx")
    ) {
        return "typescript";
    }

    if (
        lower.endsWith(".js") ||
        lower.endsWith(".jsx")
    ) {
        return "javascript";
    }

    if (lower.endsWith(".md")) {
        return "markdown";
    }

    if (lower.endsWith(".css")) {
        return "css";
    }

    if (lower.endsWith(".html")) {
        return "html";
    }

    if (
        lower.endsWith(".yaml") ||
        lower.endsWith(".yml")
    ) {
        return "yaml";
    }

    return "plaintext";
};


function RobotStudioEditor({
    activeFile,
    canWriteWorkspace,
    workspaceReadOnlyMessage,
    styles,
    onChange,
}: RobotStudioEditorProps) {

    return (
        <div style={styles.editorArea}>

            {activeFile &&
            activeFile.type === "file" ? (

                <Editor
                    height="100%"
                    theme="vs-dark"

                    language={
                        languageFromFilename(
                            activeFile.name
                        )
                    }

                    value={
                        activeFile.content || ""
                    }

                    onChange={onChange}

                    options={{
                        // O código somente pode ser alterado
                        // com Development:edit + Checkout próprio.
                        readOnly:
                            !canWriteWorkspace,

                        readOnlyMessage: {
                            value:
                                workspaceReadOnlyMessage,
                        },

                        fontSize: 14,

                        fontFamily:
                            "Consolas, 'Courier New', monospace",

                        minimap: {
                            enabled: true,
                        },

                        automaticLayout: true,

                        scrollBeyondLastLine: false,

                        wordWrap: "off",

                        tabSize: 4,

                        insertSpaces: true,

                        renderWhitespace:
                            "selection",

                        smoothScrolling: true,

                        padding: {
                            top: 12,
                        },
                    }}
                />

            ) : (

                <div style={styles.editorEmpty}>
                    <FileCode2
                        size={34}
                        strokeWidth={1.3}
                    />

                    <h3>
                        Nenhum arquivo aberto
                    </h3>

                    <p>
                        Selecione um arquivo no Explorer para começar a desenvolver.
                    </p>
                </div>
            )}

        </div>
    );
}


export default RobotStudioEditor;