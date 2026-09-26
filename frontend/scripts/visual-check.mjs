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
  { name: "robots-390-light", route: "/robots", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "robots-1440-dark", route: "/robots", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "robots-folder-create-768-light", route: "/robots", width: 768, height: 900, colorScheme: "light", authenticated: true, interaction: "robot-folder-create" },
  { name: "development-390-dark", route: "/development", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "development-1440-light", route: "/development", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "executions-1440-light", route: "/executions", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "executions-empty-1440-light", route: "/executions", width: 1440, height: 900, colorScheme: "light", authenticated: true, forceEmpty: true },
  { name: "history-1440-dark", route: "/history", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "history-1440-light", route: "/history", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-390-light", route: "/schedules", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "schedules-1440-light", route: "/schedules", width: 1440, height: 900, colorScheme: "light", authenticated: true },
  { name: "schedules-modal-390-dark", route: "/schedules", width: 390, height: 844, colorScheme: "dark", authenticated: true, interaction: "schedule-modal" },
  { name: "schedules-modal-768-light", route: "/schedules", width: 768, height: 720, colorScheme: "light", authenticated: true, interaction: "schedule-modal" },
  { name: "vault-390-dark", route: "/vault", width: 390, height: 844, colorScheme: "dark", authenticated: true },
  { name: "vault-1440-light", route: "/vault", width: 1440, height: 1000, colorScheme: "light", authenticated: true },
  { name: "roles-1440-dark", route: "/roles", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
  { name: "users-390-light", route: "/users", width: 390, height: 844, colorScheme: "light", authenticated: true },
  { name: "logs-1440-dark", route: "/logs", width: 1440, height: 1000, colorScheme: "dark", authenticated: true },
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
        const permissions = [
          "Dashboard:view", "Agents:view", "Development:view", "Development:create", "Development:edit",
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
        const body = pathname === "/auth/me"
          ? testCase.authenticated
            ? { status: "success", user: { id: 1, username: "operador", name: "Operador DUET", is_active: 1, permissions } }
            : { status: "unauthenticated" }
          : pathname === "/dashboard/stats"
            ? { total_agents: 12, agents_online: 9, total_robots: 48 }
            : pathname === "/schedules"
              ? { status: "success", schedules: [] }
            : pathname === "/schedules/options"
              ? { status: "success", robots: [{ id: 12, name: "Conciliação financeira" }], agents: [{ agent_id: "runner-01", name: "Dispositivo Financeiro", status: "online" }] }
            : pathname === "/roles" || pathname === "/roles/permissions" || pathname === "/auth/users"
              ? []
            : pathname === "/executions"
              ? { executions: testCase.forceEmpty ? [] : [{ id: 142, robot_id: 9, robot_name: "Conciliação financeira", filename: "conciliacao.zip", agent_id: "runner-03", agent_name: "Financeiro 03", status: "running", started_at: "2026-09-26T14:45:00Z", finished_at: null, error_message: null }] }
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
    if (testCase.interaction === "schedule-modal") {
      await page.getByRole("button", { name: "Novo agendamento" }).click();
      await page.getByRole("dialog", { name: "Novo agendamento" }).waitFor();
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

    let mobileNavigation = null;
    if (testCase.authenticated && !testCase.studio && !testCase.interaction && testCase.width <= 1024) {
      await page.getByRole("button", { name: "Abrir navegação" }).click();
      await page.waitForTimeout(260);
      mobileNavigation = await page.locator("#primary-navigation").evaluate((element) => element.classList.contains("sidebar--open") && Math.abs(element.getBoundingClientRect().left) < 1);
      await page.keyboard.press("Escape");
      await page.waitForTimeout(260);
    }

    await page.screenshot({ path: path.join(outputDir, `${testCase.name}.png`), fullPage: true });
    results.push({ ...testCase, ...metrics, rendered: true, rootUploadAvailable, mobileNavigation, consoleErrors, pageErrors, unavailableApiRequests });
    await context.close();
  }
} finally {
  await browser.close();
}

const failures = results.filter((result) => result.rendered === false || result.horizontalOverflow || result.overflowingDialogs || result.unlabelledFields || result.unnamedButtons || result.undersizedTargets?.length || result.decorativeHeaderIcons || result.unstyledSearchFields || result.legacyEmptyStates || !result.reducedMotionSafe || result.language !== "pt-BR" || result.consoleErrors.length || result.pageErrors.length || result.mobileNavigation === false || result.rootUploadAvailable === false);
console.log(JSON.stringify({ results, failures: failures.length }, null, 2));
if (failures.length) process.exitCode = 1;
