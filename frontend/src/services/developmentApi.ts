// ============================================================
// SERVICE - DEVELOPMENT API
// ============================================================
//
// Responsabilidade:
//     Centraliza as chamadas HTTP utilizadas pela área de
//     Desenvolvimento do DUET CORE.
//
// Este service utiliza o client Axios global já existente em:
//
//     services/api.ts
//
// Portanto:
//     - NÃO cria uma nova instância Axios;
//     - NÃO gerencia autenticação;
//     - NÃO mantém estado React;
//     - NÃO renderiza interface.
//
// A responsabilidade deste arquivo é somente comunicar a camada
// frontend com os endpoints do FastAPI.
//
// Componentes e hooks devem preferencialmente consumir estas
// funções em vez de conhecer URLs da API diretamente.
// ============================================================

import api from "./api";


import type {
    CardComment,
    CardDetailsUpdatePayload,
    CardUser,
    CreateDevelopmentProjectPayload,
    DevelopmentProject,
    DevelopmentStage,
    ExecutionAgent,
    OriginRobot,
    OriginRobotFolder,
    PublishDevelopmentProjectPayload,
    ReleasePreview,
} from "../types/development";


// ============================================================
// PROJETOS
// ============================================================

export const getDevelopmentProjects =
    async (): Promise<DevelopmentProject[]> => {

        const response =
            await api.get(
                "/development/projects"
            );


        return response.data?.projects || [];
    };


export const createDevelopmentProject =
    async (
        payload: CreateDevelopmentProjectPayload
    ): Promise<DevelopmentProject> => {

        const response =
            await api.post(
                "/development/projects",
                payload
            );


        return response.data?.project;
    };


export const deleteDevelopmentProject =
    async (
        projectId: number
    ): Promise<void> => {

        await api.delete(
            `/development/projects/${projectId}`
        );
    };


// ============================================================
// ORIGEM - ROBÔS DE PRODUÇÃO
// ============================================================

export const getDevelopmentReleaseRobots =
    async (): Promise<{
        folders: OriginRobotFolder[];
        robots: OriginRobot[];
    }> => {

        const response =
            await api.get(
                "/development/release/robots"
            );


        return {
            folders:
                response.data?.folders || [],

            robots:
                response.data?.robots || [],
        };
    };


// ============================================================
// WORKFLOW / KANBAN
// ============================================================

export const getDevelopmentWorkflow =
    async (): Promise<DevelopmentStage[]> => {

        const response =
            await api.get(
                "/development/workflow/board"
            );


        return response.data?.stages || [];
    };


export const moveDevelopmentProjectToStage =
    async (
        projectId: number,
        targetStageId: number
    ): Promise<DevelopmentProject> => {

        const response =
            await api.patch(
                `/development/projects/${projectId}/stage`,
                {
                    target_stage_id:
                        targetStageId,
                }
            );


        return response.data?.project;
    };


// ============================================================
// EXECUÇÃO
// ============================================================

export const getDevelopmentExecutionAgents =
    async (): Promise<ExecutionAgent[]> => {

        const response =
            await api.get(
                "/agents/execution/available-agents"
            );


        return response.data?.agents || [];
    };


export const runDevelopmentProject =
    async (
        projectId: number,
        agentId: string
    ) => {

        const response =
            await api.post(
                `/development/projects/${projectId}/execution/run`,
                {
                    agent_id:
                        agentId,
                }
            );


        return response.data;
    };


// ============================================================
// LIXEIRA
// ============================================================

export const getDevelopmentTrash =
    async (): Promise<DevelopmentProject[]> => {

        const response =
            await api.get(
                "/development/projects/trash"
            );


        return response.data?.projects || [];
    };


export const restoreDevelopmentProject =
    async (
        projectId: number
    ): Promise<DevelopmentProject> => {

        const response =
            await api.post(
                `/development/projects/${projectId}/restore`
            );


        return response.data?.project;
    };


export const permanentlyDeleteDevelopmentProject =
    async (
        projectId: number
    ): Promise<void> => {

        await api.delete(
            `/development/projects/${projectId}/permanent`
        );
    };


// ============================================================
// DETALHES DO CARD - USUÁRIOS
// ============================================================

export const getDevelopmentCardUsers =
    async (): Promise<CardUser[]> => {

        const response =
            await api.get(
                "/development/card-users"
            );


        return response.data?.users || [];
    };


// ============================================================
// DETALHES DO CARD - PLANEJAMENTO
// ============================================================

export const updateDevelopmentCardDetails =
    async (
        projectId: number,
        payload: CardDetailsUpdatePayload
    ): Promise<DevelopmentProject> => {

        const response =
            await api.patch(
                `/development/projects/${projectId}/card-details`,
                payload
            );


        return response.data?.project;
    };


// ============================================================
// DETALHES DO CARD - COMENTÁRIOS
// ============================================================

export const getDevelopmentProjectComments =
    async (
        projectId: number
    ): Promise<CardComment[]> => {

        const response =
            await api.get(
                `/development/projects/${projectId}/comments`
            );


        return response.data?.comments || [];
    };


export const addDevelopmentProjectComment =
    async (
        projectId: number,
        content: string
    ): Promise<CardComment> => {

        const response =
            await api.post(
                `/development/projects/${projectId}/comments`,
                {
                    content,
                }
            );


        return response.data?.comment;
    };


// ============================================================
// RELEASE - PRÉVIA
// ============================================================

export const getDevelopmentReleasePreview =
    async (
        projectId: number
    ): Promise<ReleasePreview> => {

        const response =
            await api.get(
                `/development/projects/${projectId}/release/preview`
            );


        return response.data;
    };


// ============================================================
// RELEASE - PUBLICAÇÃO
// ============================================================

export const publishDevelopmentProject =
    async (
        projectId: number,
        payload: PublishDevelopmentProjectPayload
    ) => {

        const response =
            await api.post(
                `/development/projects/${projectId}/publish`,
                payload
            );


        return response.data;
    };