import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const watchlistName = process.argv[2] || 'Watchlist';
const outPath = process.argv[3] || `artifacts/tradingview/watchlist-${watchlistName.replace(/\s+/g,'_')}.json`;

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

try {
  await page.goto('https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT&interval=15', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(5000);

  // Open watchlist selector and choose target list when available.
  const selectorBtn = page.getByText(/Watchlist|Blofin Pairs/i).first();
  if (await selectorBtn.isVisible().catch(() => false)) {
    await selectorBtn.click();
    await page.waitForTimeout(800);
    const target = page.getByText(new RegExp(`^${watchlistName}$`, 'i')).first();
    if (await target.isVisible().catch(() => false)) {
      await target.click();
      await page.waitForTimeout(1200);
    }
  }

  // Scrape visible symbols; this is enough for MVP export and can be repeated with scrolling.
  const symbols = await page.$$eval('span[class*="symbolNameText"], div[class*="symbolNameText"], a[href*="symbol="]', (els) => {
    const out = new Set();
    for (const el of els) {
      const t = (el.textContent || '').trim().toUpperCase();
      if (/^[A-Z0-9:-]{4,20}$/.test(t) && (t.includes('USD') || t.includes('USDT'))) out.add(t);
    }
    return Array.from(out);
  });

  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify({ watchlist: watchlistName, symbols }, null, 2));
  console.log(JSON.stringify({ status: 'ok', watchlist: watchlistName, count: symbols.length, outPath }));
} catch (e) {
  console.log(JSON.stringify({ status: 'failed', error: String(e) }));
  process.exit(1);
} finally {
  await browser.close();
}
