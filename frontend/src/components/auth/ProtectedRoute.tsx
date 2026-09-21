// ============================================================
// ROTA PROTEGIDA
// ============================================================

// Importa o Navigate para redirecionar usuários
// não autenticados para a tela de login.
import { Navigate } from "react-router-dom";

// Importa o hook que fornece o estado
// de autenticação da aplicação.
import { useAuth } from "../../context/AuthContext";

// ============================================================
// COMPONENTE
// ============================================================

export default function ProtectedRoute({
    children,
}: {
    children: React.ReactNode;
}) {
    // Obtém o usuário autenticado e o estado
    // de carregamento da sessão.
    const {
        user,
        loading,
    } = useAuth();

    // Enquanto o React verifica a sessão existente,
    // não devemos redirecionar o usuário.
    //
    // Isso evita que uma sessão válida seja interpretada
    // temporariamente como uma sessão inexistente.
    if (loading) {
        return (
            <div
                style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    minHeight: "100vh",
                }}
            >
                Carregando...
            </div>
        );
    }

    // Se não existir usuário autenticado,
    // redireciona para a tela de login.
    if (!user) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }

    // Se existe um usuário autenticado,
    // permite o acesso à página solicitada.
    return <>{children}</>;
}