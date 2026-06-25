/**
 * Captura screenshots do dashboard com Playwright.
 *
 * Pré-requisitos:
 *   npm install playwright       (na raiz do projeto ou em um diretório temporário)
 *   npx playwright install chromium
 *
 * Uso (a partir da raiz do repositório):
 *   node scripts/take-dashboard-screenshots.mjs
 *
 * Requisitos de ambiente:
 *   - Backend rodando em http://localhost:8000  (uvicorn app.main:app --port 8000)
 *   - Frontend rodando em http://localhost:3000  (npm run dev)
 *   - Banco com dados de demonstração (python scripts/seed_demo_data.py)
 */

import { chromium } from "playwright";
import { mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = resolve(ROOT, "docs/screenshots");
mkdirSync(OUT, { recursive: true });

const BASE = "http://localhost:3000";

async function shot(page, filename, url, action) {
  console.log(`→ ${filename}`);
  await page.goto(url, { waitUntil: "networkidle" });
  if (action) await action(page);
  await page.waitForTimeout(600);
  await page.screenshot({ path: `${OUT}/${filename}`, fullPage: true });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();

  await shot(page, "01-overview.png", `${BASE}/`);

  await shot(page, "02-watchlist-all.png", `${BASE}/watchlist`);

  await shot(page, "03-watchlist-bullish.png", `${BASE}/watchlist`, async (p) => {
    await p.getByRole("button", { name: "Alta" }).click();
    await p.waitForTimeout(500);
  });

  await shot(page, "04-watchlist-bearish.png", `${BASE}/watchlist`, async (p) => {
    await p.getByRole("button", { name: "Baixa" }).click();
    await p.waitForTimeout(500);
  });

  await shot(page, "05-asset-detail-itub4.png", `${BASE}/assets/ITUB4.SA`);

  await shot(page, "06-asset-detail-mglu3.png", `${BASE}/assets/MGLU3.SA`);

  await shot(page, "07-asset-detail-error.png", `${BASE}/assets/NOSUCH.SA`);

  await shot(page, "08-backtests-list.png", `${BASE}/backtests`);

  await shot(page, "09-backtests-detail.png", `${BASE}/backtests`, async (p) => {
    const petrBtn = p.locator("article button", { hasText: "PETR4" });
    if (await petrBtn.count() > 0) {
      await petrBtn.first().click();
    } else {
      await p.locator("article button").first().click();
    }
    await p.waitForTimeout(1500);
    await p.waitForLoadState("networkidle");
  });

  await ctx.close();

  const mobileCtx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobilePage = await mobileCtx.newPage();
  await shot(mobilePage, "10-overview-mobile.png", `${BASE}/`);
  await shot(mobilePage, "11-watchlist-mobile.png", `${BASE}/watchlist`);
  await mobileCtx.close();

  await browser.close();
  console.log("\nScreenshots salvos em:", OUT);
})();
