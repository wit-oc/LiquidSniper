import path from 'node:path';
import { createRequire } from 'node:module';

async function loadPlaywright() {
  const attempts = [];
  const requireBases = [
    path.join(process.cwd(), 'package.json'),
    import.meta.url,
  ];

  for (const base of requireBases) {
    try {
      return createRequire(base)('playwright');
    } catch (error) {
      attempts.push(`${base}: ${error.message}`);
    }
  }

  try {
    return await import('playwright');
  } catch (error) {
    attempts.push(`dynamic import: ${error.message}`);
  }

  throw new Error(
    `Missing Playwright dependency. Install it in the active repo or environment with "npm install playwright". Attempts: ${attempts.join(' | ')}`,
  );
}

export async function launchTradingView({ defaults = {}, artifactsDir }) {
  const profileEnv = defaults.chromeProfileEnv || 'TV_CHROME_PROFILE_DIR';
  const profileDir = process.env[profileEnv] || defaults.chromeProfileDir;
  if (!profileDir) {
    throw new Error(`Missing ${profileEnv}. Point it to a dedicated Chrome profile already logged into TradingView.`);
  }

  const { chromium } = await loadPlaywright();
  const browserChannel = process.env.TV_CHROME_CHANNEL || defaults.chromeChannel || 'chromium';
  const ignoreDefaultArgs = process.env.TV_USE_PLAYWRIGHT_DEFAULT_KEYCHAIN === '1'
    ? []
    : (defaults.ignoreDefaultArgs || [
      '--use-mock-keychain',
      '--password-store=basic',
      '--disable-sync',
    ]);
  let context;
  const launchOptions = {
    headless: String(process.env.TV_HEADLESS || defaults.headless || 'false') === 'true',
    ignoreDefaultArgs,
    acceptDownloads: true,
    downloadsPath: path.join(artifactsDir, 'downloads'),
    slowMo: Number(process.env.TV_SLOW_MO_MS || defaults.slowMoMs || 0),
    viewport: defaults.viewport || { width: 1440, height: 950 },
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-default-browser-check',
      '--no-first-run',
    ],
  };
  if (process.env.TV_CHROME_EXECUTABLE) {
    launchOptions.executablePath = process.env.TV_CHROME_EXECUTABLE;
  } else if (browserChannel && browserChannel !== 'chromium') {
    launchOptions.channel = browserChannel;
  }
  try {
    context = await chromium.launchPersistentContext(path.resolve(profileDir), launchOptions);
  } catch (error) {
    if (/ProcessSingleton|SingletonLock|profile directory.*in use/i.test(String(error.message || error))) {
      throw new Error(
        `Chrome profile is already in use: ${profileDir}. Close every Chrome window launched with that --user-data-dir before running this command. Playwright must own the dedicated automation profile while it runs. Original error: ${error.message}`,
      );
    }
    if (/Browser\.getWindowForTarget|Browser window not found/i.test(String(error.message || error))) {
      throw new Error(
        `Chrome launched but Playwright could not attach to a browser window. Use the bundled Playwright Chrome-for-Testing path by setting TV_CHROME_CHANNEL=chromium, or create a fresh TV_CHROME_PROFILE_DIR. Current channel: ${browserChannel}. Original error: ${error.message}`,
      );
    }
    throw error;
  }
  context.setDefaultTimeout(Number(process.env.TV_TIMEOUT_MS || defaults.timeoutMs || 30000));
  context.setDefaultNavigationTimeout(Number(process.env.TV_NAV_TIMEOUT_MS || defaults.navigationTimeoutMs || 60000));
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: 'https://www.tradingview.com' }).catch(() => {});
  const page = context.pages()[0] || await context.newPage();
  return { context, page };
}
