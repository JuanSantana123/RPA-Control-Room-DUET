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

            <div className="users-panel-header">

                <div className="users-panel-heading">

                    <div className="users-panel-icon">
                        👤
                    </div>

                    <div>

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

                    <div className="users-field-group">

                        <label>
                            Username
                        </label>

                        <input
                            type="text"
                            placeholder="Digite o username"
                            value={username}
                            onChange={(event) =>
                                setUsername(
                                    event.target.value
                                )
                            }
                        />

                    </div>


                    <div className="users-field-group">

                        <label>
                            Nome completo
                        </label>

                        <input
                            type="text"
                            placeholder="Digite o nome"
                            value={name}
                            onChange={(event) =>
                                setName(
                                    event.target.value
                                )
                            }
                        />

                    </div>


                    <div className="users-field-group">

                        <label>
                            Senha inicial
                        </label>

                        <input
                            type="password"
                            placeholder="Digite a senha"
                            value={password}
                            onChange={(event) =>
                                setPassword(
                                    event.target.value
                                )
                            }
                        />

                    </div>


                    <div className="users-field-group">

                        <label>
                            Role inicial
                        </label>

                        <select
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
                                Sem Role
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

                        </select>

                    </div>

                </div>


                <div className="users-form-actions">

                    <button
                        className="users-primary-button"
                        onClick={onCreate}
                    >
                        Criar usuário
                    </button>

                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserCreatePanel;