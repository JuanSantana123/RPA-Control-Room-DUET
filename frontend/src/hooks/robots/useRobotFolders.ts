// ============================================================
// DUET CORE - ROBOTS - FOLDERS HOOK
// ============================================================
//
// Responsabilidade:
// - carregar a estrutura de pastas de Robots;
// - controlar pasta selecionada e Raiz de Robôs;
// - controlar expansão da árvore;
// - criar pastas e subpastas;
// - excluir pastas.
//
// Este hook NÃO:
// - carrega Robots;
// - faz upload de Robots;
// - executa Robots;
// - gerencia Libraries;
// - renderiza componentes.
//
// Integrações:
// - GET    /robot-folders
// - POST   /robot-folders
// - DELETE /robot-folders/{folder_id}
//
// IMPORTANTE:
// "Raiz de Robôs" continua sendo uma localização lógica.
// Ela não corresponde a um registro RobotFolder no banco.
//
// A lógica deste hook foi extraída do Robots.tsx sem alterar
// as regras funcionais existentes da tela.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    RobotFolder,
} from "../../types/robots";


interface UseRobotFoldersParams {

    // Estado visual de erro continua pertencendo à página,
    // pois é compartilhado entre diferentes operações.
    setError: React.Dispatch<
        React.SetStateAction<string>
    >;
}


export function useRobotFolders({
    setError,
}: UseRobotFoldersParams) {

    // ========================================================
    // ESTADOS - PASTAS
    // ========================================================

    const [
        folders,
        setFolders,
    ] = useState<RobotFolder[]>([]);


    const [
        selectedFolder,
        setSelectedFolder,
    ] = useState<RobotFolder | null>(
        null
    );


    // A tela original inicia sem Raiz de Robôs selecionada.
    const [
        rootSelected,
        setRootSelected,
    ] = useState<boolean>(
        false
    );


    // IDs das pastas atualmente expandidas.
    const [
        expandedFolders,
        setExpandedFolders,
    ] = useState<Set<number>>(
        new Set()
    );


    const [
        loadingFolders,
        setLoadingFolders,
    ] = useState<boolean>(
        true
    );


    // ========================================================
    // ESTADOS - CRIAÇÃO DE PASTA
    // ========================================================

    const [
        newFolderName,
        setNewFolderName,
    ] = useState<string>("");


    // null significa criação na raiz das pastas.
    const [
        newFolderParentId,
        setNewFolderParentId,
    ] = useState<number | null>(
        null
    );


    const [
        creatingFolder,
        setCreatingFolder,
    ] = useState<boolean>(
        false
    );


    const [
        showFolderForm,
        setShowFolderForm,
    ] = useState<boolean>(
        false
    );


    // ========================================================
    // ESTADO - MENU CONTEXTUAL
    // ========================================================

    const [
        openFolderMenu,
        setOpenFolderMenu,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // CARREGAR PASTAS
    // ========================================================

    const carregarPastas = async () => {

        try {

            setLoadingFolders(true);


            const response =
                await api.get(
                    "/robot-folders"
                );


            // Mantém o contrato usado originalmente pela tela.
            setFolders(
                response.data.folders
            );

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
    // OBTER SUBPASTAS
    // ========================================================

    const obterSubpastas = (
        parentId: number
    ): RobotFolder[] => {

        return folders.filter(
            (folder) =>
                folder.parent_id === parentId
        );
    };


    // ========================================================
    // ALTERAR EXPANSÃO DA PASTA
    // ========================================================

    const alternarPasta = (
        folderId: number
    ) => {

        setExpandedFolders((atual) => {

            const novo =
                new Set(atual);


            if (novo.has(folderId)) {

                novo.delete(folderId);

            } else {

                novo.add(folderId);
            }


            return novo;
        });
    };


    // ========================================================
    // SELECIONAR RAIZ
    // ========================================================
    //
    // Esta função altera somente a seleção.
    // O carregamento dos Robots continuará sendo coordenado
    // durante a integração com useRobotsData.
    // ========================================================

    const selecionarRaiz = () => {

        setRootSelected(true);

        setSelectedFolder(null);

        setOpenFolderMenu(null);
    };


    // ========================================================
    // SELECIONAR PASTA
    // ========================================================

    const selecionarPasta = (
        folder: RobotFolder
    ) => {

        setRootSelected(false);

        setSelectedFolder(folder);

        setOpenFolderMenu(null);
    };


    // ========================================================
    // ABRIR CRIAÇÃO DE PASTA RAIZ
    // ========================================================

    const abrirCriacaoPastaRaiz = () => {

        setNewFolderName("");

        setNewFolderParentId(null);

        setShowFolderForm(true);

        setOpenFolderMenu(null);
    };


    // ========================================================
    // ABRIR CRIAÇÃO DE SUBPASTA
    // ========================================================

    const abrirCriacaoSubpasta = (
        folder: RobotFolder
    ) => {

        setNewFolderParentId(
            folder.id
        );

        setNewFolderName("");

        setOpenFolderMenu(null);

        setShowFolderForm(true);
    };


    // ========================================================
    // CRIAR PASTA
    // ========================================================

    const criarPasta = async () => {

        // Remove espaços desnecessários antes de enviar.
        const nome =
            newFolderName.trim();


        // Mantém a validação existente no Robots.tsx.
        if (!nome) {

            setError(
                "Informe um nome para a pasta."
            );

            return;
        }


        try {

            setCreatingFolder(true);

            setError("");


            const response =
                await api.post(
                    "/robot-folders",
                    {
                        name: nome,
                        parent_id:
                            newFolderParentId,
                    }
                );


            console.log(
                "Pasta criada com sucesso:",
                response.data
            );


            // Se a pasta criada for uma subpasta,
            // mantém a pasta pai expandida.
            if (
                newFolderParentId !== null
            ) {

                setExpandedFolders(
                    (atual) => {

                        const novo =
                            new Set(atual);


                        novo.add(
                            newFolderParentId
                        );


                        return novo;
                    }
                );
            }


            setNewFolderName("");

            setShowFolderForm(false);

            setNewFolderParentId(null);


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
    // EXCLUIR PASTA
    // ========================================================
    //
    // O backend continua sendo responsável por validar se a
    // pasta realmente pode ser excluída.
    // ========================================================

    const excluirPasta = async (
        folder: RobotFolder
    ) => {

        const confirmar =
            window.confirm(
                `Deseja realmente excluir a pasta "${folder.name}"?`
            );


        if (!confirmar) {
            return;
        }


        try {

            setError("");


            await api.delete(
                `/robot-folders/${folder.id}`
            );


            // Mantém a mesma regra existente:
            // se a pasta removida estava selecionada,
            // a seleção é simplesmente limpa.
            if (
                selectedFolder?.id ===
                folder.id
            ) {

                setSelectedFolder(null);
            }


            await carregarPastas();

        } catch (err: any) {

            console.error(
                "Erro ao excluir pasta:",
                err
            );


            const mensagem =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                "Não foi possível excluir a pasta.";


            setError(mensagem);
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO DO HOOK
    // ========================================================

    return {
        folders,

        selectedFolder,
        setSelectedFolder,

        rootSelected,
        setRootSelected,

        expandedFolders,
        loadingFolders,

        newFolderName,
        setNewFolderName,

        newFolderParentId,
        setNewFolderParentId,

        creatingFolder,

        showFolderForm,
        setShowFolderForm,

        openFolderMenu,
        setOpenFolderMenu,

        carregarPastas,

        obterSubpastas,
        alternarPasta,

        selecionarRaiz,
        selecionarPasta,

        abrirCriacaoPastaRaiz,
        abrirCriacaoSubpasta,

        criarPasta,
        excluirPasta,
    };
}