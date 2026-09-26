import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const password = process.env.DUET_TEST_ADMIN_PASSWORD;
if (!password) throw new Error("Defina DUET_TEST_ADMIN_PASSWORD para a conta sintética local.");

const baseUrl = process.env.DUET_FRONTEND_URL ?? "http://localhost:5173";
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outputDir = path.resolve("..", ".e2e", "performance");
const profiles = [
  { name: "desktop", width: 1440, height: 1000 },
  { name: "mobile", width: 390, height: 844 },
];

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const results = [];

try {
  for (const profile of profiles) {
    const context = await browser.newContext({ viewport: profile, locale: "pt-BR" });
    await context.addInitScript(() => {
      window.__duetLabMetrics = { cls: 0, lcp: 0, eventDuration: 0 };
      try {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) window.__duetLabMetrics.cls += entry.value;
          }
        }).observe({ type: "layout-shift", buffered: true });
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const last = entries.at(-1);
          if (last) window.__duetLabMetrics.lcp = last.startTime;
        }).observe({ type: "largest-contentful-paint", buffered: true });
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            window.__duetLabMetrics.eventDuration = Math.max(window.__duetLabMetrics.eventDuration, entry.duration);
          }
        }).observe({ type: "event", buffered: true, durationThreshold: 16 });
      } catch {
        // Browsers sem suporte continuam com valores nulos no relatório.
      }
    });

    const page = await context.newPage();
    await page.goto(`${baseUrl}/login`, { waitUntil: "networkidle" });
    await page.locator("#username").fill("admin");
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: "Entrar no Control Room" }).click();
    await page.waitForURL(`${baseUrl}/`, { timeout: 15_000 });
    await page.reload({ waitUntil: "networkidle" });
    await page.locator(".app-header .header-actions").waitFor({ state: "visible" });
    const syntheticInteractionDurationMs = await page.evaluate(async () => {
      const themeButton = document.querySelector('[aria-label="Usar tema escuro"]');
      const startedAt = performance.now();
      themeButton.click();
      await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      return performance.now() - startedAt;
    });
    await page.waitForTimeout(1_000);

    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType("navigation")[0];
      const observed = window.__duetLabMetrics ?? {};
      return {
        lcpMs: observed.lcp || null,
        cls: observed.cls ?? null,
        browserEventDurationMs: observed.eventDuration || null,
        domContentLoadedMs: navigation?.domContentLoadedEventEnd ?? null,
        loadMs: navigation?.loadEventEnd ?? null,
        transferredBytes: navigation?.transferSize ?? null,
      };
    });
    results.push({
      profile: profile.name,
      viewport: `${profile.width}x${profile.height}`,
      route: "/",
      ...metrics,
      syntheticInteractionDurationMs,
    });
    await context.close();
  }
} finally {
  await browser.close();
}

const report = {
  generatedAt: new Date().toISOString(),
  method: "Chrome headless local, rede local sem throttling, banco sintético dedicado; duração de interação é proxy laboratorial e não INP de campo.",
  results,
};
await writeFile(path.join(outputDir, "report.json"), JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
