import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const password = process.env.DUET_TEST_ADMIN_PASSWORD;
if (!password) throw new Error("Defina DUET_TEST_ADMIN_PASSWORD para a conta sintética local.");

const baseUrl = process.env.DUET_FRONTEND_URL ?? "http://localhost:5173";
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outputDir = path.resolve("..", ".e2e", "frontend-live");
const routes = ["/", "/agents", "/development", "/robots", "/executions", "/history", "/schedules", "/logs", "/vault", "/roles", "/users"];
const viewports = [
  { name: "desktop-light", width: 1440, height: 1000, colorScheme: "light" },
  { name: "desktop-dark", width: 1440, height: 1000, colorScheme: "dark" },
  { name: "tablet-light", width: 768, height: 1024, colorScheme: "light" },
  { name: "tablet-dark", width: 768, height: 1024, colorScheme: "dark" },
  { name: "mobile-light", width: 390, height: 844, colorScheme: "light" },
  { name: "mobile-dark", width: 390, height: 844, colorScheme: "dark" },
];

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const results = [];

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, colorScheme: viewport.colorScheme, locale: "pt-BR" });
    const page = await context.newPage();
    let consoleErrors = [];
    let requestFailures = [];
    page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
    page.on("requestfailed", (request) => requestFailures.push({ url: request.url(), error: request.failure()?.errorText }));

    await page.goto(`${baseUrl}/login`, { waitUntil: "networkidle" });
    await page.locator("#username").fill("admin");
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: "Entrar no Control Room" }).click();
    await page.waitForURL(`${baseUrl}/`, { timeout: 15_000 });

    for (const routePath of routes) {
      consoleErrors = [];
      requestFailures = [];
      await page.goto(`${baseUrl}${routePath}`, { waitUntil: "domcontentloaded" });
      await page.locator(".app-header .header-actions").waitFor({ state: "visible", timeout: 15_000 });
      await page.locator(".page-loading").waitFor({ state: "detached", timeout: 15_000 }).catch(() => {});
      await page.waitForTimeout(routePath === "/logs" ? 700 : 350);
      const metrics = await page.evaluate(() => ({
        horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        title: document.querySelector(".page-heading h1, .page-header h1, main h1")?.textContent?.trim() ?? document.title,
        visibleErrorText: [...document.querySelectorAll('[role="alert"], .alert-error, .logs-alert, .execution-error-alert, .roles-alert-error, .users-alert-error')]
          .filter((element) => { const style = getComputedStyle(element); return style.display !== "none" && style.visibility !== "hidden"; })
          .map((element) => element.textContent?.trim()).filter(Boolean),
        theme: document.documentElement.dataset.theme,
        unlabelledFields: [...document.querySelectorAll("input, select, textarea")]
          .filter((element) => {
            const style = getComputedStyle(element);
            const visible = style.display !== "none" && style.visibility !== "hidden" && element.getAttribute("aria-hidden") !== "true" && element.getBoundingClientRect().width > 0;
            const named = element.labels?.length || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby") || element.getAttribute("title");
            return visible && !named;
          })
          .map((element) => element.id || element.getAttribute("name") || element.tagName.toLowerCase()),
        unnamedButtons: [...document.querySelectorAll("button")]
          .filter((element) => {
            const style = getComputedStyle(element);
            const visible = style.display !== "none" && style.visibility !== "hidden" && element.getBoundingClientRect().width > 0;
            const named = element.textContent?.trim() || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby") || element.getAttribute("title");
            return visible && !named;
          }).length,
      }));
      const slug = routePath === "/" ? "dashboard" : routePath.slice(1).replaceAll("/", "-");
      await page.screenshot({ path: path.join(outputDir, `${viewport.name}-${slug}.png`), fullPage: true });
      results.push({ viewport: viewport.name, route: routePath, ...metrics, consoleErrors: [...consoleErrors], requestFailures: [...requestFailures] });
    }

    await context.close();
  }
} finally {
  await browser.close();
}

const failures = results.filter((result) => result.horizontalOverflow || result.consoleErrors.length || result.requestFailures.length || result.visibleErrorText.length || result.unlabelledFields.length || result.unnamedButtons);
const report = { generatedAt: new Date().toISOString(), results, failures: failures.length };
await writeFile(path.join(outputDir, "audit.json"), JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exitCode = 1;
