import { BrowserRouter, Routes, Route } from "react-router-dom";
// Importa o layout principal da aplicação.
import MainLayout from "./layouts/MainLayout";
// Importa o componente que impede o acesso
// às páginas internas sem uma sessão válida.
import ProtectedRoute from "./components/auth/ProtectedRoute";
// Importa a página de Dashboard.
import Dashboard from "./pages/Dashboard";
// Página de gerenciamento dos Agents/Maquinas que executam os Robôs.
import Agents from "./pages/Agents";
// Página de gerenciamento dos Robôs.
import Robots from "./pages/Robots";
// Página de desenvolvimento e testes das automações.
import Development from "./pages/Development";
// Página de desenvolvimento dos Robôs.
//
// O RobotStudio utiliza uma rota própria e ocupa a tela inteira,
// sem o MainLayout do Control Room.
import RobotStudio from "./pages/RobotStudio";
// Importa a página de Execuções.
import Executions from "./pages/Executions";
// Importa a página de Histórico.
import History from "./pages/History";
// Importa a página de Agendamentos.
import Schedules from "./pages/Schedules";
// Importa a página de Logs.
import Logs from "./pages/Logs";
// Página de gerenciamento do Vault e das credenciais.
import Vault from "./pages/Vault";
// Importa a página de gerenciamento das Roles.
import Roles from "./pages/Roles";
// Importa a tela de login que criamos.
// Essa página será exibida quando acessarmos /login.
import Login from "./pages/Login";
// Importa a página de gerenciamento dos usuários.
import Users from "./pages/Users";
// Importa o Provider responsável por disponibilizar
// o estado de autenticação para toda a aplicação.
import { AuthProvider } from "./context/AuthContext";
// ============================================================
// APLICAÇÃO PRINCIPAL
// ============================================================
//
// O React Router controla as páginas da aplicação.
//
// O MainLayout é compartilhado por todas as páginas.
//
// A estrutura fica:
//
// BrowserRouter
//     │
//     └── MainLayout
//             │
//             ├── Dashboard
//             ├── Agents
//             ├── Robôs
//             ├── Execuções
//             ├── Histórico
//             └── Agendamentos
//
// Neste momento somente Dashboard e Agents existem.
// As outras rotas serão adicionadas durante a migração.
// ============================================================

function App() {

    return (
        <AuthProvider>
            <BrowserRouter>

                <Routes>
                    {/* Rota pública da tela de login. */}
                    <Route
                        path="/login"
                        element={<Login />}
                    />


                    {/* ==================================================
                        DUET STUDIO
                        ==================================================

                        O Studio trabalha sobre um projeto de desenvolvimento.

                        O projectId identifica o workspace editável e não
                        uma versão publicada da área de Robôs.
                    */}

                    <Route
                        path="/development/:projectId/studio"
                        element={
                            <ProtectedRoute>
                                <RobotStudio />
                            </ProtectedRoute>
                        }
                    />

                    {/* ==================================================
                        LAYOUT PRINCIPAL
                        ==================================================
                        
                        Tudo que estiver dentro desta rota utilizará
                        o MainLayout.
                    */}

                    <Route
                        element={
                            <ProtectedRoute>
                                <MainLayout />
                            </ProtectedRoute>
                        }
                    >

                        {/* ==================================================
                            DASHBOARD
                            ==================================================
                        */}

                        <Route
                            path="/"
                            element={<Dashboard />}
                        />


                        {/* ==================================================
                            AGENTS
                            ==================================================
                        */}

                        <Route
                            path="/agents"
                            element={<Agents />}
                        />


                        {/* ==================================================
                            DESENVOLVIMENTO
                            ==================================================

                            Área destinada aos projetos em desenvolvimento,
                            testes e workspaces editáveis.
                        */}

                        <Route
                            path="/development"
                            element={<Development />}
                        />


                        {/* ==================================================
                            ROBÔS
                            ==================================================
                            
                            Área destinada às automações publicadas.
                        */}

                        <Route
                            path="/robots"
                            element={<Robots />}
                        />
                        {/* ==================================================
                            EXECUÇÕES
                            ==================================================
                            
                            Página de acompanhamento das execuções
                            dos robôs.
                        */}
                        <Route
                            path="/executions"
                            element={<Executions />}
                        />

                        {/* ==================================================
                            HISTÓRICO
                            ==================================================
                            
                            Página com as execuções finalizadas.
                        */}

                        <Route
                            path="/history"
                            element={<History />}
                        />

                        {/* ==================================================
                            AGENDAMENTOS
                            ==================================================
                            
                            Página de gerenciamento dos agendamentos.
                        */} 
                        <Route
                            path="/schedules"
                            element={<Schedules />}
                        />
                        {/* ==================================================
                            LOGS
                            ==================================================
                            
                            Página de acompanhamento dos logs.
                        */}
                        <Route 
                            path="/logs" 
                            element={<Logs />} 
                        />

                        {/* ==================================================
                            VAULT
                            ==================================================

                            Página de gerenciamento das credenciais.
                        */}
                        <Route
                            path="/vault"
                            element={<Vault />}
                        />

                        {/* ==================================================
                            ROLES
                            ==================================================

                            Página de gerenciamento dos perfis de acesso.
                        */}
                        <Route
                            path="/roles"
                            element={<Roles />}
                        />


                        {/* ==================================================
                            USUÁRIOS
                            ==================================================

                            Página de gerenciamento dos usuários do Control Room.
                        */}
                        <Route
                            path="/users"
                            element={<Users />}
                        />
                    </Route>

                </Routes>

            </BrowserRouter>
        </AuthProvider>                  
    );

}

export default App;