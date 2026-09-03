import { BrowserRouter, Routes, Route } from "react-router-dom";
// Importa o layout principal da aplicação.
import MainLayout from "./layouts/MainLayout";
// Importa a página de Dashboard.
import Dashboard from "./pages/Dashboard";
// Página de gerenciamento dos Agents/Maquinas que executam os Robôs.
import Agents from "./pages/Agents";
// Página de gerenciamento dos Robôs.
import Robots from "./pages/Robots";
// Importa a página de Execuções.
import Executions from "./pages/Executions";
// Importa a página de Histórico.
import History from "./pages/History";
// Importa a página de Agendamentos.
import Schedules from "./pages/Schedules";
// Importa a página de Logs.
import Logs from "./pages/Logs";

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

        <BrowserRouter>

            <Routes>

                {/* ==================================================
                    LAYOUT PRINCIPAL
                    ==================================================
                    
                    Tudo que estiver dentro desta rota utilizará
                    o MainLayout.
                */}

                <Route
                    element={<MainLayout />}
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
                        ROBÔS
                        ==================================================
                        
                        Página de gerenciamento dos Robôs.
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
                </Route>

            </Routes>

        </BrowserRouter>

    );

}

export default App;