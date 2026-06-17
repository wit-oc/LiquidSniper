# TradingView UI Assumptions

This automation uses TradingView Web in a persistent Chrome profile. It intentionally avoids private TradingView APIs.

## Stable Inputs

- `TV_CHROME_PROFILE_DIR` selects the browser profile.
- `TV_CHROME_CHANNEL=chromium` uses Playwright's bundled Chrome-for-Testing and is the recommended default. `TV_CHROME_CHANNEL=chrome` uses local Google Chrome and can be more sensitive to macOS profile/keychain behavior.
- Run manifests provide `chartUrl`, `symbols`, `timeframes`, and validation rules.
- Saved TradingView layouts preserve manually configured indicator settings and `input.source()` mappings.
- Use `tv-login` to log in through the same Playwright-owned Chrome launch path that later automation uses. Do not log in with a separately opened Chrome profile unless you have confirmed cookie persistence still works.

## Brittle Surfaces

- Pine Editor open/close controls.
- Monaco/editor focus and paste behavior.
- Save dialogs and script-name prompts.
- Add-to-chart compile notifications.
- Strategy Tester export menus.
- Chart data export menus.
- Authentication, subscription, cookie, and announcement popups.

## Recovery Steps

1. Run `tv-doctor` and inspect its screenshot.
2. If auth is missing, run `tv-login`; log in and save the layout in the browser it opens.
3. Close popups, restore the saved layout, and confirm Pine Editor and Strategy Tester are visible.
4. For scripts with external sources, confirm source mappings still point to the intended vendor plots.
5. Rerun the failing command with `TV_SLOW_MO_MS=250` for easier observation.

## Profile Locking

Chrome profiles are single-owner. If a manual Chrome window is open with `TV_CHROME_PROFILE_DIR`, Playwright will fail with `ProcessSingleton` or `SingletonLock`. Let `tv-login` open the browser, complete setup there, press Enter in the terminal, and allow the script to close Chrome cleanly.

On macOS, this skill removes Playwright's default mock-keychain flags so TradingView cookies are stored through the normal browser profile path. Set `TV_USE_PLAYWRIGHT_DEFAULT_KEYCHAIN=1` only if you intentionally want Playwright's default isolated keychain behavior.

## Selector Strategy

Scripts prefer accessible text and roles first, then loose CSS/text fallbacks. Avoid hardcoding obfuscated TradingView class names unless a local failure proves no better selector is available.

## Validation Strategy

Use CSV data as the pass/fail authority:

- Strategy scripts: Strategy Tester/exported trade rows and any diagnostic chart columns.
- Indicator scripts: chart-data export columns and optional custom diagnostics.
- Screenshots: only for debugging and user review.

## Pine Editor Insertion

The installer uses Monaco model assignment when available, then clipboard paste. It refuses keyboard insertion by default because TradingView's editor auto-indent can progressively shift Pine function bodies and create false compile errors such as `Mismatched input ... expecting end of line without line continuation`.

Set `TV_ALLOW_KEYBOARD_INSERT=1` only for tiny smoke snippets where indentation corruption is irrelevant.
