import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../components/navigation/Sidebar";
import Header from "../components/navigation/Header";

function MainLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    if (!navigationOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavigationOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [navigationOpen]);

  return (
    <div className="layout">
      <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
      <Sidebar open={navigationOpen} onClose={() => setNavigationOpen(false)} />
      {navigationOpen && (
        <button className="navigation-backdrop" type="button" aria-label="Fechar navegação" onClick={() => setNavigationOpen(false)} />
      )}
      <div className="app-main">
        <Header onMenuOpen={() => setNavigationOpen(true)} />
        <main className="content" id="main-content" tabIndex={-1}>
          <div className="route-transition" key={location.pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export default MainLayout;
