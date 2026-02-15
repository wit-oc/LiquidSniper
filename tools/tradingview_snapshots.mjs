import { chromium } from 'playwright';
import fs from 'node:fs';

const symbol = process.argv[2] || 'BINANCE:BTCUSDT';
const outDir = process.argv[3] || 'artifacts/tradingview/snapshots';
const intervals = ['15', '60', '240', '1D', '1W'];

fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

const results = [];
for (const iv of intervals) {
  const url = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(iv)}`;
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    const path = `${outDir}/${symbol.replace(':', '_')}_${iv}.png`;
    await page.screenshot({ path, fullPage: false });
    results.push({ interval: iv, status: 'ok', path, url: page.url() });
  } catch (e) {
    results.push({ interval: iv, status: 'failed', error: String(e), url });
  }
}

await browser.close();
fs.writeFileSync(`${outDir}/report.json`, JSON.stringify({ symbol, results }, null, 2));
console.log(JSON.stringify({ symbol, results }, null, 2));
