// ============================================================
// DUET CORE - USERS - PASSWORD HOOK
// ============================================================
//
// Hook responsável exclusivamente pela alteração de senha.
//
// Responsabilidade:
// - selecionar usuário;
// - controlar nova senha e confirmação;
// - validar campos;
// - persistir nova senha;
// - cancelar a operação.
//
// Integração:
// - PUT /auth/users/{user_id}/password
//
// Este hook NÃO:
// - autentica o usuário;
// - cria usuários;
// - edita Roles;
// - renderiza formulário.
// ============================================================

import {
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    User,
} from "../../types/users";


// ============================================================
// PROPS
// ============================================================

interface UseUserPasswordProps {
    setError:
        (message: string) => void;

    setSuccess:
        (message: string) => void;
}


// ============================================================
// HOOK
// ============================================================

export function useUserPassword({
    setError,
    setSuccess,
}: UseUserPasswordProps) {

    const [
        changingPasswordUserId,
        setChangingPasswordUserId,
    ] = useState<number | null>(
        null
    );


    const [
        newPassword,
        setNewPassword,
    ] = useState("");


    const [
        confirmNewPassword,
        setConfirmNewPassword,
    ] = useState("");


    // ========================================================
    // INICIAR ALTERAÇÃO
    // ========================================================

    const iniciarAlteracaoSenha =
        (
            user: User
        ) => {

            setChangingPasswordUserId(
                user.id
            );

            setNewPassword("");
            setConfirmNewPassword("");

            setError("");
            setSuccess("");
        };


    // ========================================================
    // CANCELAR
    // ========================================================

    const cancelarAlteracaoSenha =
        () => {

            setChangingPasswordUserId(
                null
            );

            setNewPassword("");
            setConfirmNewPassword("");
        };


    // ========================================================
    // SALVAR NOVA SENHA
    // ========================================================

    const salvarNovaSenha =
        async () => {

            if (
                changingPasswordUserId ===
                null
            ) {
                return;
            }


            setError("");
            setSuccess("");


            if (!newPassword) {

                setError(
                    "Informe a nova senha."
                );

                return;
            }


            if (!confirmNewPassword) {

                setError(
                    "Confirme a nova senha."
                );

                return;
            }


            if (
                newPassword !==
                confirmNewPassword
            ) {

                setError(
                    "As senhas não coincidem."
                );

                return;
            }


            try {

                await api.put(
                    `/auth/users/${changingPasswordUserId}/password`,
                    {
                        password:
                            newPassword,
                    }
                );


                setSuccess(
                    "Senha do usuário alterada com sucesso."
                );


                setChangingPasswordUserId(
                    null
                );

                setNewPassword("");
                setConfirmNewPassword("");

            } catch (err: any) {

                console.error(
                    "Erro ao alterar senha do usuário:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível alterar a senha do usuário."
                );
            }
        };


    return {
        changingPasswordUserId,

        newPassword,
        setNewPassword,

        confirmNewPassword,
        setConfirmNewPassword,

        iniciarAlteracaoSenha,
        cancelarAlteracaoSenha,
        salvarNovaSenha,
    };
}