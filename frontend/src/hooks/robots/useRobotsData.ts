// ============================================================
// DUET CORE - ROBOTS - ROBOTS DATA HOOK
// ============================================================
//
// Responsabilidade:
// - armazenar os Robots da localização selecionada;
// - carregar Robots da Raiz de Robôs;
// - carregar Robots de uma pasta;
// - realizar upload de pacote ZIP;
// - excluir Robot;
// - baixar a versão publicada;
// - criar AutomationProject para "Nova versão".
//
// Este hook NÃO:
// - renderiza componentes;
// - gerencia a árvore visual de pastas;
// - executa Robots em Agents;
// - consulta snapshots de Libraries.
//
// Integrações:
// - GET    /robots/root
// - GET    /robot-folders/{folder_id}/robots
// - POST   /robots/upload
// - DELETE /robots/{robot_id}
// - GET    /robots/{robot_id}/download
// - POST   /development/projects
//
// IMPORTANTE:
// A Raiz de Robôs permanece lógica e representa Robots cujo
// folder_id é NULL.
//
// A lógica foi extraída do Robots.tsx preservando o fluxo
// existente da aplicação.
// ============================================================

import {
    useRef,
    useState,
} from "react";

import {
    useNavigate,
} from "react-router-dom";

import api from "../../services/api";

import type {
    Robot,
    RobotFolder,
} from "../../types/robots";

import {
    obterMensagemErro,
} from "../../utils/robotErrors";


interface UseRobotsDataParams {

    // Pastas disponíveis são necessárias para atualizar a
    // pasta correta após um upload contextual.
    folders: RobotFolder[];

    // Localização atualmente selecionada.
    selectedFolder: RobotFolder | null;
    rootSelected: boolean;

    // Permitem manter a seleção sincronizada com o carregamento
    // de Robots, exatamente como acontecia no Robots.tsx.
    setSelectedFolder: React.Dispatch<
        React.SetStateAction<RobotFolder | null>
    >;

    setRootSelected: React.Dispatch<
        React.SetStateAction<boolean>
    >;

    // Mensagens continuam centralizadas na página.
    setError: React.Dispatch<
        React.SetStateAction<string>
    >;

    setSuccess: React.Dispatch<
        React.SetStateAction<string>
    >;
}


export function useRobotsData({
    folders,
    selectedFolder,
    rootSelected,
    setSelectedFolder,
    setRootSelected,
    setError,
    setSuccess,
}: UseRobotsDataParams) {

    const navigate =
        useNavigate();


    // ========================================================
    // ESTADOS - ROBOTS
    // ========================================================

    const [
        robots,
        setRobots,
    ] = useState<Robot[]>([]);


    const [
        loadingRobots,
        setLoadingRobots,
    ] = useState<boolean>(
        false
    );


    // ========================================================
    // ESTADO - MENU DO ROBOT
    // ========================================================

    const [
        openRobotMenu,
        setOpenRobotMenu,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // ESTADOS - UPLOAD
    // ========================================================

    // O valor não é utilizado visualmente na página original,
    // mas o estado continua sendo mantido durante o fluxo.
    const [
        uploading,
        setUploading,
    ] = useState<boolean>(
        false
    );


    // Pasta escolhida pelo menu contextual.
    const [
        uploadTargetFolderId,
        setUploadTargetFolderId,
    ] = useState<number | null>(
        null
    );


    // Input oculto de seleção do ZIP.
    const uploadInputRef =
        useRef<HTMLInputElement | null>(
            null
        );


    // ========================================================
    // CARREGAR ROBOTS DA RAIZ
    // ========================================================

    const carregarRobosRaiz =
        async () => {

            // Mantém a seleção existente no fluxo original.
            setRootSelected(true);

            setSelectedFolder(null);


            // Limpa a grade anterior antes da requisição.
            setRobots([]);

            setLoadingRobots(true);

            setError("");


            try {

                const response =
                    await api.get(
                        "/robots/root"
                    );


                setRobots(
                    response.data.robots ||
                    []
                );

            } catch (err) {

                console.error(
                    "Erro ao buscar robôs da raiz:",
                    err
                );


                setError(
                    "Não foi possível carregar os robôs da Raiz de Robôs."
                );

            } finally {

                setLoadingRobots(false);
            }
        };


    // ========================================================
    // CARREGAR ROBOTS DE UMA PASTA
    // ========================================================

    const carregarRobos = async (
        folder: RobotFolder
    ) => {

        // Mantém a seleção sincronizada com a pasta carregada.
        setRootSelected(false);

        setSelectedFolder(folder);


        setRobots([]);

        setLoadingRobots(true);

        setError("");


        try {

            const response =
                await api.get(
                    `/robot-folders/${folder.id}/robots`
                );


            setRobots(
                response.data.robots
            );

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


    // ========================================================
    // ATUALIZAR ROBOTS DA LOCALIZAÇÃO ATUAL
    // ========================================================

    const atualizarRobosAtuais =
        async () => {

            if (rootSelected) {

                await carregarRobosRaiz();

            } else if (selectedFolder) {

                await carregarRobos(
                    selectedFolder
                );
            }
        };


    // ========================================================
    // ABRIR UPLOAD PARA UMA PASTA
    // ========================================================

    const abrirUploadParaPasta = (
        folderId: number
    ) => {

        // Guarda a pasta que receberá o ZIP.
        setUploadTargetFolderId(
            folderId
        );


        // Abre o input invisível.
        uploadInputRef.current?.click();
    };


    // ========================================================
    // UPLOAD DE ROBOT
    // ========================================================

    const enviarRobo = async (
        file: File,
        folderId: number
    ) => {

        console.log(
            "enviarRobo foi chamado:",
            file.name
        );

        console.log(
            "PASTA DE DESTINO:",
            folderId
        );


        setError("");

        setSuccess("");


        if (!folderId) {

            setError(
                "Não foi possível identificar a pasta de destino."
            );

            return;
        }


        setUploading(true);

        setError("");


        try {

            const formData =
                new FormData();


            formData.append(
                "file",
                file
            );


            formData.append(
                "folder_id",
                String(folderId)
            );


            const response =
                await api.post(
                    "/robots/upload",
                    formData,
                    {
                        headers: {
                            "Content-Type":
                                "multipart/form-data",
                        },
                    }
                );


            console.log(
                "Upload realizado com sucesso:",
                response.data
            );


            // Mantido exatamente como no Robots.tsx atual.
            window.alert(
                response.data?.message ||
                "Operação concluída."
            );


            // IMPORTANTE:
            // Esta duplicidade existe no fluxo atual.
            // Não estamos corrigindo comportamento durante
            // a modularização.
            setSuccess(
                response.data?.message ||
                "Robô processado com sucesso."
            );


            setSuccess(
                response.data?.message ||
                "Robô processado com sucesso."
            );


            // Atualiza a pasta que efetivamente recebeu
            // o novo pacote.
            const pastaDestino =
                folders.find(
                    (folder) =>
                        folder.id === folderId
                );


            if (pastaDestino) {

                await carregarRobos(
                    pastaDestino
                );
            }

        } catch (err: any) {

            console.error(
                "Erro ao fazer upload do robô:",
                err
            );


            const mensagemBackend =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                "Não foi possível fazer o upload do robô.";


            setError(
                typeof mensagemBackend ===
                    "string"
                    ? mensagemBackend
                    : "Não foi possível fazer o upload do robô."
            );

        } finally {

            setUploading(false);
        }
    };


    // ========================================================
    // EXCLUIR ROBOT
    // ========================================================

    const excluirRobo = async (
        robot: Robot
    ) => {

        const confirmar =
            window.confirm(
                `Deseja realmente excluir o robô "${robot.name}"?`
            );


        if (!confirmar) {
            return;
        }


        setError("");

        setSuccess("");


        // A resposta fica separada porque uma falha na
        // atualização visual posterior não significa que a
        // exclusão falhou.
        let response;


        try {

            response =
                await api.delete(
                    `/robots/${robot.id}`
                );

        } catch (error) {

            console.error(
                "Erro ao excluir robô:",
                error
            );


            setError(
                obterMensagemErro(
                    error,
                    `Não foi possível excluir o robô "${robot.name}".`
                )
            );


            return;
        }


        // ====================================================
        // BACKEND CONFIRMOU A EXCLUSÃO
        // ====================================================

        const mensagemSucesso =
            response.data?.message ||
            `Robô "${robot.name}" excluído com sucesso.`;


        const aviso =
            response.data?.warning;


        setSuccess(
            aviso
                ? `${mensagemSucesso} ${aviso}`
                : mensagemSucesso
        );


        // ====================================================
        // ATUALIZA SOMENTE A LISTA VISUAL
        // ====================================================

        try {

            if (rootSelected) {

                await carregarRobosRaiz();

            } else if (selectedFolder) {

                await carregarRobos(
                    selectedFolder
                );
            }

        } catch (refreshError) {

            console.error(
                "Robot excluído, mas a lista não pôde ser atualizada:",
                refreshError
            );


            setError(
                "O Robot foi excluído, mas não foi possível atualizar a lista. Atualize a página."
            );
        }
    };


    // ========================================================
    // BAIXAR ROBOT
    // ========================================================

    const baixarRobo = async (
        robot: Robot
    ) => {

        try {

            const response =
                await api.get(
                    `/robots/${robot.id}/download`,
                    {
                        responseType:
                            "blob",
                    }
                );


            const url =
                window.URL.createObjectURL(
                    new Blob([
                        response.data,
                    ])
                );


            const link =
                document.createElement(
                    "a"
                );


            link.href = url;


            link.setAttribute(
                "download",
                robot.filename
            );


            document.body.appendChild(
                link
            );


            link.click();

            link.remove();


            window.URL.revokeObjectURL(
                url
            );


            // Mantém o fechamento do menu após sucesso.
            setOpenRobotMenu(null);

        } catch (err) {

            console.error(
                "Erro ao baixar robô:",
                err
            );


            alert(
                "Não foi possível baixar o robô."
            );
        }
    };


    // ========================================================
    // CRIAR PROJETO PARA NOVA VERSÃO
    // ========================================================

    const criarProjetoDeAlteracao =
        async (
            robot: Robot
        ) => {

            setOpenRobotMenu(null);

            setError("");


            try {

                const projectName =
                    robot.name.replace(
                        /\.(zip|rar)$/i,
                        ""
                    );


                const response =
                    await api.post(
                        "/development/projects",
                        {
                            name:
                                projectName,

                            description:
                                `Alteração do Robot ${robot.name} ` +
                                `a partir da versão ${robot.version}.`,

                            folder_id:
                                null,

                            base_robot_id:
                                robot.id,
                        }
                    );


                const project =
                    response.data?.project;


                if (!project?.id) {

                    throw new Error(
                        "O backend não retornou o projeto criado."
                    );
                }


                navigate(
                    `/development/${project.id}/studio`,
                    {
                        state: {
                            projectName:
                                project.name,
                        },
                    }
                );

            } catch (err: any) {

                console.error(
                    "Erro ao criar projeto de alteração:",
                    err
                );


                const mensagem =
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    err.message ||
                    "Não foi possível criar o projeto de alteração.";


                setError(
                    typeof mensagem ===
                        "string"
                        ? mensagem
                        : "Não foi possível criar o projeto de alteração."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO DO HOOK
    // ========================================================
    //
    // Este return é fundamental:
    // todos os estados e operações abaixo serão consumidos
    // pelo Robots.tsx na integração.
    // ========================================================

    return {
        robots,
        loadingRobots,

        openRobotMenu,
        setOpenRobotMenu,

        uploading,

        uploadTargetFolderId,
        setUploadTargetFolderId,

        uploadInputRef,

        carregarRobosRaiz,
        carregarRobos,
        atualizarRobosAtuais,

        abrirUploadParaPasta,
        enviarRobo,

        excluirRobo,
        baixarRobo,

        criarProjetoDeAlteracao,
    };
}