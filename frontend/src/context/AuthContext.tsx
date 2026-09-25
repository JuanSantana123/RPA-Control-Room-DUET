// ============================================================
// CONTEXTO DE AUTENTICAÇÃO
// ============================================================

// Importa recursos do React para criar e controlar
// o contexto de autenticação da aplicação.
import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

// Importa a instância do Axios utilizada pelo Frontend.
import api from "../services/api";

// ============================================================
// TIPAGEM DO USUÁRIO
// ============================================================

// Representa os dados do usuário autenticado.
interface User {
    id: number;
    username: string;
    name: string;
    is_active: number;

    // Permissões efetivas calculadas pelo Backend através
    // das Roles atribuídas ao usuário.
    //
    // Exemplos:
    // "Dashboard:view"
    // "Users:view"
    // "Roles:edit"
    permissions: string[];
}

// ============================================================
// TIPAGEM DO CONTEXTO
// ============================================================

interface AuthContextType {
    // Usuário atualmente autenticado.
    user: User | null;

    // Indica se o Frontend ainda está verificando
    // a sessão existente.
    loading: boolean;

    // Verifica se o usuário autenticado possui uma
    // determinada permissão efetiva do RBAC.
    //
    // Exemplo:
    // can("Dashboard:view")
    //
    // Importante:
    // esta verificação controla apenas a interface.
    // O Backend continua sendo a autoridade de segurança.
    can: (permission: string) => boolean;

    // Realiza o login e atualiza o usuário
    // dentro do AuthContext.
    login: (
        username: string,
        password: string
    ) => Promise<boolean>;

    // Encerra a sessão do usuário.
    logout: () => Promise<void>;
}

// ============================================================
// CRIAÇÃO DO CONTEXTO
// ============================================================

// Cria o contexto que será compartilhado
// pelas páginas da aplicação.
const AuthContext = createContext<
    AuthContextType | undefined
>(undefined);

// ============================================================
// PROVIDER
// ============================================================

export function AuthProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    // Guarda o usuário autenticado.
    const [user, setUser] = useState<User | null>(null);

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

// ============================================================
// HOOK DE AUTENTICAÇÃO
// ============================================================

export function useAuth() {
    // Permite que qualquer componente da aplicação
    // acesse o usuário e as funções de autenticação.
    const context = useContext(AuthContext);

    // Gera um erro caso o hook seja utilizado
    // fora do AuthProvider.
    if (!context) {
        throw new Error(
            "useAuth deve ser utilizado dentro de AuthProvider."
        );
    }

    return context;
}