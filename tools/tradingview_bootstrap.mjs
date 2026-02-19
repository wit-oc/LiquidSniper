import { chromium } from 'playwright';
import { execSync } from 'node:child_process';
import fs from 'node:fs';

function getSecret(name) {
  try {
    const out = execSync(`security find-generic-password -a openclaw -s ${name} -w`, { encoding: 'utf8' }).trim();
    return out || null;
  } catch {
    return process.env[name] || null;
  }
}

const username = getSecret('LIQUIDSNIPER_TV_USERNAME');
const password = getSecret('LIQUIDSNIPER_TV_PASSWORD');
if (!username || !password) {
  console.error('Missing TradingView credentials in keychain/env');
  process.exit(2);
}

const outDir = 'artifacts/tradingview';
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();

try {
  await page.goto('https://www.tradingview.com/accounts/signin/', { waitUntil: 'domcontentloaded', timeout: 45000 });

  // Landing page may require clicking "Email" before fields render.
  const emailButton = page.getByRole('button', { name: 'Email' });
  await emailButton.waitFor({ timeout: 15000 });
  await emailButton.click();
  await page.waitForTimeout(1200);

  const emailInput = page.locator('input[name="id_username"], input[name="username"], input[name="email"], input[type="email"], input[id*="username" i]').first();
  const pwInput = page.locator('input[name="id_password"], input[name="password"], input[type="password"], input[id*="password" i]').first();

  await emailInput.waitFor({ timeout: 20000 });
  await emailInput.fill(username);
  await pwInput.fill(password);

  const submitBtn = page.locator('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")').first();
  await submitBtn.click();

  await page.waitForTimeout(7000);
  const url = page.url();
  await page.screenshot({ path: `${outDir}/bootstrap-result.png`, fullPage: true });

  let status = 'auth_required';
  if (url.includes('/chart') || url.includes('/accounts/profile')) status = 'ok';
  if (url.includes('/accounts/signin')) status = 'failed';

  const report = {
    status,
    url,
    screenshot: `${outDir}/bootstrap-result.png`,
    note: 'If status!=ok, complete one interactive login on Mac mini and retry with persisted profile.',
  };
  fs.writeFileSync(`${outDir}/bootstrap-report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
} catch (e) {
  await page.screenshot({ path: `${outDir}/bootstrap-error.png`, fullPage: true }).catch(() => {});
  const report = { status: 'failed', error: String(e), screenshot: `${outDir}/bootstrap-error.png` };
  fs.writeFileSync(`${outDir}/bootstrap-report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report));
  process.exit(1);
} finally {
  await browser.close();
}
