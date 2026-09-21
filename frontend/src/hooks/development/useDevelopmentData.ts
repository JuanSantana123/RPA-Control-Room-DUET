// ============================================================
// USE DEVELOPMENT DATA
// ============================================================
//
// Responsabilidade:
//     Centraliza o carregamento estrutural da área de
//     Desenvolvimento.
//
// Este hook controla:
//     - permissões efetivas do usuário autenticado;
//     - carregamento inicial da página;
//     - lista oficial de AutomationProjects ativos;
//     - estado de loading da área;
//     - erro de inicialização/carregamento;
//     - recarregamento da lista de projetos.
//
// Endpoints utilizados:
//
//     GET /auth/me
//     GET /development/projects
//
// Regras preservadas:
//
//     - projetos com status "published" não aparecem na lista
//       ativa de Desenvolvimento;
//
//     - projetos publicados continuam preservados no backend
//       para histórico e auditoria;
//
//     - os projetos somente são carregados quando o usuário
//       possui Development:view;
//
//     - permissionsLoaded somente é liberado depois da
//       tentativa inicial de leitura das permissões.
//
// Este hook NÃO deve:
//     - controlar Kanban;
//     - controlar Lixeira;
//     - criar projetos;
//     - excluir projetos;
//     - executar projetos;
//     - publicar Releases;
//     - controlar navegação visual;
//     - renderizar componentes.
//
// Development.tsx continua sendo o container responsável por
// conectar esses dados aos demais domínios da página.
// ============================================================

import {
    useEffect,
    useState,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    DevelopmentProject,
} from "../../types/development";


// ============================================================
// RETORNO DO HOOK
// ============================================================

interface UseDevelopmentDataResult {

    // --------------------------------------------------------
    // PROJETOS
    // --------------------------------------------------------

    projects:
        DevelopmentProject[];

    setProjects:
        React.Dispatch<
            React.SetStateAction<
                DevelopmentProject[]
            >
        >;


    // --------------------------------------------------------
    // CARREGAMENTO / ERRO
    // --------------------------------------------------------

    loading:
        boolean;

    error:
        string;

    setError:
        React.Dispatch<
            React.SetStateAction<string>
        >;


    // --------------------------------------------------------
    // PERMISSÕES
    // --------------------------------------------------------

    permissions:
        string[];

    permissionsLoaded:
        boolean;


    // --------------------------------------------------------
    // RECARREGAMENTO
    // --------------------------------------------------------

    loadProjects:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentData():
    UseDevelopmentDataResult {

    // ========================================================
    // PROJETOS
    // ========================================================

    const [
        projects,
        setProjects,
    ] =
        useState<DevelopmentProject[]>(
            []
        );


    // ========================================================
    // CARREGAMENTO
    // ========================================================

    const [
        loading,
        setLoading,
    ] =
        useState(
            true
        );


    // ========================================================
    // FEEDBACK DE ERRO
    // ========================================================

    const [
        error,
        setError,
    ] =
        useState(
            ""
        );


    // ========================================================
    // PERMISSÕES
    // ========================================================

    const [
        permissions,
        setPermissions,
    ] =
        useState<string[]>(
            []
        );


    // Indica que a tentativa inicial de leitura das
    // permissões já terminou.
    const [
        permissionsLoaded,
        setPermissionsLoaded,
    ] =
        useState(
            false
        );


    // ========================================================
    // CARREGAR PROJETOS
    // ========================================================
    //
    // Consulta os AutomationProjects persistidos no backend.
    //
    // Projetos publicados são preservados no banco, porém não
    // fazem parte da coleção ativa de Desenvolvimento.
    // ========================================================

    const loadProjects = async () => {

        try {

            setError(
                ""
            );


            const response =
                await api.get(
                    "/development/projects"
                );


            const activeProjects: DevelopmentProject[] =
                (
                    response.data.projects ||
                    []
                ).filter(
                    (
                        project:
                            DevelopmentProject
                    ) =>
                        project.status !==
                        "published"
                );


            setProjects(
                activeProjects
            );

        } catch (err: any) {

            console.error(
                "Erro ao carregar projetos de Desenvolvimento:",
                err
            );


            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível carregar os projetos."
                )
            );

        } finally {

            setLoading(
                false
            );
        }
    };


    // ========================================================
    // CARREGAMENTO INICIAL
    // ========================================================
    //
    // Ordem:
    //
    //     1. consulta /auth/me;
    //     2. armazena as permissões efetivas;
    //     3. verifica Development:view;
    //     4. carrega os projetos quando autorizado;
    //     5. libera permissionsLoaded.
    //
    // O comportamento corresponde ao fluxo que existia
    // diretamente dentro de Development.tsx.
    // ========================================================

    useEffect(() => {

        const loadInitialData =
            async () => {

                try {

                    setLoading(
                        true
                    );

                    setError(
                        ""
                    );


                    // ----------------------------------------
                    // USUÁRIO / PERMISSÕES
                    // ----------------------------------------

                    const response =
                        await api.get(
                            "/auth/me"
                        );


                    const effectivePermissions:
                        string[] =
                        response.data
                            ?.user
                            ?.permissions ||
                        [];


                    setPermissions(
                        effectivePermissions
                    );


                    // ----------------------------------------
                    // PROJETOS
                    // ----------------------------------------

                    if (
                        effectivePermissions.includes(
                            "Development:view"
                        )
                    ) {

                        await loadProjects();

                    } else {

                        setProjects(
                            []
                        );

                        setLoading(
                            false
                        );
                    }

                } catch (err: any) {

                    console.error(
                        "Erro ao carregar permissões de Desenvolvimento:",
                        err
                    );


                    setPermissions(
                        []
                    );

                    setProjects(
                        []
                    );

                    setLoading(
                        false
                    );


                    setError(
                        getApiErrorMessage(
                            err,
                            "Não foi possível carregar suas permissões."
                        )
                    );

                } finally {

                    setPermissionsLoaded(
                        true
                    );
                }
            };


        void loadInitialData();

    }, []);


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        projects,
        setProjects,

        loading,

        error,
        setError,

        permissions,
        permissionsLoaded,

        loadProjects,
    };
}


export default useDevelopmentData;