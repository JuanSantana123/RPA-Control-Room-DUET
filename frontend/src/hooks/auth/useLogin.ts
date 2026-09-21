// ============================================================
// DUET CORE - AUTH - LOGIN HOOK
// ============================================================
//
// Hook responsável pela lógica operacional da tela de Login.
//
// Responsabilidade:
// - controlar usuário e senha;
// - controlar mensagens de erro;
// - solicitar autenticação ao AuthContext;
// - redirecionar para o Dashboard após login;
// - tratar rejeição de credenciais;
// - tratar falhas inesperadas de comunicação.
//
// Integrações:
// - AuthContext através de useAuth();
// - React Router através de useNavigate().
//
// O AuthContext continua responsável pelo fluxo real de
// autenticação e gerenciamento da sessão.
//
// Este hook NÃO:
// - executa diretamente POST /auth/login;
// - executa diretamente GET /auth/me;
// - manipula cookies;
// - renderiza a interface;
// - define estilos da tela.
//
// A lógica foi extraída de pages/Login.tsx preservando
// exatamente o comportamento atualmente existente.
// ============================================================

import {
    useState,
} from "react";

import type {
    FormEvent,
} from "react";

import {
    useNavigate,
} from "react-router-dom";

import {
    useAuth,
} from "../../context/AuthContext";


// ============================================================
// HOOK
// ============================================================

export function useLogin() {

    // ========================================================
    // CAMPOS
    // ========================================================

    const [
        username,
        setUsername,
    ] = useState("");


    const [
        password,
        setPassword,
    ] = useState("");


    // ========================================================
    // MENSAGEM DE ERRO
    // ========================================================

    const [
        errorMessage,
        setErrorMessage,
    ] = useState("");


    // ========================================================
    // DEPENDÊNCIAS
    // ========================================================

    // Responsável pela navegação após autenticação.
    const navigate =
        useNavigate();


    // O AuthContext continua sendo a única camada responsável
    // por efetivamente autenticar o usuário.
    const {
        login,
    } = useAuth();


    // ========================================================
    // LOGIN
    // ========================================================

    const handleLogin =
        async (
            event:
                FormEvent<HTMLFormElement>
        ) => {

            // Evita o reload padrão do navegador.
            event.preventDefault();


            // Limpa qualquer erro apresentado anteriormente.
            setErrorMessage("");


            try {

                // =================================================
                // AUTENTICAÇÃO
                // =================================================
                //
                // Mantém exatamente o fluxo existente:
                //
                // Login.tsx -> AuthContext -> Backend
                //
                // O AuthContext continua responsável pela sessão.
                // =================================================

                const loginRealizado =
                    await login(
                        username,
                        password
                    );


                // =================================================
                // SUCESSO
                // =================================================

                if (loginRealizado) {

                    navigate("/");

                    return;
                }


                // =================================================
                // CREDENCIAIS REJEITADAS
                // =================================================

                setErrorMessage(
                    "Usuário ou senha inválidos."
                );

            } catch (error) {

                // =================================================
                // ERRO INESPERADO
                // =================================================

                console.error(
                    "Erro ao realizar login:",
                    error
                );


                setErrorMessage(
                    "Não foi possível conectar ao Control Room."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        username,
        setUsername,

        password,
        setPassword,

        errorMessage,

        handleLogin,
    };
}