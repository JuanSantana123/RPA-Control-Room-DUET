import { useEffect, useState } from "react";
import api from "../services/api";

// ============================================================
// TIPO - PASTA DE ROBÔS
// ============================================================

interface RobotFolder {
    id: number;
    name: string;
    parent_id: number | null;
}

// ============================================================
// TIPO - ROBÔ
// ============================================================

interface Robot {
    id: number;
    name: string;
    filename: string;
    version: string;
    file_hash: string;
    file_path: string;
}

// ============================================================
// PÁGINA DE ROBÔS
// ============================================================

function Robots() {

    // ========================================================
    // ESTADOS
    // ========================================================

    const [folders, setFolders] = useState<RobotFolder[]>([]);

    const [robots, setRobots] = useState<Robot[]>([]);

    const [selectedFolder, setSelectedFolder] =
        useState<RobotFolder | null>(null);

    // Guarda quais pastas estão abertas na árvore.
    // Cada ID representa uma pasta expandida.
    const [expandedFolders, setExpandedFolders] =
        useState<Set<number>>(new Set());

    const [loadingFolders, setLoadingFolders] = useState(true);

    const [loadingRobots, setLoadingRobots] = useState(false);

    const [error, setError] = useState("");

    // ========================================================
    // ESTADO - UPLOAD
    // ========================================================

    const [uploading, setUploading] = useState(false);

    // ========================================================
    // ESTADO - CRIAÇÃO DE PASTA
    // ========================================================

    // Guarda o nome digitado pelo usuário.
    const [newFolderName, setNewFolderName] = useState("");
    // Guarda a pasta onde a nova pasta será criada.
    // null significa que a pasta será criada na raiz.
    const [newFolderParentId, setNewFolderParentId] =
        useState<number | null>(null);

    // Controla o estado do botão durante a criação.
    const [creatingFolder, setCreatingFolder] = useState(false);

    // ========================================================
    // BUSCAR PASTAS
    // ========================================================

    const carregarPastas = async () => {

        try {

            setLoadingFolders(true);

            const response = await api.get("/robot-folders");

            // Guarda as pastas retornadas pelo backend.
            setFolders(response.data.folders);

        } catch (err) {

            console.error(
                "Erro ao buscar pastas de robôs:",
                err
            );

            setError(
                "Não foi possível carregar as pastas de robôs."
            );

        } finally {

            setLoadingFolders(false);
        }
    };

    // ========================================================
    // CARREGAMENTO INICIAL
    // ========================================================

    useEffect(() => {

        carregarPastas();

    }, []);


    // ========================================================
    // MONTA A ÁRVORE DE PASTAS
    // ========================================================

    // Retorna todas as pastas filhas de uma determinada pasta.
    // A função é recursiva, então não existe limite de níveis.
    const obterSubpastas = (
        parentId: number
    ): RobotFolder[] => {

        return folders.filter(
            (folder) =>
                folder.parent_id === parentId
        );
    };

    // ========================================================
    // ALTERNA EXPANSÃO DA PASTA
    // ========================================================

    // Abre ou fecha uma pasta na árvore.
    const alternarPasta = (folderId: number) => {

        setExpandedFolders((atual) => {

            const novo = new Set(atual);

            if (novo.has(folderId)) {
                novo.delete(folderId);
            } else {
                novo.add(folderId);
            }

            return novo;
        });
    };


    // ========================================================
    // RENDERIZA UMA PASTA DA ÁRVORE
    // ========================================================

    // Renderiza a pasta e, recursivamente, todas as suas
    // subpastas, independentemente da quantidade de níveis.
    const renderizarPasta = (
        folder: RobotFolder,
        nivel: number = 0
    ): React.ReactNode => {

        const subpastas = obterSubpastas(folder.id);

        const expandida = expandedFolders.has(folder.id);

        return (
            <div key={folder.id}>

                {/* Linha da pasta atual */}
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        marginLeft: `${nivel * 24}px`,
                        marginBottom: "4px",
                    }}
                >

                    {/* Abre/fecha somente quando existem subpastas */}
                    {subpastas.length > 0 ? (
                        <button
                            type="button"
                            onClick={() =>
                                alternarPasta(folder.id)
                            }
                            style={{
                                width: "28px",
                                padding: "4px",
                                cursor: "pointer",
                            }}
                        >
                            {expandida ? "▼" : "▶"}
                        </button>
                    ) : (
                        <span
                            style={{
                                width: "28px",
                                textAlign: "center",
                            }}
                        >
                            •
                        </span>
                    )}

                    {/* Seleciona a pasta */}
                    <button
                        type="button"
                        onClick={() =>
                            carregarRobos(folder)
                        }
                        style={{
                            padding: "7px 12px",
                            cursor: "pointer",
                            textAlign: "left",
                        }}
                    >
                        📁 {folder.name}
                    </button>

                    {/* Exclui a pasta */}
                    <button
                        type="button"
                        onClick={() =>
                            excluirPasta(folder)
                        }
                        style={{
                            padding: "7px 10px",
                            cursor: "pointer",
                        }}
                    >
                        Excluir
                    </button>

                </div>

                {/* Renderiza as subpastas somente quando
                    a pasta estiver expandida. */}
                {expandida && (
                    <div>
                        {subpastas.map((subpasta) =>
                            renderizarPasta(
                                subpasta,
                                nivel + 1
                            )
                        )}
                    </div>
                )}

            </div>
        );
    };
    // ========================================================
    // CRIAR PASTA
    // ========================================================

    const criarPasta = async () => {

        // Remove espaços desnecessários antes de enviar.
        const nome = newFolderName.trim();

        // Não permite criar pasta sem nome.
        if (!nome) {

            setError("Informe um nome para a pasta.");

            return;
        }

        try {

            setCreatingFolder(true);

            setError("");

            // ========================================================
            // CRIA A PASTA NO CONTROL ROOM
            // ========================================================

            // O backend recebe:
            //
            // POST /robot-folders
            //
            // {
            //     "name": "Nome da pasta",
            //     "parent_id": null
            // }
            //
            // Como ainda não estamos trabalhando com subpastas,
            // parent_id será null.

            const response = await api.post(
                "/robot-folders",
                {
                    name: nome,
                    parent_id: newFolderParentId
                }
            );

            console.log(
                "Pasta criada com sucesso:",
                response.data
            );

            // Limpa o campo depois da criação.
            setNewFolderName("");

            // Atualiza a lista de pastas.
            await carregarPastas();

        } catch (err) {

            console.error(
                "Erro ao criar pasta:",
                err
            );

            setError(
                "Não foi possível criar a pasta."
            );

        } finally {

            setCreatingFolder(false);
        }
    };

    

    // ========================================================
    // BUSCAR ROBÔS DA PASTA
    // ========================================================

    const carregarRobos = async (folder: RobotFolder) => {

        // Guarda qual pasta está selecionada.
        setSelectedFolder(folder);

        // Limpa os robôs exibidos anteriormente.
        setRobots([]);

        // Ativa o carregamento.
        setLoadingRobots(true);

        // Limpa eventual erro anterior.
        setError("");

        try {

            const response = await api.get(
                `/robot-folders/${folder.id}/robots`
            );

            // Guarda os robôs da pasta selecionada.
            setRobots(response.data.robots);

        } catch (err) {

            console.error(
                "Erro ao buscar robôs da pasta:",
                err
            );

            setError(
                "Não foi possível carregar os robôs desta pasta."
            );

        } finally {

            setLoadingRobots(false);
        }
    };

    

    
    // ============================================================
    // UPLOAD DE ROBÔ
    // ============================================================

    const enviarRobo = async (file: File) => {
        console.log("enviarRobo foi chamado", file.name);
        // O robô obrigatoriamente precisa pertencer
        // a uma pasta antes de ser enviado.
        console.log("PASTA SELECIONADA:", selectedFolder);
        if (!selectedFolder) {

            setError(
                "Selecione uma pasta antes de enviar o robô."
            );

            return;
        }

        setUploading(true);

        setError("");

        try {

            // ========================================================
            // FORM DATA
            // ========================================================

            const formData = new FormData();

            // Adiciona o arquivo selecionado.
            formData.append("file", file);

            // Se existe uma pasta selecionada,
            // envia o ID dela.
            if (selectedFolder) {

                formData.append(
                    "folder_id",
                    String(selectedFolder.id)
                );
            }

            // ========================================================
            // ENVIO PARA O CONTROL ROOM
            // ========================================================

            const response = await api.post(
                "/robots/upload",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            console.log(
                "Upload realizado com sucesso:",
                response.data
            );

            // ========================================================
            // ATUALIZA A LISTA
            // ========================================================

            if (selectedFolder) {

                await carregarRobos(selectedFolder);
            }

        } catch (err) {

            console.error(
                "Erro ao fazer upload do robô:",
                err
            );

            setError(
                "Não foi possível fazer o upload do robô."
            );

        } finally {

            setUploading(false);
        }
    };

    // ============================================================
    // EXCLUIR ROBÔ
    // ============================================================

    const excluirRobo = async (robot: Robot) => {

        const confirmar = window.confirm(
            `Deseja realmente excluir o robô "${robot.name}"?`
        );

        if (!confirmar) {
            return;
        }

        try {

            const response = await api.delete(
                `/robots/${robot.id}`
            );

            console.log(
                "Robô excluído:",
                response.data
            );

            // Recarrega os robôs da pasta atual.
            if (selectedFolder) {

                await carregarRobos(selectedFolder);
            }

        } catch (err) {

            console.error(
                "Erro ao excluir robô:",
                err
            );

            setError(
                "Não foi possível excluir o robô."
            );
        }
    };

    // ============================================================
    // EXCLUIR PASTA
    // ============================================================

    const excluirPasta = async (folder: RobotFolder) => {

        // Pede confirmação antes de excluir.
        const confirmar = window.confirm(
            `Deseja realmente excluir a pasta "${folder.name}"?`
        );

        // Se o usuário cancelar, não faz nada.
        if (!confirmar) {
            return;
        }

        try {

            setError("");

            // Chama o endpoint do Control Room:
            //
            // DELETE /robot-folders/{folder_id}
            await api.delete(
                `/robot-folders/${folder.id}`
            );

            // Se a pasta excluída estava selecionada,
            // limpa a seleção e os robôs exibidos.
            if (selectedFolder?.id === folder.id) {

                setSelectedFolder(null);
                setRobots([]);
            }

            // Atualiza a lista de pastas.
            await carregarPastas();

        } catch (err) {

            console.error(
                "Erro ao excluir pasta:",
                err
            );

            setError(
                "Não foi possível excluir a pasta."
            );
        }
    };



    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <div>

            {/* ====================================================
                TÍTULO
                ==================================================== */}

            <h1>
                Robôs
            </h1>

            {/* ====================================================
                ERRO
                ==================================================== */}

            {error && (
                <div
                    style={{
                        padding: "10px",
                        marginBottom: "15px",
                        border: "1px solid red",
                        borderRadius: "5px",
                    }}
                >
                    {error}
                </div>
            )}

            {/* ====================================================
                CRIAR PASTA
                ==================================================== */}

            <section>

                <h2>
                    Criar Pasta
                </h2>

                {/* Campo onde o usuário informa o nome da pasta. */}
                <input
                    type="text"
                    placeholder="Nome da pasta"
                    value={newFolderName}
                    disabled={creatingFolder}
                    onChange={(event) => {
                        setNewFolderName(event.target.value);
                    }}
                    onKeyDown={(event) => {

                        // Permite criar a pasta pressionando Enter.
                        if (event.key === "Enter") {
                            criarPasta();
                        }
                    }}
                />
                {/* Seleciona a pasta pai da nova pasta.
                    "Raiz" significa que a pasta ficará no nível principal. */}
                <select
                    value={newFolderParentId ?? ""}
                    disabled={creatingFolder}
                    onChange={(event) => {
                        const value = event.target.value;

                        setNewFolderParentId(
                            value === "" ? null : Number(value)
                        );
                    }}
                >
                    <option value="">
                        Pasta raiz
                    </option>

                    {folders.map((folder) => (
                        <option
                            key={folder.id}
                            value={folder.id}
                        >
                            {folder.name}
                        </option>
                    ))}
                </select>
                {/* Botão responsável por chamar POST /robot-folders. */}
                <button
                    onClick={criarPasta}
                    disabled={
                        creatingFolder ||
                        !newFolderName.trim()
                    }
                >
                    {creatingFolder
                        ? "Criando..."
                        : "Criar pasta"}
                </button>

            </section>

            {/* ====================================================
                UPLOAD DE ROBÔ
                ==================================================== */}

            <section>

                <h2>
                    Upload de Robô
                </h2>

                <input
                    type="file"
                    accept=".zip,.rar"
                    disabled={uploading}
                    onChange={(event) => {

                        const file =
                            event.target.files?.[0];

                        if (!file) {
                            return;
                        }
                        console.log("INPUT DE ARQUIVO FUNCIONOU", file.name);
                        enviarRobo(file);

                        // Permite selecionar novamente
                        // o mesmo arquivo posteriormente.
                        event.target.value = "";

                    }}
                />

                {uploading && (
                    <p>
                        Enviando robô...
                    </p>
                )}

            </section>

            {/* ====================================================
                PASTAS
                ==================================================== */}

            <section>

                <h2>
                    Pastas
                </h2>

                {loadingFolders ? (

                    <p>
                        Carregando pastas...
                    </p>

                ) : folders.length === 0 ? (

                    <p>
                        Nenhuma pasta cadastrada.
                    </p>

                ) : (

                    <div>

                        {/* Mostra somente as pastas da raiz.
                        As subpastas serão renderizadas recursivamente
                        pela função renderizarPasta(). */}
                    {folders
                        .filter(
                            (folder) =>
                                folder.parent_id === null
                        )
                        .map((folder) =>
                            renderizarPasta(folder)
                        )}

                    </div>
                )}

            </section>

            {/* ====================================================
                ROBÔS DA PASTA SELECIONADA
                ==================================================== */}

            {selectedFolder && (

                <section>

                    <h2>
                        Robôs — {selectedFolder.name}
                    </h2>

                    {loadingRobots ? (

                        <p>
                            Carregando robôs...
                        </p>

                    ) : robots.length === 0 ? (

                        <p>
                            Nenhum robô nesta pasta.
                        </p>

                    ) : (

                        <div>

                            {robots.map((robot) => (

                                <div key={robot.id}>

                                    {/* Nome do robô. */}
                                    <h3>
                                        {robot.name}
                                    </h3>

                                    {/* Arquivo utilizado pelo robô. */}
                                    <p>
                                        <strong>
                                            Arquivo:
                                        </strong>{" "}
                                        {robot.filename}
                                    </p>

                                    {/* Versão atual do robô. */}
                                    <p>
                                        <strong>
                                            Versão:
                                        </strong>{" "}
                                        {robot.version}
                                    </p>

                                    {/* Botão para excluir o robô. */}
                                    <button
                                        onClick={() =>
                                            excluirRobo(robot)
                                        }
                                    >
                                        Excluir
                                    </button>

                                </div>

                            ))}

                        </div>
                    )}

                </section>
            )}

        </div>
    );
}

export default Robots;