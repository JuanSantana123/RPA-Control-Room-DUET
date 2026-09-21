// ============================================================
// PROJECT OPTIONS MENU
// ============================================================
//
// Responsabilidade:
//     Renderiza o menu flutuante de ações pertencente aos
//     AutomationProjects da área de Desenvolvimento.
//
// Atualmente o menu possui:
//     - exclusão lógica do projeto.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// O menu é renderizado através de createPortal(document.body)
// para não ser cortado pelo overflow dos cards ou containers
// da página.
//
// Este arquivo NÃO deve:
//     - excluir projetos diretamente;
//     - chamar endpoints HTTP;
//     - procurar projetos na lista global;
//     - alterar o estado da página;
//     - controlar permissões por conta própria.
//
// Development.tsx continua responsável por:
//     - calcular a posição do menu;
//     - controlar qual projeto possui o menu aberto;
//     - verificar permissões;
//     - localizar/excluir o projeto;
//     - atualizar a lista depois da exclusão.
//
// ProjectOptionsMenu.tsx:
//     - recebe o estado do menu;
//     - posiciona a camada visual;
//     - fecha ao clicar fora;
//     - encaminha a ação de exclusão pelo projectId.
// ============================================================

import {
    Trash2,
} from "lucide-react";


import {
    createPortal,
} from "react-dom";


import type {
    ProjectMenuState,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface ProjectOptionsMenuProps {

    // Estado atual do menu.
    //
    // null:
    //     nenhum menu está aberto.
    //
    // Quando preenchido contém:
    //     - projectId;
    //     - posição top;
    //     - posição left.
    menu:
        ProjectMenuState | null;


    // Permissão efetiva para exclusão de projetos.
    canDelete:
        boolean;


    // Projeto cuja exclusão está atualmente em andamento.
    deletingProjectId:
        number | null;


    // Fecha o menu.
    onClose:
        () => void;


    // Solicita ao componente pai a exclusão do projeto.
    //
    // O componente visual envia somente o ID.
    // A localização do objeto DevelopmentProject e a chamada
    // HTTP permanecem fora deste arquivo.
    onDelete:
        (
            projectId: number
        ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ProjectOptionsMenu({
    menu,
    canDelete,
    deletingProjectId,
    onClose,
    onDelete,
}: ProjectOptionsMenuProps) {

    // ========================================================
    // MENU FECHADO / SEM PERMISSÃO
    // ========================================================

    if (
        !menu ||
        !canDelete
    ) {

        return null;
    }


    // ========================================================
    // PORTAL
    // ========================================================

    return createPortal(

        // ====================================================
        // CAMADA EXTERNA
        // ====================================================
        //
        // Ocupa toda a viewport.
        //
        // Clicar em qualquer região fora do menu fecha
        // imediatamente a camada.
        // ====================================================

        <div
            onMouseDown={
                onClose
            }

            style={{
                position:
                    "fixed",

                inset:
                    0,

                zIndex:
                    9999,

                background:
                    "transparent",
            }}
        >

            {/* =============================================
                MENU
            ============================================= */}

            <div
                role="menu"

                // Impede que clicar dentro do menu dispare
                // o fechamento da camada externa.
                onMouseDown={(event) => {

                    event.stopPropagation();
                }}

                style={{
                    position:
                        "fixed",

                    top:
                        menu.top,

                    left:
                        menu.left,

                    width:
                        190,

                    padding:
                        6,

                    background:
                        "var(--surface-color, #ffffff)",

                    border:
                        "1px solid var(--border-color, #dfe3ea)",

                    borderRadius:
                        8,

                    boxShadow:
                        "0 10px 30px rgba(15, 23, 42, 0.18)",

                    boxSizing:
                        "border-box",
                }}
            >

                {/* =========================================
                    EXCLUIR PROJETO
                ========================================= */}

                <button
                    type="button"

                    role="menuitem"

                    disabled={
                        deletingProjectId ===
                        menu.projectId
                    }

                    onClick={() => {

                        // Apenas informa ao Development.tsx
                        // qual projeto recebeu a ação.
                        //
                        // Nenhuma chamada HTTP acontece aqui.
                        void onDelete(
                            menu.projectId
                        );
                    }}

                    style={{
                        width:
                            "100%",

                        minHeight:
                            36,

                        padding:
                            "8px 10px",

                        border:
                            "none",

                        borderRadius:
                            6,

                        background:
                            "transparent",

                        color:
                            "#dc2626",

                        display:
                            "flex",

                        alignItems:
                            "center",

                        gap:
                            9,

                        fontSize:
                            13,

                        fontWeight:
                            600,

                        textAlign:
                            "left",

                        cursor:
                            "pointer",
                    }}
                >

                    <Trash2
                        size={15}
                        strokeWidth={1.8}
                    />


                    {deletingProjectId ===
                        menu.projectId
                        ? "Excluindo..."
                        : "Excluir projeto"}

                </button>

            </div>

        </div>,

        document.body
    );
}


export default ProjectOptionsMenu;