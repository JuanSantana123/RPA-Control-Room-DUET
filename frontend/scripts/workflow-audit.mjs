import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const password = process.env.DUET_TEST_ADMIN_PASSWORD;
if (!password) throw new Error("Defina DUET_TEST_ADMIN_PASSWORD para a conta sintética local.");

const baseUrl = process.env.DUET_FRONTEND_URL ?? "http://localhost:5173";
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outputDir = path.resolve("..", ".e2e", "frontend-workflows");
const projectName = "Projeto de validação visual";

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, colorScheme: "dark", locale: "pt-BR" });
const page = await context.newPage();
const consoleErrors = [];
const requestFailures = [];

page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("requestfailed", (request) => requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));

const checkpoints = [];
async function checkpoint(name) {
  await page.waitForTimeout(350);
  const metrics = await page.evaluate(() => ({
    url: location.pathname,
    horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    dialogs: document.querySelectorAll('[role="dialog"], .schedule-modal, .library-modal, .library-picker-modal').length,
    dialogState: (() => {
      const dialog = document.querySelector('[role="dialog"], .schedule-modal, .library-modal, .library-picker-modal');
      if (!dialog) return null;
      const rect = dialog.getBoundingClientRect();
      return { top: Math.round(rect.top), bottom: Math.round(rect.bottom), scrollTop: Math.round(dialog.scrollTop), viewportHeight: innerHeight };
    })(),
    theme: document.documentElement.dataset.theme,
    skeletons: document.querySelectorAll(".skeleton").length,
    unlabelledFields: [...document.querySelectorAll("input, select, textarea")]
      .filter((element) => {
        const style = getComputedStyle(element);
        const visible = style.display !== "none" && style.visibility !== "hidden" && element.getAttribute("aria-hidden") !== "true" && element.getBoundingClientRect().width > 0;
        const named = element.labels?.length || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby") || element.getAttribute("title");
        return visible && !named;
      })
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        id: element.id || null,
        className: element.className || null,
        role: element.getAttribute("role"),
      })),
    unnamedButtons: [...document.querySelectorAll("button")]
      .filter((element) => {
        const style = getComputedStyle(element);
        const visible = style.display !== "none" && style.visibility !== "hidden" && element.getBoundingClientRect().width > 0;
        const named = element.textContent?.trim() || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby") || element.getAttribute("title");
        return visible && !named;
      }).length,
    nonstandardSelects: [...document.querySelectorAll("select:not([multiple])")]
      .filter((element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        const visible = style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        return visible && style.appearance !== "none";
      }).length,
    nonstandardCheckboxes: [...document.querySelectorAll('input[type="checkbox"]')]
      .filter((element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        const visible = style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
        return visible && (style.appearance !== "none" || rect.width < 36 || rect.height < 20);
      }).length,
    nativeSelectsOutsideDesignSystem: [...document.querySelectorAll("select")]
      .filter((element) => !element.closest(".premium-select")).length,
  }));
  await page.screenshot({ path: path.join(outputDir, `${name}.png`), fullPage: true });
  checkpoints.push({ name, ...metrics });
}

try {
  await page.goto(`${baseUrl}/login`, { waitUntil: "networkidle" });
  await page.locator("#username").fill("admin");
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Entrar no Control Room" }).click();
  await page.waitForURL(`${baseUrl}/`, { timeout: 15_000 });
  consoleErrors.length = 0;
  requestFailures.length = 0;

  await page.goto(`${baseUrl}/agents`, { waitUntil: "networkidle" });
  await page.route("**/dashboard/stats", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1_200));
    await route.continue();
  });
  await page.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded" });
  await page.locator(".dashboard-skeleton").waitFor({ timeout: 5_000 });
  await checkpoint("dashboard-loading-skeleton");
  if ((await page.locator(".dashboard-skeleton .skeleton").count()) < 8) {
    throw new Error("O dashboard não exibiu o skeleton contextual esperado.");
  }
  await page.locator(".dashboard-skeleton").waitFor({ state: "detached", timeout: 10_000 });
  await page.unroute("**/dashboard/stats");

  if ((await page.locator('.theme-switcher__option').count()) !== 3) throw new Error("O seletor de tema não exibiu os três ícones esperados.");
  await page.getByRole("button", { name: "Usar tema escuro" }).click();
  await checkpoint("theme-controls");

  await page.goto(`${baseUrl}/agents`, { waitUntil: "networkidle" });
  const environmentSelect = page.locator("#agent-environment").locator("..").getByRole("combobox");
  await environmentSelect.click();
  await page.getByRole("listbox").waitFor();
  await checkpoint("agent-environment-select-open");
  await page.keyboard.press("Escape");

  await page.goto(`${baseUrl}/robots`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Abrir Raiz de Robôs/i }).click();
  await page.getByRole("searchbox", { name: "Pesquisar robôs nesta localização" }).waitFor();
  await checkpoint("robots-workspace");

  await page.goto(`${baseUrl}/development`, { waitUntil: "networkidle" });
  await page.getByRole("combobox", { name: "Filtrar por situação" }).waitFor();
  await checkpoint("development-overview-filters");

  await page.goto(`${baseUrl}/schedules`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Novo Agendamento/i }).click();
  await page.getByText("Novo Agendamento", { exact: true }).last().waitFor();
  await checkpoint("schedule-modal-open");
  await page.getByRole("button", { name: "Cancelar" }).click();

  await page.goto(`${baseUrl}/roles`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Novo perfil/i }).click();
  await page.getByRole("button", { name: "Cancelar" }).waitFor();
  await checkpoint("role-form-open");
  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("button", { name: "Configurar" }).click();
  await page.getByRole("button", { name: "Salvar permissões" }).waitFor();
  await checkpoint("role-permissions-open");

  await page.goto(`${baseUrl}/vault`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Nova pasta/i }).first().click();
  await page.getByRole("button", { name: "Cancelar" }).waitFor();
  await checkpoint("vault-folder-form-open");
  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("tab", { name: /Credenciais de Dispositivo/i }).click();
  await page.locator(".device-credentials-panel").waitFor();
  await checkpoint("vault-device-credentials");
  await page.getByRole("tab", { name: /Credenciais de Automação/i }).click();

  await page.goto(`${baseUrl}/users`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Editar perfis" }).click();
  await checkpoint("user-roles-form-open");
  await page.getByRole("button", { name: "Cancelar" }).click();
  await page.getByRole("button", { name: "Alterar senha" }).click();
  await checkpoint("user-password-form-open");
  await page.getByRole("button", { name: "Cancelar" }).click();

  await page.goto(`${baseUrl}/development`, { waitUntil: "networkidle" });
  if (!(await page.getByText(projectName, { exact: true }).count())) {
    await page.getByRole("button", { name: /Novo projeto/i }).click();
    await page.locator("#development-project-name").fill(projectName);
    await page.locator("#development-project-description").fill("Projeto sintético local para validar a interface do Studio sem executar robôs.");
    await checkpoint("development-create-form");
    await page.getByRole("button", { name: "Criar projeto" }).click();
    await page.getByText(projectName, { exact: true }).waitFor({ timeout: 15_000 });
  }

  const projectCard = page.locator("article.robot-card").filter({ hasText: projectName });
  await projectCard.waitFor();
  await checkpoint("development-project-created");
  await page.getByRole("button", { name: "Kanban" }).click();
  await page.getByText("Backlog", { exact: true }).first().waitFor();
  await checkpoint("development-kanban");
  const kanbanCard = page.locator("article").filter({ hasText: projectName }).first();
  await kanbanCard.getByRole("button", { name: "Detalhes" }).click();
  await page.getByRole("dialog", { name: projectName }).waitFor();
  await checkpoint("development-card-details");
  await page.getByRole("button", { name: "Fechar" }).click();
  await page.getByRole("button", { name: "Projetos" }).click();
  await projectCard.getByRole("button", { name: "Abrir no Studio" }).click();
  await page.waitForURL(/\/development\/\d+\/studio/, { timeout: 15_000 });
  await page.waitForLoadState("networkidle");
  await page.locator(".monaco-editor").waitFor({ timeout: 20_000 });
  await checkpoint("studio-desktop-dark");

  if (await page.getByRole("button", { name: "Checkout" }).count()) {
    await page.getByRole("button", { name: "Checkout" }).click();
  }
  await page.getByRole("button", { name: "Checkin" }).waitFor({ timeout: 15_000 });

  if (!(await page.getByText("validacao-visual.txt", { exact: true }).count())) {
    page.once("dialog", (dialog) => dialog.accept("validacao-visual.txt"));
    await page.getByRole("button", { name: "Novo arquivo" }).click();
    await page.getByText("validacao-visual.txt", { exact: true }).first().waitFor();
    await page.locator(".monaco-editor").click();
    await page.keyboard.type("Validacao sintetica do Studio DUET.");
    await page.getByRole("button", { name: "Salvar" }).click();
  }
  await checkpoint("studio-file-saved");

  await page.getByRole("button", { name: "Gerenciar bibliotecas" }).click();
  await page.getByText("Bibliotecas", { exact: true }).last().waitFor();
  await checkpoint("studio-library-actions");
  await page.getByRole("button", { name: "Fechar", exact: true }).click();

  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Excluir validacao-visual.txt" }).click();
  await page.getByText("validacao-visual.txt", { exact: true }).first().waitFor({ state: "detached" });
  await page.getByRole("button", { name: "Checkin" }).click();
  await page.getByRole("button", { name: "Checkout" }).waitFor({ timeout: 15_000 });
  await checkpoint("studio-checkin-complete");

  await page.setViewportSize({ width: 390, height: 844 });
  await checkpoint("studio-mobile-dark");

  await page.goto(`${baseUrl}/`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Abrir navegação" }).click();
  await page.locator("#primary-navigation.sidebar--open").waitFor();
  await checkpoint("mobile-navigation-open");
  await page.getByRole("button", { name: "Fechar navegação" }).first().click();
} finally {
  await browser.close();
}

const failures = [
  ...checkpoints.filter((item) => item.horizontalOverflow || item.unlabelledFields.length || item.unnamedButtons || item.nonstandardSelects || item.nonstandardCheckboxes || item.nativeSelectsOutsideDesignSystem),
  ...consoleErrors.map((message) => ({ type: "console", message })),
  ...requestFailures.map((failure) => ({ type: "request", ...failure })),
];
const report = { generatedAt: new Date().toISOString(), projectName, checkpoints, consoleErrors, requestFailures, failures: failures.length };
await writeFile(path.join(outputDir, "audit.json"), JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exitCode = 1;
