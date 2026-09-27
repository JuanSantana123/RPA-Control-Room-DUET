// ============================================================
// DUET CORE - USERS - CREATE PANEL
// ============================================================
//
// Formulário visual de criação de usuários.
//
// Responsabilidade:
// - receber username;
// - receber nome completo;
// - receber senha inicial;
// - permitir seleção da Role inicial;
// - encaminhar a solicitação de criação.
//
// A decisão de exibir este componente continua pertencendo
// à página, baseada na permissão Users:create.
//
// Este componente NÃO:
// - cria usuários diretamente;
// - executa chamadas HTTP;
// - valida permissões;
// - carrega Roles.
// ============================================================

import type {
    UserAvailableRole,
} from "../../types/users";
import PremiumSelect from "../ui/PremiumSelect";
import { UserRound } from "lucide-react";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";


// ============================================================
// PROPS
// ============================================================

interface UserCreatePanelProps {
    username: string;

    setUsername:
        (value: string) => void;

    name: string;

    setName:
        (value: string) => void;

    password: string;

    setPassword:
        (value: string) => void;

    roles:
        UserAvailableRole[];

    selectedRoleId:
        number | "";

    setSelectedRoleId:
        (value: number | "") => void;

    onCreate:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function UserCreatePanel({
    username,
    setUsername,
    name,
    setName,
    password,
    setPassword,
    roles,
    selectedRoleId,
    setSelectedRoleId,
    onCreate,
}: UserCreatePanelProps) {

    return (
        <section className="users-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="users-panel-header ui-panel-header">

                <div className="users-panel-heading ui-panel-header__identity">

                    <div className="users-panel-icon ui-panel-header__icon">
                        <UserRound size={18} strokeWidth={1.8} aria-hidden="true" />
                    </div>

                    <div className="ui-panel-header__copy">

                        <h2>
                            Novo usuário
                        </h2>

                        <p>
                            Cadastre um novo acesso ao Control Room
                        </p>

                    </div>

                </div>

            </div>


            {/* ==================================================
                FORMULÁRIO
                ================================================== */}

            <div className="users-form-content">

                <div className="users-form-grid">

                    <TextField
                            id="new-user-username"
                            label="Nome de usuário"
                            type="text"
                            autoComplete="username"
                            placeholder="Digite o nome de usuário"
                            value={username}
                            onChange={(event) =>
                                setUsername(
                                    event.target.value
                                )
                            }
                    />


                    <TextField
                            id="new-user-name"
                            label="Nome completo"
                            type="text"
                            autoComplete="name"
                            placeholder="Digite o nome"
                            value={name}
                            onChange={(event) =>
                                setName(
                                    event.target.value
                                )
                            }
                    />


                    <TextField
                            id="new-user-password"
                            label="Senha inicial"
                            type="password"
                            autoComplete="new-password"
                            placeholder="Digite a senha"
                            value={password}
                            onChange={(event) =>
                                setPassword(
                                    event.target.value
                                )
                            }
                    />


                    <div className="users-field-group">

                        <label htmlFor="new-user-role">
                            Perfil inicial
                        </label>

                        <PremiumSelect
                            id="new-user-role"
                            value={selectedRoleId}
                            onChange={(event) => {

                                const value =
                                    event.target.value;

                                setSelectedRoleId(
                                    value
                                        ? Number(value)
                                        : ""
                                );
                            }}
                        >

                            <option value="">
                                Sem perfil
                            </option>

                            {roles.map(
                                (role) => (

                                    <option
                                        key={role.id}
                                        value={role.id}
                                    >
                                        {role.name}
                                    </option>

                                )
                            )}

                        </PremiumSelect>

                    </div>

                </div>


                <div className="users-form-actions">

                    <Button
                        variant="primary"
                        onClick={onCreate}
                    >
                        Criar usuário
                    </Button>

                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserCreatePanel;
