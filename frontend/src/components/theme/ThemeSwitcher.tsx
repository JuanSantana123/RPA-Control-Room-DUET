import { MonitorCog, Moon, Sun } from "lucide-react";
import { useTheme, type ThemePreference } from "../../context/theme";

const options: Array<{
  value: ThemePreference;
  label: string;
  icon: typeof Sun;
}> = [
  { value: "light", label: "Usar tema claro", icon: Sun },
  { value: "dark", label: "Usar tema escuro", icon: Moon },
  { value: "system", label: "Seguir tema do sistema", icon: MonitorCog },
];

export function ThemeSwitcher() {
  const { preference, setPreference } = useTheme();

  return (
    <div className="theme-switcher" role="group" aria-label="Tema da interface">
      {options.map(({ value, label, icon: Icon }) => (
        <button
          key={value}
          type="button"
          className="theme-switcher__option"
          aria-label={label}
          aria-pressed={preference === value}
          title={label}
          onClick={() => setPreference(value)}
        >
          <Icon size={16} strokeWidth={1.9} aria-hidden="true" />
        </button>
      ))}
    </div>
  );
}
