import { mkdir } from "node:fs/promises";
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
  { name: "robots-390-light", route: "/robots", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "robots-1440-dark", route: "/robots", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "robots-folder-create-768-light", route: "/robots", width: 768, height: 900, colorScheme: "light", authenticated: true, interaction: "robot-folder-create" },
  { name: "development-390-dark", route: "/development", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "development-1440-light", route: "/development", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "executions-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "executions-filter-navigation-768-dark", route: "/executions", width: 768, height: 900, colorScheme: "dark", authenticated: true, interaction: "execution-filters" },
  { name: "executions-details-390-dark", route: "/executions", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "execution-details" },
  { name: "executions-details-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true, interaction: "execution-details" },
  { name: "executions-queue-details-1440-dark", route: "/executions", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, queueData: true, interaction: "execution-queue-details" },
  { name: "executions-queue-details-390-light", route: "/executions", width: 390, height: 844, colorScheme: "light", authenticated: true, queueData: true, interaction: "execution-queue-details" },
  { name: "executions-empty-1440-light", route: "/executions", width: 1440, height: 900, colorScheme: "light", authenticated: true, forceEmpty: true },
  { name: "history-1440-dark", route: "/history", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "history-1440-light", route: "/history", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-390-light", route: "/schedules", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "schedules-1440-light", route: "/schedules", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-policy-1440-dark", route: "/schedules", width: 1440, height: 900, colorScheme: "dark", authenticated: true, scheduleData: true },
  { name: "schedules-modal-390-dark", route: "/schedules", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "schedule-modal" },
  { name: "schedules-modal-768-light", route: "/schedules", width: 768, height: 720, colorScheme: "light", authenticated: true, interaction: "schedule-modal" },
  { name: "vault-390-dark", route: "/vault", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "vault-1440-light", route: "/vault", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "roles-1440-dark", route: "/roles", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "users-390-light", route: "/users", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "logs-390-light", route: "/logs", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "logs-explorer-1440-dark", route: "/logs", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, interaction: "logs-filter" },
  { name: "studio-390-dark", route: "/development/1/studio", width: 390, height: 844, colorScheme: "dark", authenticated: true, studio: true },
  { name: "studio-1440-light", route: "/development/1/studio", width: 1440, height: 1000, colorScheme: "light", authenticated: true, studio: true },
  { name: "development-create-390-dark", route: "/development", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "development-create" },
  { name: "development-create-1440-dark", route: "/development", width: 1440, height: 1000, colorScheme: "dark", authenticated: true, interaction: "development-create" },
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
          "Dashboard:view", "Agents:view", "Agents:edit", "Development:view", "Development:create", "Development:edit",
          "Development:move_stage", "Development:delete", "Development:publish", "Development:trash_view",
          "Development:restore", "Development:permanent_delete", "Development:checkout",
          "Development:force_checkout_release", "Robots:view", "Executions:view", "Executions:execute",
          "History:view", "Schedules:view", "Vault:view", "DeviceCredentials:view", "Roles:view",
          "Users:view", "Users:create", "Users:edit", "Users:delete", "Logs:view", "Libraries:view",
          "Libraries:create", "Libraries:use",
        ];
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
          : pathname === "/agents"
            ? { status: "success", total: testCase.agentData ? 3 : 0, agents: testCase.agentData ? [
                { agent_id: "runner-fin-01", name: "Financeiro 01", environment: "production", host: "FIN-RPA-01", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: true, maintenance_reason: null, availability_updated_at: "2026-09-26T10:00:00", last_heartbeat: "2026-09-26T14:58:30", heartbeat_age_seconds: 8, health_state: "healthy", session_status: "ready", username: "duet.rpa", execution_username: "duet.rpa", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
                { agent_id: "runner-fiscal-02", name: "Fiscal 02", environment: "development", host: "FISCAL-RPA-02", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: false, maintenance_reason: "Atualização programada do Windows", availability_updated_at: "2026-09-26T13:40:00", last_heartbeat: "2026-09-26T14:57:10", heartbeat_age_seconds: 20, health_state: "healthy", session_status: "ready", username: "duet.fiscal", execution_username: "duet.fiscal", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
                { agent_id: "runner-rh-03", name: "Recursos Humanos 03", environment: "production", host: "RH-RPA-03", port: 8000, rpa_directory: "C:\\DUET\\Robots", status: "online", accepting_work: true, maintenance_reason: null, availability_updated_at: null, last_heartbeat: "2026-09-26T14:55:00", heartbeat_age_seconds: 210, health_state: "stale", session_status: "ready", username: "duet.rh", execution_username: "duet.rh", execution_domain: "CORP", display_width: 1920, display_height: 1080, display_scale: 100, display_current: { width: 1920, height: 1080 }, display_supported: [{ width: 1920, height: 1080 }] },
              ] : [] }
          : pathname === "/schedules"
              ? { status: "success", total: testCase.scheduleData ? 1 : 0, schedules: testCase.scheduleData ? [{ id: 18, robot_id: 12, robot_name: "Conciliação financeira", agent_id: null, agent_name: "Automático", tipo: "daily", data_inicio: "2026-09-20T08:00:00", horario: "08:00", dias_semana: null, ativo: true, proxima_execucao: "2026-09-27T08:00:00", ultima_execucao: "2026-09-25T08:00:05", intervalo_ativo: false, intervalo_valor: null, intervalo_unidade: null, horario_fim: null, misfire_policy: "skip", misfire_grace_seconds: 600, ultima_ocorrencia_perdida: "2026-09-26T08:00:00" }] : [] }
            : pathname === "/schedules/options"
              ? { status: "success", timezone: "America/Sao_Paulo", robots: [{ id: 12, name: "Conciliação financeira" }], agents: [{ agent_id: "runner-01", name: "Dispositivo Financeiro", status: "online" }] }
            : pathname === "/roles" || pathname === "/roles/permissions" || pathname === "/auth/users"
              ? []
            : pathname === "/executions"
              ? { status: "success", total: testCase.forceEmpty ? 0 : 1, queue_warning_seconds: 900, executions: testCase.forceEmpty ? [] : [{ id: 142, source_type: "robot", robot_id: 9, robot_version: 3, project_id: null, robot_name: "Conciliação financeira", filename: "conciliacao.zip", folder_name: "Financeiro / Fechamento", user_id: 1, username: "operador", user_name: "Operador DUET", agent_id: "runner-03", agent_name: "Financeiro 03", schedule_id: null, schedule_run_id: null, pid: testCase.queueData ? null : 4872, status: testCase.queueData ? "queued" : "running", priority: testCase.queueData ? "urgent" : "normal", queued_at: testCase.queueData ? "2026-09-26T10:00:00Z" : null, queue_position: testCase.queueData ? 1 : null, started_at: testCase.queueData ? null : "2026-09-26T14:45:00Z", finished_at: null, error_message: null }] }
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
      await page.getByRole("button", { name: "Novo projeto" }).click();
      await page.getByRole("heading", { name: "Crie um projeto de automação" }).waitFor();
      await page.waitForTimeout(180);
    }
    if (testCase.interaction === "robot-folder-create") {
      await page.locator(".robots-folders-panel").getByRole("button", { name: "Nova pasta" }).click();
      await page.getByRole("heading", { name: "Nova pasta" }).waitFor();
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
    const metrics = await page.evaluate(() => {
      const visible = (element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      const horizontalOverflow = document.documentElement.scrollWidth > document.documentElement.clientWidth;
      const overflowingDialogs = [...document.querySelectorAll('[role="dialog"]')]
        .filter((element) => visible(element) && element.scrollWidth > element.clientWidth + 1).length;
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
        unstyledSearchFields: [...document.querySelectorAll('input[type="search"]')]
          .filter((element) => visible(element) && !element.classList.contains("ui-input")).length,
        legacyEmptyStates: [...document.querySelectorAll(".empty-state, .panel-empty-state, .execution-empty-state, .users-empty-state, .roles-empty-state, .vault-empty-state, .logs-empty-state")]
          .filter(visible).length,
        reducedMotionSafe: !matchMedia("(prefers-reduced-motion: reduce)").matches || document.getAnimations().every((animation) => Number(animation.effect?.getTiming().duration ?? 0) <= 1),
        overflowingDialogs,
        dialogGeometry: [...document.querySelectorAll('[role="dialog"]')]
          .filter(visible)
          .map((element) => ({ className: element.className, clientWidth: element.clientWidth, scrollWidth: element.scrollWidth })),
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

    const rootUploadAvailable = testCase.route === "/robots"
      ? await page.getByRole("button", { name: "Enviar pacote" }).first().isEnabled()
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
    results.push({ ...testCase, ...metrics, rendered: true, rootUploadAvailable, schedulePolicyWorks, mobileNavigation, scheduleRecoveryWorks, filterNavigationWorks, executionDetailsWorks, executionQueueDetailsWorks, logsExplorerWorks, agentMaintenanceWorks, agentMaintenanceEditorWorks, agentHealthAttentionWorks, consoleErrors, pageErrors, unavailableApiRequests });
    await context.close();
  }
} finally {
  await browser.close();
}

const failures = results.filter((result) => result.rendered === false || result.horizontalOverflow || result.overflowingDialogs || result.unlabelledFields || result.unnamedButtons || result.undersizedTargets?.length || result.decorativeHeaderIcons || result.unstyledSearchFields || result.legacyEmptyStates || !result.reducedMotionSafe || result.language !== "pt-BR" || result.consoleErrors.length || result.pageErrors.length || result.mobileNavigation === false || result.rootUploadAvailable === false || result.schedulePolicyWorks === false || result.scheduleRecoveryWorks === false || result.filterNavigationWorks === false || result.executionDetailsWorks === false || result.executionQueueDetailsWorks === false || result.logsExplorerWorks === false || result.agentMaintenanceWorks === false || result.agentMaintenanceEditorWorks === false || result.agentHealthAttentionWorks === false);
console.log(JSON.stringify({ results, failures: failures.length }, null, 2));
if (failures.length) process.exitCode = 1;
