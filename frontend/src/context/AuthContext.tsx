// ============================================================
// CONTEXTO DE AUTENTICAÇÃO
// ============================================================

// Importa recursos do React para criar e controlar
// o contexto de autenticação da aplicação.
import {
    useEffect,
    useState,
} from "react";

// Importa a instância do Axios utilizada pelo Frontend.
import api from "../services/api";
import { AuthContext, type AuthUser } from "./auth-context";

// ============================================================
// TIPAGEM DO USUÁRIO
// ============================================================

// Representa os dados do usuário autenticado.
// ============================================================
// PROVIDER
// ============================================================

export function AuthProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    // Guarda o usuário autenticado.
    const [user, setUser] = useState<AuthUser | null>(null);

    // Enquanto verificamos a sessão existente,
    // mantemos loading como true.
    const [loading, setLoading] = useState(true);

    // ========================================================
    // VERIFICAR SESSÃO
    // ========================================================

    useEffect(() => {
        // Faz uma chamada ao Backend para descobrir
        // se o cookie atual representa uma sessão válida.
        api.get("/auth/me")
            .then((response) => {
                // Se o Backend confirmar a sessão,
                // armazenamos o usuário no contexto.
                if (response.data.status === "success") {
                    setUser(response.data.user);
                }
            })
            .catch(() => {
                // Se a sessão não existir ou estiver inválida,
                // consideramos que não existe usuário autenticado.
                setUser(null);
            })
            .finally(() => {
                // Finaliza a verificação inicial da sessão.
                setLoading(false);
            });
    }, []);

    // ========================================================
    // LOGIN
    // ========================================================

    const login = async (
        username: string,
        password: string
    ): Promise<boolean> => {
        try {
            // Envia as credenciais para o Backend.
            //
            // O Backend irá validar a senha, criar a sessão
            // e enviar o cookie HttpOnly.
            const response = await api.post(
                "/auth/login",
                {
                    username,
                    password
                }
            );

            // Verifica se o Backend confirmou o login.
            if (response.data.status !== "success") {
                return false;
            }

            // Depois que o login foi realizado, consulta
            // novamente o Backend para obter o usuário
            // associado à sessão recém-criada.
            const usuarioResponse = await api.get(
                "/auth/me"
            );

            // Se a sessão foi reconhecida pelo Backend,
            // atualiza o usuário no AuthContext.
            if (
                usuarioResponse.data.status ===
                "success"
            ) {
                setUser(
                    usuarioResponse.data.user
                );

                return true;
            }

            return false;

        } catch (error) {
            // Caso o Backend não esteja disponível
            // ou ocorra algum erro durante o login.
            console.error(
                "Erro ao realizar login:",
                error
            );

            return false;
        }
    };

    // ========================================================
    // LOGOUT
    // ========================================================

    const logout = async () => {
        try {
            // Solicita ao Backend o encerramento da sessão.
            await api.post("/auth/logout");
        } finally {
            // Remove o usuário do estado do React,
            // independentemente do resultado da API.
            setUser(null);
        }
    };


    // ========================================================
    // VERIFICAÇÃO DE PERMISSÃO
    // ========================================================
    //
    // Centraliza a consulta das permissões efetivas recebidas
    // do Backend.
    //
    // O Frontend utiliza essa função para decidir se elementos
    // visuais devem ou não ser apresentados.
    //
    // A segurança real continua sendo validada pelo Backend.
    // ========================================================

    const can = (
        permission: string
    ): boolean => {

        if (!user) {
            return false;
        }

        return (
            user.permissions ?? []
        ).includes(
            permission
        );
    };

    // ========================================================
    // DISPONIBILIZAÇÃO DO CONTEXTO
    // ========================================================

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                login,
                logout,
                can,
            }}

        >
            {children}
        </AuthContext.Provider>
    );
}
