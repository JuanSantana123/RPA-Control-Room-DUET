import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const baseUrl = process.env.DUET_FRONTEND_URL ?? "http://localhost:5173";
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outputDir = path.resolve("..", ".e2e", "frontend-rebuild");
const allCases = [
  { name: "login-320-light", route: "/login", width: 320, height: 720, colorScheme: "light" },
  { name: "login-390-light", route: "/login", width: 390, height: 844, colorScheme: "light" },
  { name: "login-768-dark", route: "/login", width: 768, height: 1024, colorScheme: "dark" },
  { name: "login-1440-light", route: "/login", width: 1440, height: 1000, colorScheme: "light" },
  { name: "dashboard-390-light", route: "/", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "dashboard-1440-dark", route: "/", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "dashboard-390-reduced-motion", route: "/", width: 390, height: 844, colorScheme: "dark", authenticated: true, reducedMotion: "reduce" },
  { name: "agents-390-dark", route: "/agents", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "agents-1440-light", route: "/agents", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "agents-maintenance-390-light", route: "/agents", width: 390, height: 844, colorScheme: "light", authenticated: true, agentData: true, interaction: "agent-maintenance" },
  { name: "agents-maintenance-1440-dark", route: "/agents", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, agentData: true, interaction: "agent-maintenance" },
  { name: "agents-maintenance-editor-768-dark", route: "/agents", width: 768, height: 900, colorScheme: "dark", authenticated: true, agentData: true, interaction: "agent-maintenance-editor" },
  { name: "agents-health-attention-1440-light", route: "/agents", width: 1440, height: 1000, colorScheme: "light", authenticated: true, agentData: true, interaction: "agent-health-attention" },
  { name: "agents-readonly-1440-light", route: "/agents", width: 1440, height: 1000, colorScheme: "light", authenticated: true, agentData: true, readOnlyDomain: "Agents", interaction: "capability-readonly" },
  { name: "agents-create-error-persistent-1440-light", route: "/agents", width: 1440, height: 1000, colorScheme: "light", authenticated: true, interaction: "agent-create-error" },
  { name: "automations-overview-390-light", route: "/automations/overview", width: 390, height: 844, colorScheme: "light", authenticated: true, automationData: true },
  { name: "automations-overview-1440-dark", route: "/automations/overview", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, automationData: true },
  { name: "robots-390-light", route: "/automations/catalog/robots", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "robots-1440-dark", route: "/automations/catalog/robots", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "robots-folder-hit-area-390-dark", route: "/automations/catalog/robots", width: 390, height: 844, colorScheme: "dark", authenticated: true, automationData: true, interaction: "robot-folder-hit-area" },
  { name: "robots-folder-hit-area-1440-light", route: "/automations/catalog/robots", width: 1440, height: 1000, colorScheme: "light", authenticated: true, automationData: true, interaction: "robot-folder-hit-area" },
  { name: "robots-folder-create-768-light", route: "/automations/catalog/robots", width: 768, height: 900, colorScheme: "light", authenticated: true, automationData: true, interaction: "robot-folder-create" },
  { name: "robots-versions-390-dark", route: "/automations/catalog/robots", width: 390, height: 844, colorScheme: "dark", authenticated: true, robotData: true, interaction: "robot-versions" },
  { name: "robots-versions-1440-light", route: "/automations/catalog/robots", width: 1440, height: 1000, colorScheme: "light", authenticated: true, robotData: true, interaction: "robot-versions" },
  { name: "robots-readonly-1440-dark", route: "/automations/catalog/robots", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, robotData: true, readOnlyDomain: "Robots", interaction: "capability-readonly" },
  { name: "libraries-hierarchy-390-dark", route: "/automations/catalog/libraries", width: 390, height: 844, colorScheme: "dark", authenticated: true, libraryData: true, interaction: "library-folder-hierarchy" },
  { name: "libraries-hierarchy-1440-light", route: "/automations/catalog/libraries", width: 1440, height: 1100, colorScheme: "light", authenticated: true, libraryData: true, interaction: "library-folder-hierarchy" },
  { name: "libraries-readonly-1440-light", route: "/automations/catalog/libraries", width: 1440, height: 1100, colorScheme: "light", authenticated: true, libraryData: true, readOnlyDomain: "Libraries", interaction: "capability-readonly" },
  { name: "development-390-dark", route: "/automations/build", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "development-1440-light", route: "/automations/build", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "development-kanban-390-dark", route: "/automations/build", width: 390, height: 844, colorScheme: "dark", authenticated: true, kanbanData: true, interaction: "development-kanban" },
  { name: "development-kanban-1440-light", route: "/automations/build", width: 1440, height: 900, colorScheme: "light", authenticated: true, kanbanData: true, interaction: "development-kanban" },
  { name: "development-activity-390-dark", route: "/automations/build", width: 390, height: 844, colorScheme: "dark", authenticated: true, kanbanData: true, interaction: "development-activity" },
  { name: "development-activity-1440-light", route: "/automations/build", width: 1440, height: 1000, colorScheme: "light", authenticated: true, kanbanData: true, interaction: "development-activity" },
  { name: "executions-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "executions-filter-navigation-768-dark", route: "/executions", width: 768, height: 900, colorScheme: "dark", authenticated: true, interaction: "execution-filters" },
  { name: "executions-details-390-dark", route: "/executions", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "execution-details" },
  { name: "executions-details-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true, interaction: "execution-details" },
  { name: "executions-queue-details-1440-dark", route: "/executions", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, queueData: true, interaction: "execution-queue-details" },
  { name: "executions-queue-details-390-light", route: "/executions", width: 390, height: 844, colorScheme: "light", authenticated: true, queueData: true, interaction: "execution-queue-details" },
  { name: "executions-empty-1440-light", route: "/executions", width: 1440, height: 900, colorScheme: "light", authenticated: true, forceEmpty: true },
  { name: "executions-readonly-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true, queueData: true, readOnlyDomain: "Executions", interaction: "capability-readonly" },
  { name: "history-1440-dark", route: "/history", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, historyData: true, interaction: "history-filter" },
  { name: "history-1440-light", route: "/history", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-390-light", route: "/schedules", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "schedules-1440-light", route: "/schedules", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-policy-1440-dark", route: "/schedules", width: 1440, height: 900, colorScheme: "dark", authenticated: true, scheduleData: true },
  { name: "schedules-modal-390-dark", route: "/schedules", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "schedule-modal" },
  { name: "schedules-modal-768-light", route: "/schedules", width: 768, height: 720, colorScheme: "light", authenticated: true, interaction: "schedule-modal" },
  { name: "schedules-readonly-1440-dark", route: "/schedules", width: 1440, height: 900, colorScheme: "dark", authenticated: true, scheduleData: true, readOnlyDomain: "Schedules", interaction: "capability-readonly" },
  { name: "vault-390-dark", route: "/vault", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "vault-1440-light", route: "/vault", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "vault-automation-data-390-light", route: "/vault", width: 390, height: 844, colorScheme: "light", authenticated: true, vaultData: true, interaction: "vault-automation-data" },
  { name: "vault-automation-data-1440-dark", route: "/vault", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, vaultData: true, interaction: "vault-automation-data" },
  { name: "vault-readonly-1440-light", route: "/vault", width: 1440, height: 1000, colorScheme: "light", authenticated: true, vaultData: true, readOnly: true, interaction: "vault-readonly" },
  { name: "roles-390-light", route: "/roles", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "roles-1440-dark", route: "/roles", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "roles-readonly-1440-light", route: "/roles", width: 1440, height: 1000, colorScheme: "light", authenticated: true, roleData: true, readOnlyDomain: "Roles", interaction: "capability-readonly" },
  { name: "users-390-light", route: "/users", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "users-readonly-1440-dark", route: "/users", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, userData: true, readOnlyDomain: "Users", interaction: "capability-readonly" },
  { name: "logs-390-light", route: "/logs", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "logs-explorer-1440-dark", route: "/logs", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, interaction: "logs-filter" },
  { name: "studio-390-dark", route: "/development/1/studio", width: 390, height: 844, colorScheme: "dark", authenticated: true, studio: true },
  { name: "studio-1440-light", route: "/development/1/studio", width: 1440, height: 1000, colorScheme: "light", authenticated: true, studio: true },
  { name: "development-create-390-dark", route: "/automations/build", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "development-create" },
  { name: "development-create-1440-dark", route: "/automations/build", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, interaction: "development-create" },
];
const requestedCase = process.env.DUET_VISUAL_CASE;
const cases = requestedCase
  ? allCases.filter((testCase) => testCase.name === requestedCase)
  : allCases;

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const results = [];

try {
  for (const testCase of cases) {
    console.log(`[visual] ${testCase.name}`);
    const context = await browser.newContext({
      viewport: { width: testCase.width, height: testCase.height },
      colorScheme: testCase.colorScheme,
      reducedMotion: testCase.reducedMotion ?? "no-preference",
      locale: "pt-BR",
    });
    const page = await context.newPage();
    const consoleErrors = [];
    const pageErrors = [];
    const unavailableApiRequests = [];
    page.on("console", (message) => {
      if (message.type() === "error" && !message.text().includes("ERR_CONNECTION_REFUSED")) {
        consoleErrors.push(message.text());
      }
    });
    page.on("requestfailed", (request) => {
      if (request.url().startsWith("http://127.0.0.1:9000") || request.url().startsWith("http://localhost:9000")) {
        unavailableApiRequests.push(request.url());
      }
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));

    const mockApi = async (route) => {
        const pathname = new URL(route.request().url()).pathname;
        const method = route.request().method();
        const permissions = [
          "Dashboard:view", "Agents:view", "Agents:create", "Agents:edit", "Agents:delete", "Agents:bootstrap", "Development:view", "Development:create", "Development:edit",
          "Development:move_stage", "Development:delete", "Development:publish", "Development:trash_view",
          "Development:restore", "Development:permanent_delete", "Development:checkout",
          "Development:force_checkout_release", "Robots:view", "Robots:create", "Robots:delete", "Executions:view", "Executions:execute", "Executions:stop", "Executions:cancel",
          "History:view", "Schedules:view", "Schedules:create", "Schedules:edit", "Schedules:delete", "Vault:view", "Vault:create", "Vault:edit", "Vault:delete",
          "DeviceCredentials:view", "DeviceCredentials:create", "DeviceCredentials:edit", "DeviceCredentials:delete", "Roles:view", "Roles:create", "Roles:edit", "Roles:delete",
          "Users:view", "Users:create", "Users:edit", "Users:delete", "Logs:view", "Libraries:view",
          "Libraries:create", "Libraries:edit", "Libraries:delete", "Libraries:publish", "Libraries:use",
        ].filter((permission) => {
          if (testCase.readOnly && /^(?:Vault|DeviceCredentials):(?:create|edit|delete)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Agents" && /^Agents:(?:create|edit|delete|bootstrap)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Robots" && /^(?:Robots:(?:create|delete)|Executions:execute|Development:create|Libraries:)/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Libraries" && /^Libraries:(?:create|edit|delete|publish|use)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Executions" && /^Executions:(?:execute|stop|cancel)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Schedules" && /^Schedules:(?:create|edit|delete)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Roles" && /^Roles:(?:create|edit|delete)$/.test(permission)) return false;
          if (testCase.readOnlyDomain === "Users" && /^Users:(?:create|edit|delete)$/.test(permission)) return false;
          return true;
        });
        const emptyCollections = {
          agents: [], robots: [], folders: [], executions: [], schedules: [], roles: [], users: [],
          permissions: [], credentials: [], logs: [], projects: [], cards: [], columns: [], libraries: [],
          dependencies: [], versions: [], tree: [],
        };
        const body = method === "PATCH" && pathname.endsWith("/availability")
          ? { status: "success", message: "Device colocado em manutenção.", agent: { agent_id: "runner-fin-01", name: "Financeiro 01", environment: "production", host: "FIN-RPA-01", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: false, maintenance_reason: "Atualização preventiva do runtime", availability_updated_at: "2026-09-26T15:00:00", last_heartbeat: "2026-09-26T14:58:30", heartbeat_age_seconds: 8, health_state: "healthy", session_status: "ready", username: "duet.rpa", execution_username: "duet.rpa", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] } }
          : pathname === "/auth/me"
          ? testCase.authenticated
            ? { status: "success", user: { id: 1, username: "operador", name: "Operador DUET", is_active: 1, permissions } }
            : { status: "unauthenticated" }
          : pathname === "/dashboard/stats"
            ? { total_agents: 12, agents_online: 9, total_robots: 48 }
          : pathname === "/agents" && method === "POST" && testCase.interaction === "agent-create-error"
            ? { status: "error", error_code: "agent_token_key_unavailable", message: "O dispositivo não pôde ser criado porque a chave de proteção dos tokens dos Agents não está configurada no Control Room." }
          : pathname === "/agents"
            ? { status: "success", total: testCase.agentData ? 3 : 0, agents: testCase.agentData ? [
                { agent_id: "runner-fin-01", name: "Financeiro 01", environment: "production", host: "FIN-RPA-01", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: true, maintenance_reason: null, availability_updated_at: "2026-09-26T10:00:00", last_heartbeat: "2026-09-26T14:58:30", heartbeat_age_seconds: 8, health_state: "healthy", session_status: "ready", username: "duet.rpa", execution_username: "duet.rpa", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
                { agent_id: "runner-fiscal-02", name: "Fiscal 02", environment: "development", host: "FISCAL-RPA-02", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: false, maintenance_reason: "Atualização programada do Windows", availability_updated_at: "2026-09-26T13:40:00", last_heartbeat: "2026-09-26T14:57:10", heartbeat_age_seconds: 20, health_state: "healthy", session_status: "ready", username: "duet.fiscal", execution_username: "duet.fiscal", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
                { agent_id: "runner-rh-03", name: "Recursos Humanos 03", environment: "production", host: "RH-RPA-03", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: true, maintenance_reason: null, availability_updated_at: null, last_heartbeat: "2026-09-26T14:55:00", heartbeat_age_seconds: 210, health_state: "stale", session_status: "ready", username: "duet.rh", execution_username: "duet.rh", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
              ] : [] }
          : pathname === "/agents/execution/available-agents"
            ? { status: "success", agents: testCase.automationData ? [
                { agent_id: "runner-fin-01", name: "Financeiro 01", status: "online", session_status: "ready", host: "FIN-RPA-01", port: 8000, rpa_directory: "C:\\DUET\\Robots", username: "duet.rpa" },
                { agent_id: "runner-rh-03", name: "Recursos Humanos 03", status: "online", session_status: "ready", host: "RH-RPA-03", port: 8000, rpa_directory: "C:\\DUET\\Robots", username: "duet.rh" },
              ] : [] }
          : pathname === "/development/projects"
            ? { status: "success", projects: testCase.automationData || testCase.kanbanData ? [
                { id: 37, name: "Conciliação bancária — regra fiscal", status: "modified", updated_at: "2026-09-26T18:30:00Z", checkout: { id: 8, user_id: 1 } },
                { id: 36, name: "Importação de documentos de transporte", status: "draft", updated_at: "2026-09-26T16:10:00Z", checkout: null },
                { id: 35, name: "Validação de fornecedores", status: "draft", updated_at: "2026-09-25T13:40:00Z", checkout: null },
              ] : [] }
          : pathname === "/development/workflow/board"
            ? { status: "success", stages: testCase.kanbanData ? [
                { id: 1, code: "BACKLOG", name: "Backlog", position: 1, is_active: true, total_projects: 1, projects: [{ id: 37, name: "Conciliação bancária", description: "Revisar conciliação mensal", status: "modified", current_stage_id: 1, base_robot_id: null, base_robot_name: null, base_version: null, folder_id: null, created_by: 1, created_at: "2026-09-20T10:00:00Z", updated_at: "2026-09-26T18:30:00Z", functional_responsible_id: null, technical_responsible_id: null, start_date: null, due_date: null, effort_hours: null, deleted_at: null, deleted_by: null, is_active: true }] },
                { id: 2, code: "DEVELOPMENT", name: "Em desenvolvimento", position: 2, is_active: true, total_projects: 1, projects: [{ id: 36, name: "Projeto de validação visual", description: "Validar o fluxo completo", status: "draft", current_stage_id: 2, base_robot_id: null, base_robot_name: null, base_version: null, folder_id: null, created_by: 1, created_at: "2026-09-21T10:00:00Z", updated_at: "2026-09-26T16:10:00Z", functional_responsible_id: null, technical_responsible_id: null, start_date: null, due_date: null, effort_hours: null, deleted_at: null, deleted_by: null, is_active: true }] },
                { id: 3, code: "READY_FOR_TEST", name: "Pronto para testes", position: 3, is_active: true, total_projects: 0, projects: [] },
                { id: 4, code: "TESTING", name: "Em testes", position: 4, is_active: true, total_projects: 0, projects: [] },
                { id: 5, code: "HOMOLOGATION", name: "Homologação", position: 5, is_active: true, total_projects: 0, projects: [] },
                { id: 6, code: "APPROVED", name: "Aprovado", position: 6, is_active: true, total_projects: 0, projects: [] },
                { id: 7, code: "PUBLISHED", name: "Publicado", position: 7, is_active: true, total_projects: 0, projects: [] },
              ] : [] }
          : pathname === "/development/card-users"
            ? { status: "success", users: [{ id: 1, name: "Operador DUET" }, { id: 2, name: "Marina Costa" }] }
          : pathname === "/development/projects/37/comments"
            ? { status: "success", project_id: 37, total: 2, comments: [
                { id: 8, event_key: "comment-8", kind: "comment", project_id: 37, user_id: 2, user_name: "Marina Costa", content: "Validação concluída. Consulte a [documentação](https://example.com/validacao).", attachments: [], created_at: "2026-09-26T17:30:00Z", updated_at: "2026-09-26T17:30:00Z" },
                { id: 12, event_key: "stage-movement-12", kind: "stage_movement", project_id: 37, user_id: 1, user_name: "Operador DUET", content: null, attachments: [], from_stage: { id: 2, code: "DEVELOPMENT", name: "Em desenvolvimento" }, to_stage: { id: 1, code: "BACKLOG", name: "Backlog" }, created_at: "2026-09-26T18:15:00Z", updated_at: "2026-09-26T18:15:00Z" },
              ] }
          : pathname === "/robot-folders"
            ? { status: "success", folders: testCase.automationData ? [{ id: 1, name: "Financeiro", parent_id: null }, { id: 2, name: "Fiscal", parent_id: null }, { id: 3, name: "RH", parent_id: null }, { id: 4, name: "Conciliações", parent_id: 1 }, { id: 5, name: "Fechamento mensal", parent_id: 4 }] : [] }
          : pathname === "/robots/root"
            ? { status: "success", total: testCase.robotData || testCase.automationData ? 1 : 0, robots: testCase.robotData || testCase.automationData ? [{ id: 12, name: "Conciliação financeira", filename: "conciliacao-financeira.zip", version: 4, file_hash: "a".repeat(64), file_path: "storage/releases/12/v4.zip" }] : [] }
          : pathname === "/robots/12/versions"
            ? { status: "success", robot: { id: 12, name: "Conciliação financeira", filename: "conciliacao-financeira.zip", current_version: 4 }, total: 3, versions: [
                { id: 104, version: 4, filename: "conciliacao-financeira-v4.zip", file_hash: "a".repeat(64), published_at: "2026-09-26T18:30:00Z", created_at: "2026-09-26T18:30:02Z", is_current: true, publisher: { id: 1, name: "Operador DUET", username: "operador" }, source_project: { id: 37, name: "Conciliação — regra fiscal setembro" } },
                { id: 103, version: 3, filename: "conciliacao-financeira-v3.zip", file_hash: "b".repeat(64), published_at: "2026-08-18T11:20:00Z", created_at: "2026-08-18T11:20:01Z", is_current: false, publisher: { id: 2, name: "Marina Costa", username: "marina" }, source_project: { id: 31, name: "Conciliação — tolerância bancária" } },
                { id: 102, version: 2, filename: "conciliacao-financeira-v2.zip", file_hash: "c".repeat(64), published_at: null, created_at: "2026-07-02T09:10:00Z", is_current: false, publisher: null, source_project: null },
              ] }
          : pathname === "/robots/12/versions/4/libraries"
            ? { status: "success", total: 2, libraries: [
                { library_id: 8, name: "Integração Bancária", import_name: "duet_bank", library_version_id: 19, version: "2.4.0", is_current_production: true },
                { library_id: 11, name: "Documentos Fiscais", import_name: "duet_fiscal", library_version_id: 22, version: "1.8.2", is_current_production: false },
              ] }
          : pathname === "/libraries/tree"
            ? { status: "success", total_folders: testCase.libraryData ? 3 : 0, total_libraries: testCase.libraryData ? 2 : 0, tree: testCase.libraryData ? [{
                type: "folder", id: 31, name: "Integrações", parent_id: null, created_by: 1, created_at: "2026-08-10T12:00:00Z", updated_at: "2026-09-20T09:00:00Z", is_active: true, children: [{
                  type: "folder", id: 32, name: "Financeiro", parent_id: 31, created_by: 1, created_at: "2026-08-10T12:00:00Z", updated_at: "2026-09-20T09:00:00Z", is_active: true, children: [{
                    type: "library", id: 45, name: "Conciliação bancária", import_name: "duet_bank", description: "Rotinas compartilhadas de conciliação.", folder_id: 32, created_by: 1, created_at: "2026-08-12T12:00:00Z", updated_at: "2026-09-22T09:00:00Z", is_active: true,
                  }],
                }, {
                  type: "library", id: 44, name: "Conectores ERP", import_name: "duet_erp", description: "Conectores reutilizáveis para os ERPs homologados.", folder_id: 31, created_by: 1, created_at: "2026-08-11T12:00:00Z", updated_at: "2026-09-21T09:00:00Z", is_active: true,
                }],
              }, {
                type: "folder", id: 33, name: "Documentos", parent_id: null, created_by: 1, created_at: "2026-08-13T12:00:00Z", updated_at: "2026-09-23T09:00:00Z", is_active: true, children: [],
              }] : [] }
          : pathname === "/vault/folders"
            ? { status: "success", folders: testCase.vaultData ? [
                { id: 4, name: "Financeiro", parent_id: null, children: [
                  { id: 7, name: "Produção", parent_id: 4, children: [] },
                ] },
              ] : [] }
          : pathname === "/vault/credentials"
            ? { status: "success", credentials: testCase.vaultData ? [
                { id: 21, name: "ERP Financeiro", folder_id: 7, created_at: "2026-06-12T10:00:00Z", updated_at: "2026-09-25T16:40:00Z", fields: [
                  { id: 81, name: "Usuário", value: "svc.duet.financeiro", is_secret: false },
                  { id: 82, name: "Senha", value: "********", is_secret: true },
                  { id: 83, name: "Tenant", value: "BR-SP-01", is_secret: false },
                ] },
                { id: 22, name: "Portal Bancário", folder_id: 7, created_at: "2026-07-08T09:30:00Z", updated_at: "2026-09-20T13:15:00Z", fields: [
                  { id: 84, name: "Login", value: "tesouraria.rpa", is_secret: false },
                  { id: 85, name: "Senha", value: "********", is_secret: true },
                  { id: 86, name: "Token MFA", value: "********", is_secret: true },
                ] },
              ] : [] }
          : pathname === "/schedules"
              ? { status: "success", total: testCase.scheduleData ? 1 : 0, schedules: testCase.scheduleData ? [{ id: 18, robot_id: 12, robot_name: "Conciliação financeira", agent_id: null, agent_name: "Automático", tipo: "daily", data_inicio: "2026-09-20T08:00:00", horario: "08:00", dias_semana: null, ativo: true, proxima_execucao: "2026-09-27T08:00:00", ultima_execucao: "2026-09-25T08:00:05", intervalo_ativo: false, intervalo_valor: null, intervalo_unidade: null, horario_fim: null, misfire_policy: "skip", misfire_grace_seconds: 600, ultima_ocorrencia_perdida: "2026-09-26T08:00:00" }] : [] }
            : pathname === "/schedules/options"
              ? { status: "success", timezone: "America/Sao_Paulo", robots: [{ id: 12, name: "Conciliação financeira" }], agents: [{ agent_id: "runner-01", name: "Dispositivo Financeiro", status: "online" }] }
            : pathname === "/roles/permissions"
              ? testCase.roleData ? [{ id: 1, resource: "Robots", action: "view" }, { id: 2, resource: "Robots", action: "create" }] : []
            : pathname === "/roles/7/permissions"
              ? testCase.roleData ? [{ id: 1, resource: "Robots", action: "view" }] : []
            : pathname === "/roles"
              ? testCase.roleData ? [{ id: 7, name: "Operação assistida", description: "Consulta execuções e dispositivos sem alterar configurações." }] : []
            : pathname === "/auth/users"
              ? testCase.userData ? [{ id: 12, username: "ana.operacao", name: "Ana Operação", is_active: 1, roles: [{ id: 7, name: "Operação assistida" }] }] : []
            : pathname === "/executions"
              ? { status: "success", total: testCase.forceEmpty ? 0 : 1, queue_warning_seconds: 900, executions: testCase.forceEmpty ? [] : [{ id: 142, source_type: "robot", robot_id: 9, robot_version: 3, project_id: null, robot_name: "Conciliação financeira", filename: "conciliacao.zip", folder_name: "Financeiro / Fechamento", user_id: 1, username: "operador", user_name: "Operador DUET", agent_id: "runner-03", agent_name: "Financeiro 03", schedule_id: null, schedule_run_id: null, pid: testCase.queueData ? null : 4872, status: testCase.queueData ? "queued" : "running", priority: testCase.queueData ? "urgent" : "normal", queued_at: testCase.queueData ? "2026-09-26T10:00:00Z" : null, queue_position: testCase.queueData ? 1 : null, started_at: testCase.queueData ? null : "2026-09-26T14:45:00Z", finished_at: null, error_message: null }] }
              : pathname === "/executions/history"
                ? { status: "success", executions: testCase.historyData ? [
                    { id: 381, robot_name: "Conciliação financeira", folder_name: "Financeiro / Fechamento", user_id: 1, username: "operador", user_name: "Operador DUET", agent_name: "Financeiro 03", started_at: "2026-09-26T17:40:00Z", finished_at: "2026-09-26T17:41:18Z", status: "success", error_message: null },
                    { id: 380, robot_name: "Importação fiscal", folder_name: "Fiscal", user_id: 2, username: "ana.operacao", user_name: "Ana Operação", agent_name: "Fiscal 02", started_at: "2026-09-26T16:10:00Z", finished_at: "2026-09-26T16:10:23Z", status: "error", error_message: "Falha controlada ao validar o arquivo de entrada." },
                  ] : [] }
              : pathname === "/logs"
                ? { status: "success", total: 3, truncated: false, logs: [
                    { timestamp: "2026-09-26T18:42:03Z", level: "ERROR", message: "Falha controlada ao consultar o Device.", event: "agent_health_failed", request_id: "req-9001", service: "control-room" },
                    { timestamp: "2026-09-26T18:41:55Z", level: "WARNING", message: "Device sem heartbeat dentro da janela esperada.", event: "agent_offline" },
                    { timestamp: "2026-09-26T18:41:30Z", level: "INFO", message: "Ciclo de monitoramento concluído.", event: "agent_monitor_cycle" },
                  ] }
              : pathname === "/development/projects/1"
                ? { project: { id: 1, name: "Validação visual", description: "Projeto sintético para auditoria local", folder_id: null, status: "development", base_robot_id: null, base_version: null, created_by: 1, created_at: "2026-09-26T12:00:00Z", updated_at: "2026-09-26T12:00:00Z", is_active: true } }
                : pathname === "/development/projects/1/checkout"
                  ? { checked_out: false, owns_checkout: false, checkout: null }
                  : emptyCollections;
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    };
    await context.route("http://127.0.0.1:9000/**", mockApi);
    await context.route("http://localhost:9000/**", mockApi);

    await page.goto(`${baseUrl}${testCase.route}`, { waitUntil: "networkidle" });
    const readySelector = testCase.authenticated
      ? testCase.studio ? ".robot-studio" : "#main-content"
      : "#login-title";
    try {
      await page.locator(readySelector).waitFor({ timeout: 8000 });
    } catch {
      await page.screenshot({ path: path.join(outputDir, `${testCase.name}-render-failure.png`), fullPage: true });
      results.push({
        ...testCase,
        rendered: false,
        url: page.url(),
        bodyText: (await page.locator("body").innerText()).slice(0, 500),
        consoleErrors,
        pageErrors,
        unavailableApiRequests,
      });
      await context.close();
      continue;
    }
    await page.waitForTimeout(120);
    let scheduleRecoveryWorks = null;
    if (testCase.interaction === "schedule-modal") {
      await page.getByRole("button", { name: "Novo agendamento" }).click();
      const dialog = page.getByRole("dialog", { name: "Novo agendamento" });
      await dialog.waitFor();
      await dialog.getByRole("combobox", { name: "Ocorrência vencida" }).click();
      await page.getByRole("option", { name: "Ignorar e seguir a agenda" }).click();
      await dialog.getByRole("combobox", { name: "Tolerância" }).click();
      await page.getByRole("option", { name: "10 minutos" }).click();
      scheduleRecoveryWorks = await dialog.getByText("A ocorrência antiga não gera execução").isVisible();
      await page.waitForTimeout(180);
    }
    if (testCase.interaction === "development-create") {
      await page.getByRole("button", { name: "Novo projeto" }).first().click();
      await page.getByRole("heading", { name: "Crie um projeto de automação" }).waitFor();
      await page.waitForTimeout(180);
    }
    let kanbanSpacingWorks = null;
    if (testCase.interaction === "development-kanban") {
      await page.getByRole("button", { name: /Kanban/ }).click();
      const board = page.locator(".kanban-board");
      await board.waitFor();
      await page.waitForTimeout(180);
      kanbanSpacingWorks = await board.evaluate(async (element) => {
        const columns = [...element.querySelectorAll(".kanban-column")];
        const first = columns[0];
        const last = columns.at(-1);
        if (!first || !last) return false;
        const boardRect = element.getBoundingClientRect();
        const startGap = first.getBoundingClientRect().left - boardRect.left;
        element.scrollLeft = element.scrollWidth;
        await new Promise((resolve) => requestAnimationFrame(() => resolve()));
        const endGap = boardRect.right - last.getBoundingClientRect().right;
        element.scrollLeft = 0;
        return startGap >= 12 && endGap >= 12;
      });
    }
    let activityTimelineWorks = null;
    if (testCase.interaction === "development-activity") {
      await page.getByRole("button", { name: /Kanban/ }).click();
      await page.locator(".kanban-board").waitFor();
      await page.getByRole("button", { name: "Detalhes" }).first().click();
      const drawer = page.locator(".card-details-drawer");
      await drawer.waitFor();
      activityTimelineWorks = await drawer.locator(".card-comment--movement").getByText("Em desenvolvimento", { exact: true }).isVisible()
        && await drawer.getByRole("toolbar", { name: "Formatação do comentário" }).isVisible()
        && await drawer.getByRole("button", { name: "Anexar imagem" }).isVisible()
        && await drawer.getByRole("link", { name: "documentação" }).isVisible();
      await page.waitForTimeout(180);
    }
    let agentCreateErrorPersists = null;
    if (testCase.interaction === "agent-create-error") {
      await page.getByRole("spinbutton", { name: "Porta de comunicação" }).fill("8000");
      await page.getByRole("button", { name: "Cadastrar dispositivo" }).click();
      const errorBanner = page.getByRole("alert").filter({ hasText: "chave de proteção" });
      await errorBanner.waitFor();
      await page.waitForTimeout(2_500);
      agentCreateErrorPersists = await errorBanner.isVisible()
        && await page.getByRole("button", { name: "Repetir cadastro" }).isVisible();
    }
    let robotFolderCreateWorks = null;
    if (testCase.interaction === "robot-folder-create") {
      await page.locator(".robots-folders-panel").getByRole("button", { name: "Nova pasta" }).click();
      const dialog = page.getByRole("dialog", { name: "Nova pasta" });
      await dialog.waitFor();
      await dialog.getByRole("combobox", { name: "Criar dentro de" }).click();
      await page.getByRole("option", { name: "— Financeiro", exact: true }).click();
      const subfolderDialog = page.getByRole("dialog", { name: "Nova subpasta" });
      await subfolderDialog.getByRole("textbox", { name: "Nome da pasta" }).fill("Conferências");
      const destinationPreview = subfolderDialog.locator(".folder-editor-dialog__path-preview");
      const overlayBox = await page.locator(".folder-editor-overlay").boundingBox();
      const overlayCoversViewport = overlayBox !== null
        && Math.abs(overlayBox.x) <= 1
        && Math.abs(overlayBox.y) <= 1
        && Math.abs(overlayBox.width - testCase.width) <= 1
        && Math.abs(overlayBox.height - testCase.height) <= 1;
      robotFolderCreateWorks = overlayCoversViewport
        && await destinationPreview.getByText("Raiz de Robôs", { exact: true }).isVisible()
        && await destinationPreview.getByText("Financeiro", { exact: true }).isVisible()
        && await destinationPreview.getByText("Conferências", { exact: true }).isVisible()
        && await subfolderDialog.getByRole("button", { name: "Criar subpasta" }).isEnabled();
      await page.waitForTimeout(180);
    }
    let robotFolderHitAreaWorks = null;
    let robotFolderHitAreaDetails = null;
    let robotFolderHierarchyWorks = null;
    if (testCase.interaction === "robot-folder-hit-area") {
      const folderTree = page.locator(".robot-folders-tree");
      const financeRow = page.locator(".robot-folder-row").filter({ hasText: "Financeiro" }).first();
      await financeRow.waitFor();
      await financeRow.getByRole("button", { name: "Expandir pasta Financeiro" }).click();
      await page.waitForTimeout(120);
      const reconciliationsButton = folderTree.getByRole("button", { name: "Conciliações", exact: true });
      await reconciliationsButton.waitFor();
      await folderTree.getByRole("button", { name: "Expandir pasta Conciliações" }).click();
      const monthlyClosingButton = folderTree.getByRole("button", { name: "Fechamento mensal", exact: true });
      await monthlyClosingButton.waitFor();
      const folderSearch = page.getByRole("searchbox", { name: "Pesquisar pastas" });
      await folderSearch.fill("Fechamento");
      robotFolderHierarchyWorks = await financeRow.isVisible()
        && await reconciliationsButton.isVisible()
        && await monthlyClosingButton.isVisible();
      await page.getByRole("button", { name: "Limpar pesquisa de pastas" }).click();
      const menuButton = financeRow.getByRole("button", { name: "Ações da pasta Financeiro" });
      await menuButton.click();
      const menuKeepsSelectionIsolated = !(await financeRow.evaluate((element) => element.classList.contains("robot-folder-row-selected")));
      await menuButton.click();
      const selectionBox = await financeRow.locator(".robot-folder-select").boundingBox();
      if (selectionBox) {
        await page.mouse.click(selectionBox.x + selectionBox.width * 0.8, selectionBox.y + selectionBox.height / 2);
      }
      await page.waitForTimeout(120);
      const blankAreaSelects = await financeRow.evaluate((element) => element.classList.contains("robot-folder-row-selected"));
      const fiscalButton = page.locator(".robot-folders-tree").getByRole("button", { name: "Fiscal", exact: true });
      await fiscalButton.focus();
      await page.keyboard.press("Enter");
      const keyboardSelects = await fiscalButton.getAttribute("aria-pressed") === "true";
      robotFolderHitAreaWorks = Boolean(selectionBox) && menuKeepsSelectionIsolated && blankAreaSelects && keyboardSelects;
      robotFolderHitAreaDetails = { hasGeometry: Boolean(selectionBox), menuKeepsSelectionIsolated, blankAreaSelects, keyboardSelects };
      await page.waitForTimeout(180);
    }
    let robotVersionsWorks = null;
    if (testCase.interaction === "robot-versions") {
      await page.getByRole("button", { name: "Versões", exact: true }).click();
      const dialog = page.getByRole("dialog", { name: "Conciliação financeira" });
      await dialog.waitFor();
      await dialog.getByRole("button", { name: "Bibliotecas" }).first().click();
      robotVersionsWorks = await dialog.locator(".robot-version-number").filter({ hasText: "v4" }).isVisible()
        && await dialog.getByText("Vigente", { exact: true }).isVisible()
        && await dialog.getByText("Integração Bancária").isVisible()
        && await dialog.getByRole("button", { name: "Baixar v3" }).isVisible();
      await page.waitForTimeout(180);
    }
    let vaultAutomationWorks = null;
    if (testCase.interaction === "vault-automation-data") {
      const credentialRequest = page.waitForRequest((request) => {
        const url = new URL(request.url());
        return url.pathname === "/vault/credentials" && url.searchParams.get("folder_id") === "7";
      });
      await page.getByRole("button", { name: "Produção", exact: true }).click();
      await credentialRequest;
      await page.getByText("ERP Financeiro", { exact: true }).waitFor();
      const search = page.getByRole("searchbox", { name: "Buscar credenciais de automação" });
      await search.fill("tesouraria");
      vaultAutomationWorks = await page.locator(".vault-credential-card").count() === 1
        && await page.getByText("Portal Bancário", { exact: true }).isVisible()
        && await page.getByText("2 campos protegidos", { exact: true }).isVisible()
        && await page.getByRole("button", { name: "Copiar Login" }).isVisible();
      await page.waitForTimeout(180);
    }
    let vaultReadOnlyWorks = null;
    if (testCase.interaction === "vault-readonly") {
      const credentialRequest = page.waitForRequest((request) => {
        const url = new URL(request.url());
        return url.pathname === "/vault/credentials" && url.searchParams.get("folder_id") === "7";
      });
      await page.getByRole("button", { name: "Produção", exact: true }).click();
      await credentialRequest;
      await page.getByText("ERP Financeiro", { exact: true }).waitFor();
      vaultReadOnlyWorks = await page.getByText("Somente leitura", { exact: true }).count() === 2
        && await page.getByRole("button", { name: "Nova pasta" }).count() === 0
        && await page.getByRole("button", { name: "Nova credencial" }).count() === 0
        && await page.getByRole("button", { name: /Editar|Excluir|Subpasta/ }).count() === 0
        && await page.getByRole("button", { name: "Copiar Usuário" }).isVisible();
      await page.waitForTimeout(180);
    }
    let filterNavigationWorks = null;
    if (testCase.interaction === "execution-filters") {
      await page.getByRole("combobox", { name: "Robô" }).click();
      await page.getByRole("option", { name: "Conciliação financeira", exact: true }).click();
      await page.waitForURL(/robot=Concilia/);
      await page.waitForFunction(() => document.querySelector('#filtro-robo')?.textContent?.includes("Conciliação financeira"));
      await page.goBack();
      await page.waitForURL((url) => !url.searchParams.has("robot"));
      await page.waitForFunction(() => document.querySelector('#filtro-robo')?.textContent?.includes("Todos os robôs"));
      await page.waitForFunction(() => document.querySelector('button') && [...document.querySelectorAll('button')].find((button) => button.textContent?.includes("Limpar filtros"))?.disabled);
      filterNavigationWorks = true;
    }
    let executionDetailsWorks = null;
    if (testCase.interaction === "execution-details") {
      await page.getByRole("button", { name: "Ver detalhes da execução 142" }).click();
      const dialog = page.getByRole("dialog", { name: "Execução #142" });
      await dialog.waitFor();
      executionDetailsWorks = await dialog.locator(".execution-timeline__step").count() === 3
        && await dialog.getByRole("button", { name: "Parar execução" }).isVisible()
        && await dialog.getByText("Financeiro / Fechamento").isVisible();
      await page.waitForTimeout(180);
    }
    let executionQueueDetailsWorks = null;
    if (testCase.interaction === "execution-queue-details") {
      await page.getByRole("button", { name: "Ver detalhes da execução 142" }).click();
      const dialog = page.getByRole("dialog", { name: "Execução #142" });
      await dialog.waitFor();
      executionQueueDetailsWorks = await dialog.getByText("Gestão da fila").isVisible()
        && await dialog.getByText("1ª posição neste dispositivo").isVisible()
        && await dialog.getByText("Requer atenção").isVisible()
        && await dialog.getByRole("combobox", { name: "Prioridade operacional" }).isVisible();
      if (testCase.width <= 600) await dialog.locator(".execution-queue-panel").scrollIntoViewIfNeeded();
      await page.waitForTimeout(180);
    }
    let logsExplorerWorks = null;
    if (testCase.interaction === "logs-filter") {
      await page.getByRole("combobox", { name: "Nível" }).click();
      await page.getByRole("option", { name: "Erros", exact: true }).click();
      await page.getByRole("searchbox", { name: "Pesquisar registros" }).fill("req-9001");
      await page.getByRole("switch", { name: /Atualização automática/ }).uncheck();
      await page.getByText("Atualização pausada").waitFor();
      logsExplorerWorks = await page.locator(".logs-entry").count() === 1
        && await page.getByText("referência: req-9001").isVisible();
    }
    let agentMaintenanceWorks = null;
    if (testCase.interaction === "agent-maintenance") {
      await page.getByRole("combobox", { name: "Disponibilidade" }).click();
      await page.getByRole("option", { name: "Em manutenção" }).click();
      await page.getByText("Atualização programada do Windows").waitFor();
      agentMaintenanceWorks = await page.locator(".agent-card").count() === 1
        && await page.getByText("Fiscal 02").isVisible()
        && await page.locator(".agent-maintenance-badge").getByText("Manutenção", { exact: true }).isVisible();
      await page.waitForTimeout(180);
    }
    let agentMaintenanceEditorWorks = null;
    if (testCase.interaction === "agent-maintenance-editor") {
      const card = page.locator(".agent-card").filter({ hasText: "Financeiro 01" });
      await card.getByRole("switch", { name: /Novas reservas habilitadas/ }).click();
      const reason = card.getByRole("textbox", { name: "Motivo da manutenção" });
      await reason.waitFor();
      const submit = card.getByRole("button", { name: "Pausar novas execuções" });
      const requiredStateWorks = await submit.isDisabled();
      await reason.fill("Atualização preventiva do runtime");
      await submit.click();
      await card.getByText("Atualização preventiva do runtime").waitFor();
      agentMaintenanceEditorWorks = requiredStateWorks
        && await card.locator(".agent-maintenance-badge").isVisible();
      await page.waitForTimeout(180);
    }
    let agentHealthAttentionWorks = null;
    if (testCase.interaction === "agent-health-attention") {
      await page.getByRole("combobox", { name: "Disponibilidade" }).click();
      await page.getByRole("option", { name: "Requer atenção" }).click();
      const card = page.locator(".agent-card").filter({ hasText: "Recursos Humanos 03" });
      await card.waitFor();
      agentHealthAttentionWorks = await page.locator(".agent-card").count() === 1
        && await card.getByText("Heartbeat atrasado").isVisible()
        && await card.getByText("Há 3 min").isVisible();
      await page.waitForTimeout(180);
    }
    let historyFilterWorks = null;
    if (testCase.interaction === "history-filter") {
      await page.getByText("Conciliação financeira", { exact: true }).waitFor();
      const search = page.getByRole("searchbox", { name: "Pesquisar no histórico" });
      await search.fill("registro inexistente");
      await page.getByRole("heading", { name: "Nenhuma execução corresponde aos filtros" }).waitFor();
      await page.locator(".ui-empty-state").getByRole("button", { name: "Limpar filtros" }).click();
      await page.getByRole("combobox", { name: "Filtrar histórico por situação" }).click();
      await page.getByRole("option", { name: "Erro", exact: true }).click();
      const statusWorks = await page.getByText("Importação fiscal", { exact: true }).isVisible()
        && await page.getByText("Conciliação financeira", { exact: true }).count() === 0;
      await page.getByRole("button", { name: "Limpar filtros" }).click();
      historyFilterWorks = statusWorks
        && await page.getByText("Conciliação financeira", { exact: true }).isVisible();
      await page.waitForTimeout(180);
    }
    let libraryFolderHierarchyWorks = null;
    if (testCase.interaction === "library-folder-hierarchy") {
      const module = page.locator(".libraries-module");
      const financeFolder = module.getByRole("button", { name: "Financeiro, pasta" });
      await financeFolder.waitFor();
      await financeFolder.click();

      await module.getByRole("button", { name: "Recolher", exact: true }).click();
      const selectedPathPreserved = await financeFolder.isVisible();

      await module.getByRole("button", { name: "Expandir", exact: true }).click();
      const nestedLibraryVisible = await module.getByText("Conciliação bancária", { exact: true }).isVisible();

      const search = module.getByRole("searchbox", { name: "Buscar no catálogo de bibliotecas" });
      await search.fill("conciliação");
      const searchKeepsAncestors = await module.getByText("Integrações", { exact: true }).isVisible()
        && await financeFolder.isVisible()
        && await module.getByText("Conciliação bancária", { exact: true }).isVisible();
      await search.fill("");

      await module.getByRole("button", { name: "Criar subpasta em Financeiro" }).click();
      const dialog = page.getByRole("dialog", { name: "Nova subpasta" });
      await dialog.waitFor();
      const destinationText = (await dialog.locator(".folder-editor-dialog__path").textContent())
        ?.replace(/\s+/g, " ")
        .trim() ?? "";
      const overlayBox = await page.locator(".folder-editor-overlay").boundingBox();
      const destinationIsExplicit = destinationText.includes("Bibliotecas")
        && destinationText.includes("Integrações")
        && destinationText.includes("Financeiro");
      const overlayCoversViewport = overlayBox !== null
        && Math.abs(overlayBox.x) <= 1
        && Math.abs(overlayBox.y) <= 1
        && Math.abs(overlayBox.width - testCase.width) <= 1
        && Math.abs(overlayBox.height - testCase.height) <= 1;
      libraryFolderHierarchyWorks = selectedPathPreserved
        && nestedLibraryVisible
        && searchKeepsAncestors
        && destinationIsExplicit
        && overlayCoversViewport;
    }
    let capabilityReadOnlyWorks = null;
    if (testCase.interaction === "capability-readonly") {
      if (testCase.readOnlyDomain === "Agents") {
        await page.getByText("Financeiro 01", { exact: true }).waitFor();
        capabilityReadOnlyWorks = await page.getByText("Somente leitura", { exact: true }).count() === 1
          && await page.getByRole("switch").count() === 0
          && await page.locator(".agent-availability-readonly").count() === 3
          && await page.getByRole("button", { name: /Cadastrar dispositivo|Alterar ambiente|Alterar display|Baixar|Excluir/ }).count() === 0;
      }
      if (testCase.readOnlyDomain === "Robots") {
        await page.getByText("Conciliação financeira", { exact: true }).waitFor();
        capabilityReadOnlyWorks = await page.getByText("Somente leitura", { exact: true }).count() === 1
          && await page.getByRole("button", { name: /Nova pasta|Enviar pacote|Nova versão|Executar|Adicionar robô|Criar subpasta|Excluir/ }).count() === 0
          && await page.getByRole("button", { name: "Versões", exact: true }).isVisible()
          && await page.getByRole("heading", { name: "Catálogo de bibliotecas" }).count() === 0;
      }
      if (testCase.readOnlyDomain === "Executions") {
        await page.getByRole("button", { name: "Ver detalhes da execução 142" }).click();
        const dialog = page.getByRole("dialog", { name: "Execução #142" });
        await dialog.waitFor();
        capabilityReadOnlyWorks = await page.getByText("Somente leitura", { exact: true }).count() === 1
          && await page.getByRole("button", { name: /Parar|Cancelar da fila/ }).count() === 0
          && await dialog.getByRole("combobox", { name: "Prioridade operacional" }).count() === 0
          && await dialog.locator(".execution-queue-priority-readonly").getByText("Urgente").isVisible();
      }
      if (testCase.readOnlyDomain === "Schedules") {
        await page.getByText("Conciliação financeira", { exact: true }).waitFor();
        capabilityReadOnlyWorks = await page.getByText("Somente leitura", { exact: true }).count() === 2
          && await page.getByRole("button", { name: /Novo agendamento|Editar|Ativar|Desativar|Excluir/ }).count() === 0
          && await page.getByText("Consulta", { exact: true }).isVisible();
      }
      if (testCase.readOnlyDomain === "Libraries") {
        const module = page.locator(".libraries-module");
        await module.getByText("Conectores ERP", { exact: true }).waitFor();
        await module.getByRole("button", { name: "Ações de Conectores ERP" }).click();
        const libraryReadOnlyChecks = {
          badges: await module.getByText("Somente leitura", { exact: true }).count(),
          forbiddenActions: await module.getByRole("button", { name: /Nova pasta|Nova biblioteca|Criar pasta|Criar subpasta|Editar metadados|Mover para pasta|Desativar/ }).count(),
          detailsVisible: await module.getByRole("menuitem", { name: "Ver detalhes" }).isVisible(),
        };
        capabilityReadOnlyWorks = libraryReadOnlyChecks.badges >= 1
          && libraryReadOnlyChecks.forbiddenActions === 0
          && libraryReadOnlyChecks.detailsVisible;
      }
      if (testCase.readOnlyDomain === "Roles") {
        await page.getByText("Operação assistida", { exact: true }).waitFor();
        await page.getByRole("button", { name: "Consultar" }).click();
        await page.getByRole("heading", { name: "Operação assistida" }).last().waitFor();
        const search = page.getByRole("searchbox", { name: "Pesquisar perfis de acesso" });
        await search.fill("perfil inexistente");
        await page.getByRole("heading", { name: "Nenhum perfil corresponde à pesquisa" }).waitFor();
        await page.locator(".ui-empty-state").getByRole("button", { name: "Limpar pesquisa" }).click();
        const roleFilterWorks = await page.getByRole("button", { name: "Consultar" }).isVisible();
        capabilityReadOnlyWorks = roleFilterWorks
          && await page.getByText("Somente leitura", { exact: true }).count() >= 1
          && await page.getByRole("button", { name: /Novo perfil|Excluir|Salvar permissões/ }).count() === 0
          && await page.getByRole("switch").count() === 2
          && await page.getByRole("switch").first().isDisabled();
      }
      if (testCase.readOnlyDomain === "Users") {
        await page.getByText("Ana Operação", { exact: true }).waitFor();
        const search = page.getByRole("searchbox", { name: "Pesquisar usuários" });
        await search.fill("usuário inexistente");
        await page.getByRole("heading", { name: "Nenhum usuário corresponde aos filtros" }).waitFor();
        await page.locator(".ui-empty-state").getByRole("button", { name: "Limpar filtros" }).click();
        const userFilterWorks = await page.getByText("Ana Operação", { exact: true }).isVisible();
        capabilityReadOnlyWorks = userFilterWorks
          && await page.getByText("Somente leitura", { exact: true }).count() >= 1
          && await page.getByRole("button", { name: /Editar perfis|Alterar senha|Excluir|Desativar|Ativar/ }).count() === 0
          && await page.getByText("Consulta", { exact: true }).isVisible();
      }
      await page.waitForTimeout(180);
    }
    const metrics = await page.evaluate(() => {
      const visible = (element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      const horizontalOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth;
      const dialogElements = [...document.querySelectorAll('[role="dialog"], [role="alertdialog"]')];
      const overflowingDialogs = dialogElements
        .filter((element) => visible(element) && element.scrollWidth > element.clientWidth + 1).length;
      const modalStyleProbe = document.createElement("div");
      modalStyleProbe.className = "ui-modal-backdrop";
      modalStyleProbe.hidden = true;
      document.body.append(modalStyleProbe);
      const expectedModalStyle = getComputedStyle(modalStyleProbe);
      const expectedModalBackground = expectedModalStyle.backgroundColor;
      const expectedModalFilter = expectedModalStyle.backdropFilter;
      modalStyleProbe.remove();
      const modalContractViolations = dialogElements
        .filter(visible)
        .flatMap((dialog) => {
          const violations = [];
          const backdrop = dialog.closest(".ui-modal-backdrop");
          if (!dialog.classList.contains("ui-modal-surface")) violations.push("surface-class");
          if (!backdrop) return [...violations, "backdrop-class"];
          const rect = backdrop.getBoundingClientRect();
          const style = getComputedStyle(backdrop);
          if (Math.abs(rect.x) > 1 || Math.abs(rect.y) > 1 || Math.abs(rect.width - innerWidth) > 1 || Math.abs(rect.height - innerHeight) > 1) {
            violations.push("viewport-coverage");
          }
          if (style.backgroundColor !== expectedModalBackground) violations.push("backdrop-color");
          if (style.backdropFilter !== expectedModalFilter) violations.push("backdrop-filter");
          return violations;
        });
      const panelHeaders = [...document.querySelectorAll(".ui-panel-header")].filter(visible);
      const executionSummaryCards = [...document.querySelectorAll(".execution-summary-card")].filter(visible);
      const executionSummaryGridAligned = executionSummaryCards.length === 0 || innerWidth <= 1024
        ? null
        : executionSummaryCards.length === 4
          && new Set(executionSummaryCards.map((card) => Math.round(card.getBoundingClientRect().top))).size === 1
          && Math.max(...executionSummaryCards.map((card) => card.getBoundingClientRect().width))
            - Math.min(...executionSummaryCards.map((card) => card.getBoundingClientRect().width)) <= 2;
      const misalignedFillEmptyStates = [...document.querySelectorAll(".ui-empty-state--fill")]
        .filter(visible)
        .filter((emptyState) => {
          const stateRect = emptyState.getBoundingClientRect();
          const content = [...emptyState.children].filter(visible);
          if (content.length === 0) return true;
          const contentRects = content.map((element) => element.getBoundingClientRect());
          const contentTop = Math.min(...contentRects.map((rect) => rect.top));
          const contentBottom = Math.max(...contentRects.map((rect) => rect.bottom));
          const verticalDelta = Math.abs((contentTop + contentBottom) / 2 - (stateRect.top + stateRect.bottom) / 2);
          const horizontalDelta = Math.max(...contentRects.map((rect) => Math.abs((rect.left + rect.right) / 2 - (stateRect.left + stateRect.right) / 2)));
          return verticalDelta > 2 || horizontalDelta > 2;
        })
        .length;
      const compositeRows = [
        ...[...document.querySelectorAll(".robot-folder-row")].map((row) => ({
          row,
          target: row.querySelector(".robot-folder-select"),
          lead: row.querySelector(".robot-folder-expand"),
          trailing: row.querySelector(":scope > .robot-folder-actions"),
        })),
        ...[...document.querySelectorAll(".library-catalog-row")].map((row) => ({
          row,
          target: row.querySelector(":scope > .library-catalog-main-button"),
          lead: row.querySelector(":scope > .library-catalog-expand"),
          trailing: row.querySelector(":scope > .library-catalog-actions"),
        })),
        ...[...document.querySelectorAll(".vault-folder-row")].map((row) => ({
          row,
          target: row.querySelector(":scope > .vault-folder-select-button"),
          lead: null,
          trailing: row.querySelector(":scope > .vault-folder-action-button"),
        })),
      ];
      const incompleteCompositeTargets = compositeRows.flatMap(({ row, target, lead, trailing }) => {
        if (!visible(row) || !target || !visible(target)) return [];
        const rowRect = row.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        const rowStyle = getComputedStyle(row);
        const contentLeft = rowRect.left + Number.parseFloat(rowStyle.paddingLeft || "0") + Number.parseFloat(rowStyle.borderLeftWidth || "0");
        const contentRight = rowRect.right - Number.parseFloat(rowStyle.paddingRight || "0") - Number.parseFloat(rowStyle.borderRightWidth || "0");
        const expectedLeft = lead && visible(lead) ? lead.getBoundingClientRect().right : contentLeft;
        const expectedRight = trailing && visible(trailing) ? trailing.getBoundingClientRect().left : contentRight;
        const rowGap = Number.parseFloat(rowStyle.columnGap || rowStyle.gap || "0");
        const targetGap = Number.parseFloat(getComputedStyle(target.parentElement ?? row).columnGap || "0");
        const allowedHorizontalGap = Math.max(rowGap, targetGap, 0) + 1;
        const incomplete = targetRect.left - expectedLeft > allowedHorizontalGap
          || expectedRight - targetRect.right > allowedHorizontalGap
          || targetRect.top - rowRect.top > 8
          || rowRect.bottom - targetRect.bottom > 8;
        return incomplete ? [{
          row: row.className,
          target: target.className,
          text: target.textContent?.trim().slice(0, 80) ?? "",
          startGap: Math.round(targetRect.left - expectedLeft),
          endGap: Math.round(expectedRight - targetRect.right),
          topGap: Math.round(targetRect.top - rowRect.top),
          bottomGap: Math.round(rowRect.bottom - targetRect.bottom),
          allowedHorizontalGap,
        }] : [];
      });
      return {
        horizontalOverflow,
        language: document.documentElement.lang,
        theme: document.documentElement.dataset.theme,
        unlabelledFields: [...document.querySelectorAll("input, select, textarea")]
          .filter((element) => visible(element) && !(element.labels?.length || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby"))).length,
        unnamedButtons: [...document.querySelectorAll("button")]
          .filter((element) => visible(element) && !(element.textContent?.trim() || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby"))).length,
        undersizedTargets: [...document.querySelectorAll("button")]
          .filter((element) => {
            if (!visible(element)) return false;
            const rect = element.getBoundingClientRect();
            return rect.width < 24 || rect.height < 24;
          }).map((element) => element.getAttribute("aria-label") || element.textContent?.trim()),
        decorativeHeaderIcons: [...document.querySelectorAll(".page-heading-icon")].filter(visible).length,
        inconsistentPanelHeaders: panelHeaders.filter((header) => {
          const heading = header.querySelector("h2, h3");
          return heading && Math.abs(Number.parseFloat(getComputedStyle(heading).fontSize) - 16) > 0.1;
        }).length,
        legacyPanelHeaders: [...document.querySelectorAll(".content-panel-header, .executions-table-header, .roles-panel-header, .users-panel-header, .logs-panel-header, .vault-panel-header, .device-credentials-panel-header, .dashboard-module-header, .panel-header")]
          .filter((header) => visible(header) && !header.classList.contains("ui-panel-header")).length,
        executionSummaryGridAligned,
        unstyledSearchFields: [...document.querySelectorAll('input[type="search"]')]
          .filter((element) => visible(element) && !element.classList.contains("ui-input")).length,
        legacyEmptyStates: [...document.querySelectorAll(".empty-state, .panel-empty-state, .execution-empty-state, .users-empty-state, .roles-empty-state, .vault-empty-state, .logs-empty-state")]
          .filter(visible).length,
        misalignedFillEmptyStates,
        incompleteCompositeTargets,
        reducedMotionSafe: !matchMedia("(prefers-reduced-motion: reduce)").matches || document.getAnimations().every((animation) => Number(animation.effect?.getTiming().duration ?? 0) <= 1),
        modalContractViolations,
        overflowingDialogs,
        dialogGeometry: dialogElements
          .filter(visible)
          .map((element) => ({ className: element.className, clientWidth: element.clientWidth, scrollWidth: element.scrollWidth })),
        dialogOverflowSources: dialogElements
          .filter(visible)
          .flatMap((dialog) => [...dialog.querySelectorAll("*")]
            .filter((element) => visible(element) && element.scrollWidth > element.clientWidth + 2)
            .map((element) => ({
              tag: element.tagName,
              className: typeof element.className === "string" ? element.className : "",
              clientWidth: element.clientWidth,
              scrollWidth: element.scrollWidth,
            })))
          .slice(0, 8),
        overflowSources: horizontalOverflow || overflowingDialogs ? [...document.querySelectorAll("body *")]
          .filter((element) => {
            if (!visible(element)) return false;
            if (element.classList.contains("sr-only")) return false;
            const rect = element.getBoundingClientRect();
            return rect.right > document.documentElement.clientWidth + 1 || element.scrollWidth > element.clientWidth + 2;
          })
          .slice(0, 8)
          .map((element) => ({
            tag: element.tagName,
            className: typeof element.className === "string" ? element.className : "",
            text: element.textContent?.trim().slice(0, 80) ?? "",
            clientWidth: element.clientWidth,
            scrollWidth: element.scrollWidth,
            rect: Math.round(element.getBoundingClientRect().width),
          })) : [],
      };
    });

    const rootUploadAvailable = testCase.route === "/automations/catalog/robots" && testCase.readOnlyDomain !== "Robots"
      ? await page.locator("button").filter({ hasText: "Enviar pacote" }).first().isEnabled()
      : null;
    const schedulePolicyWorks = testCase.scheduleData
      ? await page.getByText("Ignora atraso > 10 min").isVisible()
        && await page.getByText(/Ignorada em/).isVisible()
      : null;

    let mobileNavigation = null;
    if (testCase.authenticated && !testCase.studio && !testCase.interaction && testCase.width <= 1024) {
      await page.getByRole("button", { name: "Abrir navegação" }).click();
      await page.waitForTimeout(260);
      mobileNavigation = await page.locator("#primary-navigation").evaluate((element) => element.classList.contains("sidebar--open") && Math.abs(element.getBoundingClientRect().left) < 1);
      await page.keyboard.press("Escape");
      await page.waitForTimeout(260);
    }

    await page.screenshot({ path: path.join(outputDir, `${testCase.name}.png`), fullPage: true });
    results.push({ ...testCase, ...metrics, rendered: true, rootUploadAvailable, schedulePolicyWorks, mobileNavigation, scheduleRecoveryWorks, robotFolderCreateWorks, robotFolderHitAreaWorks, robotFolderHitAreaDetails, robotFolderHierarchyWorks, robotVersionsWorks, kanbanSpacingWorks, activityTimelineWorks, vaultAutomationWorks, vaultReadOnlyWorks, libraryFolderHierarchyWorks, capabilityReadOnlyWorks, filterNavigationWorks, executionDetailsWorks, executionQueueDetailsWorks, logsExplorerWorks, agentMaintenanceWorks, agentMaintenanceEditorWorks, agentHealthAttentionWorks, agentCreateErrorPersists, historyFilterWorks, consoleErrors, pageErrors, unavailableApiRequests });
    await context.close();
  }
} finally {
  await browser.close();
}

const failures = results.filter((result) => result.rendered === false || result.horizontalOverflow || result.overflowingDialogs || result.modalContractViolations?.length || result.unlabelledFields || result.unnamedButtons || result.undersizedTargets?.length || result.decorativeHeaderIcons || result.inconsistentPanelHeaders || result.legacyPanelHeaders || result.executionSummaryGridAligned === false || result.unstyledSearchFields || result.legacyEmptyStates || result.misalignedFillEmptyStates || result.incompleteCompositeTargets?.length || !result.reducedMotionSafe || result.language !== "pt-BR" || result.consoleErrors.length || result.pageErrors.length || result.mobileNavigation === false || result.rootUploadAvailable === false || result.schedulePolicyWorks === false || result.scheduleRecoveryWorks === false || result.robotFolderCreateWorks === false || result.robotFolderHitAreaWorks === false || result.robotFolderHierarchyWorks === false || result.robotVersionsWorks === false || result.kanbanSpacingWorks === false || result.activityTimelineWorks === false || result.vaultAutomationWorks === false || result.vaultReadOnlyWorks === false || result.libraryFolderHierarchyWorks === false || result.capabilityReadOnlyWorks === false || result.filterNavigationWorks === false || result.executionDetailsWorks === false || result.executionQueueDetailsWorks === false || result.logsExplorerWorks === false || result.agentMaintenanceWorks === false || result.agentMaintenanceEditorWorks === false || result.agentHealthAttentionWorks === false || result.agentCreateErrorPersists === false || result.historyFilterWorks === false);
const report = { results, failures: failures.length };
await writeFile(path.join(outputDir, "audit.json"), JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exitCode = 1;
