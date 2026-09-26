import { lazy, Suspense } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import MainLayout from "./layouts/MainLayout";
import { PageSkeleton } from "./components/ui/Skeletons";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Agents = lazy(() => import("./pages/Agents"));
const Robots = lazy(() => import("./pages/Robots"));
const Development = lazy(() => import("./pages/Development"));
const RobotStudio = lazy(() => import("./pages/RobotStudio"));
const Executions = lazy(() => import("./pages/Executions"));
const History = lazy(() => import("./pages/History"));
const Schedules = lazy(() => import("./pages/Schedules"));
const Logs = lazy(() => import("./pages/Logs"));
const Vault = lazy(() => import("./pages/Vault"));
const Roles = lazy(() => import("./pages/Roles"));
const Users = lazy(() => import("./pages/Users"));
const ComponentLab = import.meta.env.DEV ? lazy(() => import("./pages/ComponentLab")) : null;

function PageLoading() {
  return <PageSkeleton />;
}

function NotFound() {
  return (
    <section className="not-found">
      <span className="not-found-code">404</span>
      <h2>Página não encontrada</h2>
      <p>O endereço informado não corresponde a uma área disponível do Control Room.</p>
      <Link className="ui-button ui-button--primary ui-button--md" to="/">
        <span className="ui-button__content">Voltar à visão geral</span>
      </Link>
    </section>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageLoading />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/development/:projectId/studio" element={<ProtectedRoute><RobotStudio /></ProtectedRoute>} />
            <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/development" element={<Development />} />
              <Route path="/robots" element={<Robots />} />
              <Route path="/executions" element={<Executions />} />
              <Route path="/history" element={<History />} />
              <Route path="/schedules" element={<Schedules />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/vault" element={<Vault />} />
              <Route path="/roles" element={<Roles />} />
              <Route path="/users" element={<Users />} />
              {ComponentLab && <Route path="/component-lab" element={<ComponentLab />} />}
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
