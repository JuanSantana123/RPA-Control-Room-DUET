// ============================================================
// DUET CORE - ROLES - PERMISSION UTILITIES
// ============================================================
//
// Utilitários puros utilizados para organizar permissões.
//
// Responsabilidade:
// - agrupar o catálogo de permissões pelo recurso.
//
// Exemplo:
//
// Agents
//   view
//   create
//   edit
//   delete
//
// Robots
//   view
//   create
//   edit
//   delete
//
// Este módulo NÃO:
// - modifica permissões;
// - executa chamadas HTTP;
// - possui estado;
// - conhece a Role selecionada.
//
// A função apenas transforma a coleção recebida.
// ============================================================

import type {
    Permission,
} from "../types/roles";


// ============================================================
// AGRUPAR PERMISSÕES POR RECURSO
// ============================================================

export function groupPermissionsByResource(
    permissions: Permission[]
): Record<string, Permission[]> {

    return permissions.reduce<
        Record<string, Permission[]>
    >(
        (
            grupos,
            permission
        ) => {

            // Cria o grupo somente quando o recurso
            // ainda não estiver presente.
            if (
                !grupos[
                    permission.resource
                ]
            ) {

                grupos[
                    permission.resource
                ] = [];
            }


            // Adiciona a permissão ao recurso correspondente.
            grupos[
                permission.resource
            ].push(
                permission
            );


            return grupos;
        },
        {}
    );
}