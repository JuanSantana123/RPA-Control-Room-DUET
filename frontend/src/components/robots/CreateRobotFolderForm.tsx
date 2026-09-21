// ============================================================
// DUET CORE - ROBOTS - CREATE FOLDER FORM
// ============================================================
//
// Responsabilidade:
// - renderizar o formulário visual utilizado para criar uma
//   pasta raiz ou uma subpasta de Robots;
// - apresentar o contexto da pasta pai;
// - encaminhar alterações e solicitação de criação por
//   callbacks.
//
// Este componente NÃO:
// - cria a pasta no backend;
// - carrega a árvore;
// - altera diretamente a seleção;
// - contém chamadas HTTP.
//
// Estados e operações permanecem controlados externamente.
//
// Integrações:
// - página Robots;
// - futuro hook useRobotFolders;
// - tipo RobotFolder.
// ============================================================

import {
    FolderPlus,
    Plus,
} from "lucide-react";

import type {
    RobotFolder,
} from "../../types/robots";


interface CreateRobotFolderFormProps {
    folders: RobotFolder[];

    newFolderName: string;
    newFolderParentId: number | null;

    creatingFolder: boolean;

    onFolderNameChange: (
        value: string
    ) => void;

    onCreateFolder: () => void;
}


function CreateRobotFolderForm({
    folders,
    newFolderName,
    newFolderParentId,
    creatingFolder,
    onFolderNameChange,
    onCreateFolder,
}: CreateRobotFolderFormProps) {

    // --------------------------------------------------------
    // Localiza apenas o nome da pasta pai para apresentação.
    // Nenhuma regra de criação é executada aqui.
    // --------------------------------------------------------

    const parentFolder =
        newFolderParentId !== null
            ? folders.find(
                (folder) =>
                    folder.id === newFolderParentId
            )
            : null;


    return (
        <section className="content-panel">
            <div className="content-panel-header">

                <div className="section-icon">
                    <FolderPlus
                        size={18}
                        strokeWidth={1.8}
                    />
                </div>

                <div>
                    <h2>
                        {newFolderParentId !== null
                            ? "Criar subpasta"
                            : "Nova pasta"}
                    </h2>

                    <p>
                        {newFolderParentId !== null
                            ? "A nova pasta será criada dentro da pasta selecionada."
                            : "Crie uma pasta raiz para organizar seus robôs."}
                    </p>
                </div>
            </div>


            <div className="robot-form">
                <div className="form-field">

                    <label htmlFor="new-folder-name">
                        Nome da pasta
                    </label>

                    <input
                        id="new-folder-name"
                        type="text"
                        placeholder="Ex.: Financeiro"
                        value={newFolderName}
                        disabled={creatingFolder}
                        onChange={(event) => {
                            onFolderNameChange(
                                event.target.value
                            );
                        }}
                        onKeyDown={(event) => {
                            // Preserva a criação pelo Enter
                            // existente no formulário original.
                            if (event.key === "Enter") {
                                onCreateFolder();
                            }
                        }}
                    />
                </div>


                {/* Contexto exibido somente para subpastas. */}
                {newFolderParentId !== null && (
                    <div className="folder-parent-context">

                        <span className="folder-parent-context-label">
                            Pasta pai
                        </span>

                        <strong>
                            {parentFolder?.name ||
                                "Pasta selecionada"}
                        </strong>
                    </div>
                )}


                <button
                    type="button"
                    className="primary-button"
                    onClick={onCreateFolder}
                    disabled={
                        creatingFolder ||
                        !newFolderName.trim()
                    }
                >
                    <Plus
                        size={16}
                        strokeWidth={2}
                    />

                    {creatingFolder
                        ? "Criando..."
                        : "Criar pasta"}
                </button>
            </div>
        </section>
    );
}


export default CreateRobotFolderForm;