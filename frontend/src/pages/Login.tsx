// ============================================================
// DUET CORE - LOGIN PAGE
// ============================================================
//
// Tela de autenticação do DUET CORE.
//
// Responsabilidade:
// - renderizar a interface de Login;
// - apresentar os campos de usuário e senha;
// - apresentar mensagens de erro;
// - encaminhar o envio do formulário ao hook useLogin.
//
// A lógica operacional está concentrada em:
//
// useLogin
// - estado do usuário;
// - estado da senha;
// - autenticação através do AuthContext;
// - tratamento de erros;
// - redirecionamento após autenticação.
//
// Os estilos visuais estão concentrados em:
//
// styles/login.css
//
// Esta página NÃO:
// - chama diretamente endpoints de autenticação;
// - manipula cookies ou sessões;
// - implementa regras do AuthContext;
// - concentra estilos inline.
//
// O AuthContext continua sendo responsável pelo processo real
// de autenticação e gerenciamento da sessão.
// ============================================================

import {
    useLogin,
} from "../hooks/auth/useLogin";

import "../styles/login.css";


// ============================================================
// COMPONENTE LOGIN
// ============================================================

export default function Login() {

    // ========================================================
    // ESTADO / OPERAÇÕES
    // ========================================================
    //
    // Toda a lógica da tela permanece encapsulada no hook.
    // ========================================================

    const {
        username,
        setUsername,

        password,
        setPassword,

        errorMessage,

        handleLogin,
    } = useLogin();


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="login-page">

            {/* ==================================================
                CARD PRINCIPAL
                ================================================== */}

            <div className="login-card">

                {/* ==============================================
                    CABEÇALHO
                    ============================================== */}

                <h1 className="login-title">
                    RPA Control Room
                </h1>


                <p className="login-description">
                    Entre com suas credenciais
                </p>


                {/* ==============================================
                    FORMULÁRIO
                    ============================================== */}

                <form onSubmit={handleLogin}>

                    {/* ==========================================
                        USUÁRIO
                        ========================================== */}

                    <div className="login-field">

                        <label className="login-label">
                            Usuário
                        </label>


                        <input
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(
                                    event.target.value
                                )
                            }
                            placeholder="Digite seu usuário"
                            autoComplete="username"
                            className="login-input"
                        />

                    </div>


                    {/* ==========================================
                        SENHA
                        ========================================== */}

                    <div
                        className="
                            login-field
                            login-field-password
                        "
                    >

                        <label className="login-label">
                            Senha
                        </label>


                        <input
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(
                                    event.target.value
                                )
                            }
                            placeholder="Digite sua senha"
                            autoComplete="current-password"
                            className="login-input"
                        />

                    </div>


                    {/* ==========================================
                        MENSAGEM DE ERRO
                        ========================================== */}

                    {errorMessage && (

                        <div className="login-error">
                            {errorMessage}
                        </div>

                    )}


                    {/* ==========================================
                        LOGIN
                        ========================================== */}

                    <button
                        type="submit"
                        className="login-submit"
                    >
                        Entrar
                    </button>

                </form>

            </div>

        </div>
    );
}