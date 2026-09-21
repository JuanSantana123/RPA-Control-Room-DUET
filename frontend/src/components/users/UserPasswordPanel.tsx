// ============================================================
// DUET CORE - USERS - PASSWORD PANEL
// ============================================================
//
// Formulário visual para alteração de senha de um usuário.
//
// Responsabilidade:
// - receber nova senha;
// - receber confirmação;
// - encaminhar salvamento;
// - encaminhar cancelamento.
//
// Este componente NÃO:
// - valida igualdade das senhas;
// - executa chamadas HTTP;
// - conhece o endpoint utilizado;
// - controla mensagens globais.
//
// Essas responsabilidades pertencem a useUserPassword.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface UserPasswordPanelProps {
    newPassword:
        string;

    setNewPassword:
        (value: string) => void;

    confirmNewPassword:
        string;

    setConfirmNewPassword:
        (value: string) => void;

    onCancel:
        () => void;

    onSave:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function UserPasswordPanel({
    newPassword,
    setNewPassword,
    confirmNewPassword,
    setConfirmNewPassword,
    onCancel,
    onSave,
}: UserPasswordPanelProps) {

    return (
        <section className="users-panel users-edit-panel">

            <div className="users-panel-header">

                <div className="users-panel-heading">

                    <div className="users-panel-icon">
                        🔑
                    </div>

                    <div>

                        <h2>
                            Alterar senha
                        </h2>

                        <p>
                            Defina uma nova senha para o usuário selecionado
                        </p>

                    </div>

                </div>

            </div>


            <div className="users-edit-content">

                <div className="users-form-grid">

                    <div className="users-field-group">

                        <label>
                            Nova senha
                        </label>

                        <input
                            type="password"
                            placeholder="Digite a nova senha"
                            value={newPassword}
                            onChange={(event) =>
                                setNewPassword(
                                    event.target.value
                                )
                            }
                        />

                    </div>


                    <div className="users-field-group">

                        <label>
                            Confirmar senha
                        </label>

                        <input
                            type="password"
                            placeholder="Confirme a nova senha"
                            value={confirmNewPassword}
                            onChange={(event) =>
                                setConfirmNewPassword(
                                    event.target.value
                                )
                            }
                        />

                    </div>

                </div>


                <div className="users-edit-actions">

                    <button
                        className="users-secondary-button"
                        onClick={onCancel}
                    >
                        Cancelar
                    </button>

                    <button
                        className="users-primary-button"
                        onClick={onSave}
                    >
                        Salvar nova senha
                    </button>

                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserPasswordPanel;