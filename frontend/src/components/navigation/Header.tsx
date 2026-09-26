import { Menu } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import { ThemeSwitcher } from "../theme/ThemeSwitcher";
import { IconButton } from "../ui/Button";

function Header({ onMenuOpen }: { onMenuOpen: () => void }) {
  const { user } = useAuth();
  const displayName = user?.name || user?.username || "Usuário";

  return (
    <header className="app-header">
      <IconButton
        className="mobile-menu-button"
        label="Abrir navegação"
        icon={<Menu size={20} aria-hidden="true" />}
        aria-controls="primary-navigation"
        onClick={onMenuOpen}
      />
      <div className="header-spacer" aria-hidden="true" />
      <div className="header-actions">
        <ThemeSwitcher />
        <div className="header-divider" aria-hidden="true" />
        <div className="header-user" title={displayName}>
          <div className="header-user-avatar" aria-hidden="true">{displayName.charAt(0).toUpperCase()}</div>
          <div className="header-user-info">
            <span className="header-user-name">{displayName}</span>
            <span className="header-user-role">{user?.username || "Sessão ativa"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
