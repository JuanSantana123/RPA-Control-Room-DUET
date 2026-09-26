import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright-core";

const baseUrl = process.env.DUET_FRONTEND_URL ?? "http://localhost:5173";
const executablePath = process.env.CHROME_PATH ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const outputDir = path.resolve("..", ".e2e", "component-catalog");
const cases = [
  { name: "components-390-dark", width: 390, height: 844, colorScheme: "dark" },
  { name: "components-1440-light", width: 1440, height: 1000, colorScheme: "light" },
  { name: "components-320-reduced-motion", width: 320, height: 640, colorScheme: "light", reducedMotion: "reduce" },
];

await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
const results = [];

try {
  for (const testCase of cases) {
    const context = await browser.newContext({
      viewport: { width: testCase.width, height: testCase.height },
      colorScheme: testCase.colorScheme,
      reducedMotion: testCase.reducedMotion ?? "no-preference",
      locale: "pt-BR",
    });
    await context.route("**/auth/me", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "success",
        user: {
          id: 1,
          username: "catalogo",
          name: "Catálogo local",
          is_active: 1,
          permissions: [],
        },
      }),
    }));

    const page = await context.newPage();
    const consoleErrors = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });

    await page.goto(`${baseUrl}/component-lab`, { waitUntil: "networkidle" });
    await page.getByRole("heading", { name: "Componentes da interface" }).waitFor();

    const trigger = page.getByRole("combobox", { name: "Ambiente" });
    await trigger.focus();
    await page.keyboard.press("Enter");
    await page.getByRole("listbox").waitFor();
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");

    await page.getByRole("button", { name: "Criar automação" }).focus();
    const focusVisible = await page.getByRole("button", { name: "Criar automação" }).evaluate((element) => {
      const style = getComputedStyle(element);
      return style.outlineStyle !== "none" || style.boxShadow !== "none";
    });

    const confirmationTrigger = page.getByRole("button", { name: "Abrir confirmação" });
    await confirmationTrigger.click();
    const confirmationDialog = page.getByRole("alertdialog", { name: "Publicar automação?" });
    await confirmationDialog.waitFor();
    const dialogFocused = await confirmationDialog.evaluate((dialog) => dialog.contains(document.activeElement));
    await page.keyboard.press("Escape");
    await confirmationDialog.waitFor({ state: "hidden" });
    const focusReturned = await confirmationTrigger.evaluate((trigger) => trigger === document.activeElement);

    const metrics = await page.evaluate(() => {
      const visible = (element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };
      return {
        horizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
        unnamedButtons: [...document.querySelectorAll("button")].filter((element) => visible(element) && !(element.textContent?.trim() || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby"))).length,
        unlabelledFields: [...document.querySelectorAll("input, select, textarea")].filter((element) => visible(element) && !(element.labels?.length || element.getAttribute("aria-label") || element.getAttribute("aria-labelledby"))).length,
        undersizedButtons: [...document.querySelectorAll("button")].filter((element) => {
          if (!visible(element)) return false;
          const rect = element.getBoundingClientRect();
          return rect.width < 32 || rect.height < 32;
        }).map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            name: element.getAttribute("aria-label") || element.textContent?.trim(),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          };
        }),
        reducedMotionSafe: !matchMedia("(prefers-reduced-motion: reduce)").matches || document.getAnimations().every((animation) => Number(animation.effect?.getTiming().duration ?? 0) <= 1),
      };
    });

    await page.screenshot({ path: path.join(outputDir, `${testCase.name}.png`), fullPage: true });
    results.push({ ...testCase, ...metrics, focusVisible, dialogFocused, focusReturned, consoleErrors });
    await context.close();
  }
} finally {
  await browser.close();
}

const failures = results.filter((result) => result.horizontalOverflow || result.unnamedButtons || result.unlabelledFields || result.undersizedButtons.length || !result.focusVisible || !result.dialogFocused || !result.focusReturned || !result.reducedMotionSafe || result.consoleErrors.length);
console.log(JSON.stringify({ results, failures: failures.length }, null, 2));
if (failures.length) process.exitCode = 1;
