import { Outlet } from "react-router-dom";
import Sidebar from "../components/navigation/Sidebar";
import Header from "../components/navigation/Header";

/*
|--------------------------------------------------------------------------
| MAIN LAYOUT
|--------------------------------------------------------------------------
| Composição principal da aplicação.
|
| Responsabilidades:
| - Montar Sidebar
| - Montar Header
| - Renderizar a página atual
|--------------------------------------------------------------------------
*/

function MainLayout() {
    return (
        <div className="layout">

            {/* Navegação lateral */}
            <Sidebar />

            {/* Área principal */}
            <div className="app-main">

                {/* Cabeçalho superior */}
                <Header />

                {/* Conteúdo da página */}
                <main className="content">
                    <Outlet />
                </main>

            </div>

        </div>
    );
}

export default MainLayout;