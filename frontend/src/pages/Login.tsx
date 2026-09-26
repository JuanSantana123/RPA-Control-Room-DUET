import { LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import { BrandMark } from "../components/brand/BrandMark";
import { ThemeSwitcher } from "../components/theme/ThemeSwitcher";
import { useLogin } from "../hooks/auth/useLogin";
import { Button } from "../components/ui/Button";
import { TextField } from "../components/ui/TextField";
import "../styles/login.css";

export default function Login() {
  const { username, setUsername, password, setPassword, errorMessage, isSubmitting, handleLogin } = useLogin();
  return (
    <main className="login-page">
      <div className="login-topbar"><ThemeSwitcher /></div>
      <section className="login-intro" aria-labelledby="login-product-title">
        <BrandMark />
        <div className="login-intro-copy">
          <span className="login-kicker">Orquestração de automações</span>
          <h1 id="login-product-title">Operação precisa.<br />Controle permanente.</h1>
          <p>Um ponto seguro para desenvolver, publicar e acompanhar seus robôs em toda a operação.</p>
        </div>
        <div className="login-trust"><ShieldCheck size={18} /><span>Ambiente privado do Control Room</span></div>
      </section>
      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-card">
          <div className="login-card-heading">
            <span className="login-eyebrow">Acesso seguro</span>
            <h2 className="login-title" id="login-title">Entre no DUET CORE</h2>
            <p className="login-description">Use as credenciais fornecidas pelo administrador.</p>
          </div>
          <form onSubmit={handleLogin} noValidate>
            <TextField
              id="username"
              label="Usuário"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Seu usuário"
              autoComplete="username"
              leadingIcon={<UserRound size={18} />}
              containerClassName="login-field"
              required
              autoFocus
            />
            <TextField
              id="password"
              label="Senha"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Sua senha"
              autoComplete="current-password"
              leadingIcon={<LockKeyhole size={18} />}
              containerClassName="login-field login-field-password"
              required
            />
            {errorMessage && <div className="login-error" role="alert">{errorMessage}</div>}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              className="login-submit"
              busy={isSubmitting}
              loadingLabel="Autenticando"
              disabled={!username || !password}
            >
              Entrar no Control Room
            </Button>
          </form>
          <p className="login-help">Problemas de acesso? Procure o administrador da sua instalação.</p>
        </div>
      </section>
    </main>
  );
}
