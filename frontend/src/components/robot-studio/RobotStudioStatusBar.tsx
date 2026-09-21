// ============================================================
// DUET CORE - ROBOT STUDIO - STATUS BAR
// ============================================================
//
// Responsabilidade:
// - representar a barra inferior visual do Robot Studio;
// - apresentar informações de contexto já calculadas pelo
//   componente proprietário.
//
// IMPORTANTE:
// Este componente é exclusivamente visual.
// Nenhuma regra funcional deve ser introduzida aqui.
//
// Este componente NÃO deve:
// - acessar API;
// - controlar Checkout;
// - manipular workspace;
// - alterar projeto;
// - controlar Libraries.
//
// Todos os valores apresentados são recebidos por props.
// ============================================================

import type {
    CSSProperties,
    ReactNode,
} from "react";


interface RobotStudioStatusBarStyles {
    statusbar: CSSProperties;
    statusbarLeft: CSSProperties;
    statusbarRight: CSSProperties;
}


interface RobotStudioStatusBarProps {
    styles: RobotStudioStatusBarStyles;

    leftContent: ReactNode;
    rightContent: ReactNode;
}


function RobotStudioStatusBar({
    styles,
    leftContent,
    rightContent,
}: RobotStudioStatusBarProps) {

    return (
        <footer style={styles.statusbar}>

            <div style={styles.statusbarLeft}>
                {leftContent}
            </div>

            <div style={styles.statusbarRight}>
                {rightContent}
            </div>

        </footer>
    );
}


export default RobotStudioStatusBar;