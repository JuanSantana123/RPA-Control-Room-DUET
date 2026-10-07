// ============================================================
// DUET CORE - DEVELOPMENT - EXTERNAL IDE HOOK
// ============================================================
//
// Responsabilidade:
// - orquestrar a ação "Abrir em IDE";
// - manter loading por projeto;
// - encaminhar feedback para Development.tsx;
// - não renderizar componentes.
// ============================================================

import {
    useState,
} from "react";

import type {
    DevelopmentProject,
} from "../../types/development";

import {
    createDeveloperIdeLaunch,
    openDeveloperIdeProtocol,
} from "../../services/developerIdeApi";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


interface UseExternalIdeOptions {
    canOpenExternalIde: boolean;

    onError:
        (message: string) => void;

    onSuccess:
        (message: string) => void;
}


function useExternalIde({
    canOpenExternalIde,
    onError,
    onSuccess,
}: UseExternalIdeOptions) {

    const [
        openingIdeProjectId,
        setOpeningIdeProjectId,
    ] = useState<number | null>(
        null
    );


    const openExternalIde = async (
        project: DevelopmentProject
    ) => {

        if (!canOpenExternalIde) {
            onError(
                "Você não possui permissão para editar este projeto em uma IDE externa."
            );
            return;
        }

        try {
            setOpeningIdeProjectId(
                project.id
            );

            onError("");

            const launch =
                await createDeveloperIdeLaunch(
                    project.id
                );

            // A escolha da IDE acontece no aplicativo local.
            openDeveloperIdeProtocol(
                launch
            );

            onSuccess(
                `Abrindo "${project.name}" no DUET Developer Tools...`
            );

        } catch (err) {
            onError(
                getApiErrorMessage(
                    err,
                    "Não foi possível abrir o projeto em uma IDE externa."
                )
            );

        } finally {
            setOpeningIdeProjectId(
                null
            );
        }
    };


    return {
        openingIdeProjectId,
        openExternalIde,
    };
}


export default useExternalIde;
