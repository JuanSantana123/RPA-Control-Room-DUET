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

import { KeyRound } from "lucide-react";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";


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

            <div className="users-panel-header ui-panel-header">

                <div className="users-panel-heading ui-panel-header__identity">

                    <div className="users-panel-icon ui-panel-header__icon">
                        <KeyRound size={18} strokeWidth={1.8} aria-hidden="true" />
                    </div>

                    <div className="ui-panel-header__copy">

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

                    <TextField
                            id="new-user-password-value"
                            label="Nova senha"
                            type="password"
                            autoComplete="new-password"
                            placeholder="Digite a nova senha"
                            value={newPassword}
                            onChange={(event) =>
                                setNewPassword(
                                    event.target.value
                                )
                            }
                    />


                    <TextField
                            id="confirm-user-password-value"
                            label="Confirmar senha"
                            type="password"
                            autoComplete="new-password"
                            placeholder="Confirme a nova senha"
                            value={confirmNewPassword}
                            onChange={(event) =>
                                setConfirmNewPassword(
                                    event.target.value
                                )
                            }
                    />

                </div>


                <div className="users-edit-actions">

                    <Button
                        onClick={onCancel}
                    >
                        Cancelar
                    </Button>

                    <Button
                        variant="primary"
                        onClick={onSave}
                    >
                        Salvar nova senha
                    </Button>

                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserPasswordPanel;
