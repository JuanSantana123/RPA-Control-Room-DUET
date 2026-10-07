// ============================================================
// DUET CORE - ROBOT STUDIO - WORKSPACE ASSETS
// ============================================================
//
// Responsabilidade:
// - fazer upload de arquivos binários ou textuais para pastas de Library;
// - baixar arquivos individuais;
// - baixar pastas/Libraries como ZIP;
// - atualizar a árvore do Studio sem abrir o arquivo enviado no Monaco.
//
// Segurança real continua no backend. O frontend somente evita ações
// incompatíveis com o estado atual do Checkout.
// ============================================================

import {
    useRef,
    useState,
    type ChangeEvent,
    type Dispatch,
    type SetStateAction,
} from "react";

import {
    getApiErrorMessage,
    getApiErrorStatus,
} from "../../utils/apiErrors";

import {
    addNodeToFolder,
} from "../../utils/robotStudioTree";

import type {
    StudioNode,
} from "../../types/robotStudio";

import {
    downloadWorkspaceAsset,
    uploadWorkspaceAsset,
} from "../../services/workspaceAssetsApi";


interface UseRobotStudioWorkspaceAssetsParams {
    projectId?: string;

    canWritePath: (
        path: string
    ) => boolean;

    setWorkspace: Dispatch<
        SetStateAction<StudioNode[]>
    >;

    setExpandedFolders: Dispatch<
        SetStateAction<Set<string>>
    >;

    setOutputLines: Dispatch<
        SetStateAction<string[]>
    >;

    carregarCheckout: (
        registrarOutput?: boolean
    ) => Promise<void>;
}


export function useRobotStudioWorkspaceAssets({
    projectId,
    canWritePath,
    setWorkspace,
    setExpandedFolders,
    setOutputLines,
    carregarCheckout,
}: UseRobotStudioWorkspaceAssetsParams) {
    const fileInputRef =
        useRef<HTMLInputElement>(null);

    const uploadTargetRef =
        useRef<string | null>(null);

    const [
        uploadingFolderPath,
        setUploadingFolderPath,
    ] = useState<string | null>(null);

    const [
        downloadingPath,
        setDownloadingPath,
    ] = useState<string | null>(null);


    const requestUpload = (
        targetFolderPath: string
    ) => {
        if (
            !projectId ||
            !targetFolderPath.startsWith(
                "_libraries/"
            ) ||
            !canWritePath(
                targetFolderPath
            )
        ) {
            setOutputLines(
                (current) => [
                    ...current,
                    "[DUET] Faça Checkout do projeto e da Library para enviar arquivos.",
                ]
            );

            return;
        }

        uploadTargetRef.current =
            targetFolderPath;

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
            fileInputRef.current.click();
        }
    };


    const handleUploadSelected =
        async (
            event: ChangeEvent<HTMLInputElement>
        ) => {
            const file =
                event.target.files?.[0];

            const targetFolderPath =
                uploadTargetRef.current;

            if (
                !file ||
                !projectId ||
                !targetFolderPath
            ) {
                return;
            }

            if (
                !canWritePath(
                    targetFolderPath
                )
            ) {
                setOutputLines(
                    (current) => [
                        ...current,
                        "[DUET] A Library não está mais disponível para edição por este usuário.",
                    ]
                );

                return;
            }

            try {
                setUploadingFolderPath(
                    targetFolderPath
                );

                const result =
                    await uploadWorkspaceAsset(
                        projectId,
                        targetFolderPath,
                        file
                    );

                const newNode: StudioNode = {
                    id: result.path,
                    name: result.filename,
                    type: "file",
                };

                setWorkspace(
                    (current) =>
                        addNodeToFolder(
                            current,
                            targetFolderPath,
                            newNode
                        )
                );

                setExpandedFolders(
                    (current) => {
                        const next =
                            new Set(current);

                        next.add(
                            targetFolderPath
                        );

                        return next;
                    }
                );

                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] Arquivo enviado para a Library: ${result.path}`,
                    ]
                );

            } catch (err: unknown) {
                console.error(
                    "Erro ao enviar arquivo para a Library:",
                    err
                );

                if (
                    getApiErrorStatus(err) ===
                    423
                ) {
                    await carregarCheckout(
                        false
                    );
                }

                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] ERRO NO UPLOAD: ${
                            getApiErrorMessage(
                                err,
                                "Não foi possível enviar o arquivo para a Library."
                            )
                        }`,
                    ]
                );

            } finally {
                setUploadingFolderPath(
                    null
                );

                uploadTargetRef.current =
                    null;

                event.target.value = "";
            }
        };


    const downloadNode =
        async (
            node: StudioNode
        ) => {
            if (
                !projectId ||
                !node.id.startsWith(
                    "_libraries/"
                )
            ) {
                return;
            }

            try {
                setDownloadingPath(
                    node.id
                );

                const blob =
                    await downloadWorkspaceAsset(
                        projectId,
                        node.id
                    );

                const downloadName =
                    node.type === "folder"
                        ? `${node.name}.zip`
                        : node.name;

                const url =
                    URL.createObjectURL(
                        blob
                    );

                const anchor =
                    document.createElement(
                        "a"
                    );

                anchor.href = url;
                anchor.download = downloadName;
                anchor.style.display = "none";

                document.body.appendChild(
                    anchor
                );

                anchor.click();
                anchor.remove();

                window.setTimeout(
                    () =>
                        URL.revokeObjectURL(
                            url
                        ),
                    1000
                );

                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] Download iniciado: ${downloadName}`,
                    ]
                );

            } catch (err: unknown) {
                console.error(
                    "Erro ao baixar item da Library:",
                    err
                );

                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] ERRO NO DOWNLOAD: ${
                            getApiErrorMessage(
                                err,
                                "Não foi possível baixar o item da Library."
                            )
                        }`,
                    ]
                );

            } finally {
                setDownloadingPath(
                    null
                );
            }
        };


    return {
        fileInputRef,
        uploadingFolderPath,
        downloadingPath,
        requestUpload,
        handleUploadSelected,
        downloadNode,
    };
}
