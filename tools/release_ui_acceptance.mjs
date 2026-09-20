import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

// Public, read-only UI acceptance. No account creation, model runs or writes to the service.
// Pass AIPEDIA_PLAYWRIGHT_PACKAGE when the local installed browser bundle is external.
const require = createRequire(import.meta.url);
const pw = require(process.env.AIPEDIA_PLAYWRIGHT_PACKAGE || 'playwright');
const base = process.env.AIPEDIA_PUBLIC_URL || 'https://aipediya.com';
const phase = process.env.AIPEDIA_QA_PHASE || 'baseline';
const output = path.resolve('artifacts/acceptance-20260920/ui', phase);
fs.mkdirSync(output, { recursive: true });
const results = { base, phase, started: new Date().toISOString(), physicalDevices: 'NOT TESTED; viewport and touch emulation only', textZoomMethod: 'All engines: computed text enlargement. Chromium additionally: native browser zoom 200% via settings in an isolated QA profile, checked using innerWidth and devicePixelRatio.', engines: [], checks: [], screenshots: [], clicks: [] };
const save = () => fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
const check = (ok, message) => { if (!ok) throw new Error(message); };
async function test(engine, name, fn) {
  if (process.env.AIPEDIA_QA_CASE && name !== process.env.AIPEDIA_QA_CASE) return;
  if (process.env.AIPEDIA_QA_CASE_PATTERN && !new RegExp(process.env.AIPEDIA_QA_CASE_PATTERN).test(name)) return;
  const started = Date.now();
  try { const data = await fn(); results.checks.push({ engine, name, status: 'PASS', ms: Date.now() - started, data }); }
  catch (error) { results.checks.push({ engine, name, status: 'FAIL', ms: Date.now() - started, error: error.message }); }
  console.log(JSON.stringify(results.checks.at(-1)));
  save();
}
async function go(page, query = '?lang=en') { await page.goto(`${base}/${query}`, { waitUntil: 'networkidle' }); }
async function navigate(page, action) {
  const before = page.url();
  await Promise.all([page.waitForURL(url => url.href !== before, { waitUntil: 'networkidle' }), action()]);
}
async function capture(page, name) {
  const file = `${name}.png`;
  await page.screenshot({ path: path.join(output, file) });
  results.screenshots.push({ file, url: page.url(), viewport: page.viewportSize() });
  return file;
}
async function rows(page) {
  return page.locator('#model-rows > tr').evaluateAll(items => items.filter(x => x.querySelector('.model-name')).map(row => {
    const text = cls => (row.querySelector(cls)?.innerText || '').replace(/\s+/g, ' ').trim();
    const number = Number(text('.number-col').replace('#', ''));
    const priceText = row.querySelector('.price-col strong')?.textContent || '';
    const scoreText = row.querySelector('.checks-col strong')?.textContent || '';
    const purpose = [...row.querySelectorAll('.purpose-col .task')].map(e => e.textContent.trim()).join(' · ');
    const accessLabels = [...new Set([...row.querySelectorAll('.access-col a')].map(e => e.textContent.trim().split(' · ')[0]))];
    return { number, name: text('.model-name'), purpose, access: accessLabels.join(' · '), price: priceText.startsWith('$') ? Number(priceText.replace(/[$,\s]/g, '')) : null, score: scoreText ? Number(scoreText.replace(',', '.').match(/-?\d+(?:\.\d+)?/)?.[0]) : null, priceText: text('.price-col'), scoreText: text('.checks-col'), href: row.querySelector('.model-name').getAttribute('href') };
  }));
}
function assertOrder(items, key, desc = false) {
  const errors = [];
  let missing = false;
  for (let i = 0; i < items.length; i++) {
    let current = items[i][key];
    if (current == null || current === '' || Number.isNaN(current)) { missing = true; continue; }
    if (missing) errors.push(`known value after missing: #${items[i].number}=${current}`);
    if (i === 0) continue;
    let prior = items[i - 1][key];
    if (prior == null || prior === '' || Number.isNaN(prior)) continue;
    if (typeof current === 'string') { current = current.normalize('NFKC').toLowerCase().replaceAll('ё', 'е'); prior = prior.normalize('NFKC').toLowerCase().replaceAll('ё', 'е'); }
    if (desc ? prior < current : prior > current) errors.push(`#${items[i-1].number} ${prior} -> #${items[i].number} ${current}`);
    if (prior === current && items[i-1].number > items[i].number) errors.push(`unstable equal-value order #${items[i-1].number} -> #${items[i].number}`);
  }
  check(!errors.length, `${key} ${desc ? 'descending' : 'ascending'} actual displayed order: ${errors.slice(0, 8).join('; ')}`);
}
async function fullRows(page) {
  const match = (await page.locator('.pagination').first().innerText()).match(/\/\s*(\d+)\s/);
  const total = Number(match?.[1]);
  check(Number.isInteger(total), 'cannot read total');
  for (let i = 0; i < 60; i++) {
    const count = await page.locator('#model-rows .model-name').count();
    if (count >= total) break;
    await page.locator('#infinite-scroll').scrollIntoViewIfNeeded();
    await page.waitForFunction(count => document.querySelectorAll('#model-rows .model-name').length > count, count, { timeout: 12000 });
  }
  const all = await rows(page);
  check(all.length === total, `loaded ${all.length}/${total}`);
  check(new Set(all.map(r => r.number)).size === all.length, 'duplicate permanent numbers');
  check(new Set(all.map(r => r.href.split('?')[0])).size === all.length, 'duplicate model URLs');
  check(Number(await page.locator('#shown-count').innerText()) === total, 'shown counter differs from loaded rows');
  return all;
}
async function geometry(page) {
  return page.evaluate(async () => {
    const scroller = document.querySelector('.table-scroll');
    const num = document.querySelector('tbody .number-col');
    const model = document.querySelector('tbody .model-col');
    const hn = document.querySelector('thead .number-col');
    const hm = document.querySelector('thead .model-col');
    const initial = model.getBoundingClientRect();
    scroller.scrollLeft = 260;
    await new Promise(resolve => requestAnimationFrame(resolve));
    const n = num.getBoundingClientRect(), m = model.getBoundingClientRect(), hnr = hn.getBoundingClientRect(), hmr = hm.getBoundingClientRect();
    const range = document.createRange(); range.selectNodeContents(num);
    const metrics = { pageWidth: document.documentElement.scrollWidth, viewport: innerWidth, pageFits: document.documentElement.scrollWidth <= innerWidth + 1, innerScroll: scroller.scrollWidth > scroller.clientWidth, stickyDelta: Math.abs(initial.left - m.left), numberWidth: n.width, numberOneLine: range.getClientRects().length === 1, columnsDoNotOverlap: n.right <= m.left + 1 && hnr.right <= hmr.left + 1, headersMatch: Math.abs(n.width - hnr.width) < 1 && Math.abs(m.width - hmr.width) < 1, rowCount: document.querySelectorAll('.model-name').length };
    scroller.scrollLeft = 0;
    return metrics;
  });
}
async function matrix(browser, engine) {
  const ctx = await browser.newContext(); const page = await ctx.newPage();
  await go(page, '?lang=en&q=GPT-5.6');
  if (!await page.locator('.model-name').count()) await go(page, '?lang=en');
  const preferredCard = page.locator('.model-name').filter({ hasText: /^GPT-5\.6 Sol$/ });
  const detailPath = (await (await preferredCard.count() ? preferredCard : page.locator('.model-name').first()).getAttribute('href')).split('?')[0];
  const widths = process.env.AIPEDIA_QA_WIDTHS ? process.env.AIPEDIA_QA_WIDTHS.split(',').map(Number) : [320, 360, 390, 430, 768, 1024, 1440, 1920];
  for (const width of widths) {
    for (const lang of ['ru', 'en']) for (const theme of ['light', 'dark']) {
      await test(engine, `matrix-${width}-${lang}-${theme}`, async () => {
        await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
        await go(page, `?lang=${lang}`);
        if (await page.locator('html').getAttribute('data-theme') !== theme) await page.locator('#theme').click();
        const m = await geometry(page);
        await capture(page, `${engine}-${width}-${lang}-${theme}`);
        check(await page.locator('html').getAttribute('lang') === lang, 'language mismatch');
        check(await page.locator('html').getAttribute('data-theme') === theme, 'theme mismatch');
        check(m.pageFits, `page overflow ${m.pageWidth}/${width}`);
        check(m.columnsDoNotOverlap, 'sticky number and model columns overlap');
        check(m.headersMatch, 'header/cell columns misalign');
        check(m.numberOneLine && m.numberWidth >= 84, 'permanent number wraps/is clipped');
        if (width <= 600) check(m.innerScroll && m.stickyDelta < 2, 'mobile table/column scrolling fails');
        const controls = await page.locator('#filters select').evaluateAll(items => items.map(e => {
          const style = getComputedStyle(e); const canvas = document.createElement('canvas'); const ctx = canvas.getContext('2d'); ctx.font = `${style.fontSize} ${style.fontFamily}`;
          const selected = e.selectedOptions[0]?.textContent.trim() || ''; const firstWord = selected.split(/\s+/)[0];
          const required = ctx.measureText(firstWord).width + parseFloat(style.paddingLeft) + parseFloat(style.paddingRight) + 16;
          return { name: e.name, width: e.getBoundingClientRect().width, selected, required };
        }));
        check(controls.every(e => e.width + 1 >= e.required), `filter first word invisible: ${controls.filter(e => e.width + 1 < e.required).map(e => `${e.name}=${e.width.toFixed(1)}px (need ${e.required.toFixed(1)})`).join(', ')}`);
        if (width === 390 || width === 768) { await page.locator('.table-scroll').evaluate(e => e.scrollLeft = e.scrollWidth); await capture(page, `${engine}-${width}-${lang}-${theme}-scrolled`); }
        return m;
      });
      await test(engine, `card-${width}-${lang}-${theme}`, async () => {
        await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
        await page.goto(`${base}${detailPath}?lang=${lang}`, { waitUntil: 'networkidle' });
        if (await page.locator('html').getAttribute('data-theme') !== theme) await page.locator('#theme').click();
        const m = await page.locator('article.model-detail').evaluate(e => {
          const header = e.querySelector('.detail-prices thead th'); const range = document.createRange(); if (header) range.selectNodeContents(header);
          return { pageFits: document.documentElement.scrollWidth <= innerWidth + 1, heading: e.querySelector('h1').innerText, number: e.querySelector('.record-number')?.innerText, scores: e.querySelectorAll('.evaluation').length, tablesFit: [...e.querySelectorAll('.table-scroll')].every(t => t.getBoundingClientRect().right <= innerWidth + 1), providerHeaderLines: header ? range.getClientRects().length : 0, providerHeaderWidth: header?.getBoundingClientRect().width };
        });
        await capture(page, `${engine}-card-${width}-${lang}-${theme}`);
        check(m.pageFits && m.tablesFit, 'detail card overflows viewport');
        check(m.number?.startsWith('#'), 'detail card permanent number missing');
        check(m.providerHeaderLines <= 3, `price provider header wraps into ${m.providerHeaderLines} lines at ${m.providerHeaderWidth}px`);
        if ([390, 768, 1440].includes(width) && m.scores) { await page.locator('#evaluations').evaluate(e => e.scrollIntoView({ block: 'start' })); await capture(page, `${engine}-scores-${width}-${lang}-${theme}`); }
        return m;
      });
    }
  }
  await ctx.close();
}
async function headerClicks(browser, engine) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, recordVideo: { dir: output, size: { width: 1440, height: 1000 } } });
  const page = await ctx.newPage();
  const specs = [['number', 'number', 'number_asc', 'number_desc'], ['model', 'name', 'name_asc', 'name_desc'], ['purpose', 'purpose', 'purpose_asc', 'purpose_desc'], ['price', 'price', 'price_asc', 'price_desc'], ['access', 'access', 'access_asc', 'access_desc'], ['checks', 'score', 'check_best', 'check_worst']];
  for (const lang of (process.env.AIPEDIA_QA_SHORT_RECORDING === '1' ? [process.env.AIPEDIA_QA_SHORT_LANG || 'ru'] : ['ru', 'en'])) for (const [column, key, first, second] of specs) {
    await test(engine, `header-${lang}-${column}`, async () => {
      await go(page, `?lang=${lang}&sort=number_desc`);
      const before = await rows(page);
      const actual = [];
      for (let click = 0; click < 2; click++) {
        const cell = page.locator(`thead .${column}-col`);
        const sortLink = cell.locator('a').first();
        const button = await sortLink.count() ? sortLink : cell.locator('button').first();
        const previousURL = page.url();
        if (await sortLink.count()) await navigate(page, () => button.click());
        else { await button.click(); await page.waitForTimeout(250); await page.waitForLoadState('networkidle'); }
        const now = await rows(page);
        const state = { engine, lang, column, click: click + 1, beforeURL: previousURL, url: page.url(), ariaSort: await page.locator(`thead .${column}-col`).getAttribute('aria-sort'), values: now.slice(0, 8).map(r => ({ number: r.number, value: r[key], shown: key === 'price' ? r.priceText : key === 'score' ? r.scoreText : r[key] })) };
        results.clicks.push(state); actual.push({ state, now }); save();
        if (phase !== 'baseline' && phase !== 'baseline-confirmed' && process.env.AIPEDIA_QA_SHORT_RECORDING !== '1') {
          const all = await fullRows(page);
          actual.at(-1).all = all;
          await page.evaluate(() => scrollTo(0, 0));
        }
        await page.waitForTimeout(180);
      }
      const expected = [first, second];
      for (let i = 0; i < 2; i++) {
        check(new URL(actual[i].state.url).searchParams.get('sort') === expected[i], `click ${i+1} did not set ${expected[i]}: ${actual[i].state.url}`);
        check(actual[i].state.ariaSort && actual[i].state.ariaSort !== 'none', `click ${i+1} missing active aria-sort`);
        check(!new URL(actual[i].state.url).searchParams.get('category'), 'header click silently applies category filter');
        assertOrder(actual[i].all || actual[i].now, key, key === 'score' ? i === 0 : i === 1);
      }
      check(JSON.stringify(actual[0].now.map(x => x.number)) !== JSON.stringify(actual[1].now.map(x => x.number)), 'second click did not change actual rows');
      return { total: actual[0].all?.length, first: actual[0].state, second: actual[1].state };
    });
  }
  const video = page.video(); await ctx.close();
  await video.saveAs(path.join(output, `${engine}-header-clicks.webm`));
}
async function flows(browser, engine) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } }); const page = await ctx.newPage(); const pageErrors = [];
  page.on('pageerror', e => pageErrors.push(e.message));
  await test(engine, 'public-build-health', async () => {
    await go(page);
    const health = await page.evaluate(async () => { const response = await fetch('/healthz'); return { status: response.status, body: await response.json() }; });
    check(health.status === 200 && health.body.service === 'aipedia' && health.body.status === 'ok', `health endpoint: ${JSON.stringify(health)}`);
    if (process.env.AIPEDIA_EXPECTED_BUILD) check(health.body.release === process.env.AIPEDIA_EXPECTED_BUILD, `deployed commit ${health.body.release} differs from expected ${process.env.AIPEDIA_EXPECTED_BUILD}`);
    return health;
  });
  await test(engine, 'static-assets-and-public-fingerprints', async () => {
    await go(page);
    const urls = await page.locator('link[rel=stylesheet], script[src]').evaluateAll(items => items.map(e => e.href || e.src).filter(url => new URL(url).pathname.startsWith('/static/')));
    check(urls.length >= 4, 'expected CSS and JavaScript assets absent');
    const assets = [];
    for (const url of urls) {
      const response = await page.evaluate(async url => { const response = await fetch(url); return { status: response.status, ok: response.ok, type: response.headers.get('content-type'), cache: response.headers.get('cache-control') }; }, url);
      check(response.ok, `asset ${url} returned ${response.status}`);
      if (new URL(base).protocol === 'https:') check(/\.[a-f0-9]{12}\.(css|js)$/.test(new URL(url).pathname), `public asset is not fingerprinted: ${url}`);
      assets.push({ url, ...response });
    }
    return assets;
  });
  await test(engine, 'full-pagination', async () => { await go(page, '?lang=en&sort=number_asc'); const all = await fullRows(page); assertOrder(all, 'number'); return { total: all.length, numbers: all.map(r => r.number) }; });
  await test(engine, 'detail-back-filter-state', async () => {
    await go(page, '?lang=en&q=gpt&sort=number_desc');
    const first = (await rows(page))[0]; await navigate(page, () => page.locator('.model-name').first().click()); await page.locator('article.model-detail').waitFor();
    check((await page.locator('.record-number').innerText()).includes(String(first.number)), 'detail permanent number differs');
    check(await page.locator('html').evaluate(e => e.scrollWidth <= innerWidth), 'detail page overflow');
    await capture(page, `${engine}-detail-desktop-en`);
    await navigate(page, () => page.locator('.back').click());
    check(new URL(page.url()).searchParams.get('q') === 'gpt' && new URL(page.url()).searchParams.get('sort') === 'number_desc', 'detail back loses state');
    check((await rows(page))[0].number === first.number, 'detail back changes first row');
  });
  await test(engine, 'page-two-detail-back-state', async () => {
    await go(page, '?lang=en&sort=number_asc&page=2');
    const secondPage = await rows(page); const first = secondPage[0].number;
    check(Number(await page.locator('#shown-count').innerText()) === secondPage.length, 'direct page 2 shown count differs from actual rows');
    await navigate(page, () => page.locator('.model-name').first().click());
    check(new URL(page.url()).searchParams.get('page') === '2', 'detail URL loses originating page 2');
    await navigate(page, () => page.locator('.back').click());
    check(new URL(page.url()).searchParams.get('page') === '2', 'back link loses originating page 2');
    check((await rows(page))[0].number === first, 'page 2 back changes first number');
    check(Number(await page.locator('#shown-count').innerText()) === (await rows(page)).length, 'page 2 back shown count differs from actual rows');
    return { first, url: page.url() };
  });
  await test(engine, 'retry-after-failed-next-page', async () => {
    let failed = false;
    await page.route('**/*partial=rows*', async route => { if (!failed) { failed = true; await route.fulfill({ status: 503, body: 'simulated temporary failure' }); } else await route.continue(); });
    await go(page); await page.locator('#infinite-scroll').scrollIntoViewIfNeeded(); await page.getByRole('button', { name: 'Retry', exact: true }).waitFor(); await page.getByRole('button', { name: 'Retry', exact: true }).click();
    await page.waitForFunction(() => document.querySelectorAll('.model-name').length > 25);
    const all = await rows(page); check(new Set(all.map(r => r.number)).size === all.length, 'retry duplicates rows'); await page.unrouteAll();
  });
  await test(engine, 'slow-network-filter-race', async () => {
    let started; const pending = new Promise(resolve => started = resolve);
    await page.route('**/*partial=rows*', async route => { started(); await new Promise(resolve => setTimeout(resolve, 1600)); try { await route.continue(); } catch {} });
    await go(page); await page.locator('#infinite-scroll').scrollIntoViewIfNeeded(); await pending;
    await page.locator('input[name=q]').fill('claude'); await navigate(page, () => page.locator('input[name=q]').press('Enter')); await page.waitForTimeout(1800);
    const all = await rows(page); check(all.length > 0 && all.every(r => r.name.toLowerCase().includes('claude')), 'stale next-page response contaminates new filter'); await page.unrouteAll(); return { rows: all.length };
  });
  await test(engine, 'empty-search-and-archive', async () => {
    await go(page, '?lang=en&q=aipedia-no-such-model-987654321'); check((await rows(page)).length === 0 && await page.locator('.empty').count() === 1, 'empty state absent');
    await navigate(page, () => page.locator('.empty a').click()); check((await rows(page)).length > 0, 'empty reset broken');
    await navigate(page, () => page.selectOption('select[name=status]', 'archived')); const archive = await rows(page);
    check(new URL(page.url()).searchParams.get('status') === 'archived', 'archive filter URL missing');
    await navigate(page, () => page.selectOption('select[name=status]', 'all')); const all = await fullRows(page); return { archive: archive.length, all: all.length };
  });
  await test(engine, 'separate-filter-action', async () => {
    await go(page, '?lang=en&sort=number_desc'); const original = (await rows(page)).map(r => r.number);
    const filter = page.locator('thead [data-filter-control="category"]'); await filter.click();
    check(new URL(page.url()).searchParams.get('sort') === 'number_desc', 'filter button changes sort');
    check(JSON.stringify((await rows(page)).map(r => r.number)) === JSON.stringify(original), 'filter open reorders rows');
    check(await page.locator('select[name=category]').evaluate(e => e === document.activeElement), 'filter action does not focus its control');
    await navigate(page, () => page.selectOption('select[name=category]', { index: 1 }));
    check(Boolean(new URL(page.url()).searchParams.get('category')), 'category selection not applied');
    return { url: page.url() };
  });
  await test(engine, 'keyboard-sort-focus', async () => {
    await go(page, '?lang=en&sort=number_desc');
    const link = page.locator('thead .number-col a').first(); await link.focus(); check(await link.evaluate(e => e === document.activeElement), 'header link cannot receive keyboard focus'); await navigate(page, () => page.keyboard.press('Enter')); assertOrder(await rows(page), 'number');
    await page.locator('.table-scroll').focus(); await page.keyboard.press('ArrowRight');
  });
  await test(engine, 'combined-filter-price-score-detail-full-list', async () => {
    await go(page, '?lang=en&sort=number_asc');
    const opts = await page.locator('select[name=category] option').evaluateAll(items => items.map(e => ({ value: e.value, label: e.textContent.trim() })));
    const textOption = opts.find(e => e.label === 'Text');
    const speechOption = opts.find(e => /speech/i.test(e.label));
    check(textOption && speechOption, 'text/speech category choices missing');
    for (const option of [speechOption, textOption]) {
      await navigate(page, () => page.selectOption('select[name=category]', option.value));
      const selected = await fullRows(page);
      check(selected.length > 0 && selected.every(row => row.purpose.split(' · ').includes(option.label)), `${option.label} filter shows unrelated tasks`);
    }
    const priceLink = page.locator('thead .price-col a[data-sort]');
    check(await priceLink.count() > 0, 'price header is not a separate sort link');
    await navigate(page, () => priceLink.click());
    check(await page.locator('select[name=price_unit]').inputValue() === 'input', 'default comparison is not input / 1M tokens');
    check(await page.locator('select[name=price_scope]').inputValue() === 'standard', 'default comparison is not standard price conditions');
    const priced = await fullRows(page); assertOrder(priced, 'price');
    check(priced.some(r => r.price !== null), 'no selected comparable price shown');
    const benchmarks = await page.locator('select[name=benchmark] option').evaluateAll(items => items.filter(e => e.value).map(e => ({ value: e.value, label: e.textContent })));
    const selectedBenchmark = benchmarks.find(e => /\bECI\b/.test(e.label)) || benchmarks[0];
    check(selectedBenchmark, 'no score selector values');
    if (await page.locator('select[name=benchmark]').inputValue() !== selectedBenchmark.value) await navigate(page, () => page.selectOption('select[name=benchmark]', selectedBenchmark.value));
    await navigate(page, () => page.locator('thead .checks-col a[data-sort]').click());
    const scored = await fullRows(page);
    assertOrder(scored, 'score', true);
    check(scored.some(r => r.score !== null), 'selected score has no comparable rows');
    const state = new URL(page.url()).searchParams;
    await page.evaluate(() => scrollTo(0, 0));
    const selectedNumber = (await rows(page))[0].number;
    await navigate(page, () => page.locator('.model-name').first().click());
    check((await page.locator('.record-number').innerText()).includes(String(selectedNumber)), 'integrated flow loses permanent number');
    await navigate(page, () => page.locator('.back').click());
    for (const key of ['lang', 'category', 'price_unit', 'price_scope', 'benchmark', 'sort']) check(new URL(page.url()).searchParams.get(key) === state.get(key), `detail back loses ${key}`);
    const returned = await fullRows(page);
    check(returned.map(r => r.number).join() === scored.map(r => r.number).join(), 'returned complete list differs');
    return { category: textOption.label, benchmark: selectedBenchmark.label, total: returned.length, scores: returned.filter(r => r.score !== null).length };
  });
  await test(engine, 'score-filter-and-mode-identity', async () => {
    await go(page, '?lang=en&status=all&sort=check_best');
    const all = await fullRows(page); const measured = all.filter(r => r.score !== null);
    check(measured.length > 1 && all.length > measured.length, 'expected measured and unknown ECI rows');
    check(await page.locator('select[name=configuration]').count() === 1 && await page.locator('select[name=snapshot]').count() === 1, 'score mode/snapshot selectors missing');
    await navigate(page, () => page.locator('input[name=evaluated_only]').check());
    const only = await fullRows(page);
    check(only.map(r => r.number).join() === measured.map(r => r.number).join(), 'only measured filter changes scores or includes missing rows');
    const benchmarks = await page.locator('select[name=benchmark] option').evaluateAll(items => items.map(e => ({ value: e.value, label: e.textContent })));
    const multi = benchmarks.find(e => e.label.startsWith('Mock AIME 2024/2025 · '));
    check(multi, 'expected multi-configuration Mock AIME 2024/2025 benchmark not available');
    await navigate(page, () => page.selectOption('select[name=benchmark]', multi.value));
    const modes = await page.locator('select[name=configuration] option').evaluateAll(items => items.map(e => ({ value: e.value, label: e.textContent.trim() })));
    check(modes.length > 1, 'multiple published configurations collapsed');
    const observations = [];
    for (const mode of [modes[0], modes.at(-1)]) {
      if (await page.locator('select[name=configuration]').inputValue() !== mode.value) await navigate(page, () => page.selectOption('select[name=configuration]', mode.value));
      const selected = await fullRows(page);
      check(selected.length > 0 && selected.every(r => r.score !== null && r.scoreText.includes(mode.label)), `selected ${mode.label} mixes modes or has no displayed scores`);
      assertOrder(selected, 'score', true);
      observations.push({ mode: mode.label, rows: selected.length, snapshot: await page.locator('select[name=snapshot]').inputValue() });
    }
    return { all: all.length, measured: measured.length, modes: observations };
  });
  await test(engine, 'language-preserves-price-conditions', async () => {
    await go(page, '?lang=en&sort=price_asc&price_unit=input&price_scope=standard&price_variant=base');
    const en = await fullRows(page);
    await navigate(page, () => page.getByRole('link', { name: 'RU', exact: true }).click());
    const ru = await fullRows(page);
    check(en.map(r => `${r.number}:${r.price}`).join() === ru.map(r => `${r.number}:${r.price}`).join(), 'language switch changes comparison prices or ordering');
    for (const [key, value] of Object.entries({ price_unit: 'input', price_scope: 'standard', price_variant: 'base', sort: 'price_asc' })) check(new URL(page.url()).searchParams.get(key) === value, `language switch loses ${key}`);
    const conditions = await page.locator('.price-col .price-condition').allTextContents();
    check(conditions.length > 0 && conditions.every(t => t.includes(' · ') && t.split(' · ').at(-1).trim()), 'provider or price condition disappears in RU');
    return { compared: ru.length, priced: ru.filter(r => r.price !== null).length };
  });
  await test(engine, 'price-modality-isolation', async () => {
    await go(page, '?lang=en&sort=price_asc&price_unit=input&price_scope=standard&price_variant=base&price_modality=text');
    const evidence = [];
    for (const modality of ['text', 'audio', 'image']) {
      if (await page.locator('select[name=price_modality]').inputValue() !== modality) await navigate(page, () => page.selectOption('select[name=price_modality]', modality));
      const all = await fullRows(page); assertOrder(all, 'price');
      const known = all.filter(r => r.price !== null);
      const basis = await page.locator('.comparison-basis').innerText();
      check(basis.toLowerCase().includes(modality), `comparison basis loses ${modality}`);
      if (!known.length) check(basis.includes('No matching offers'), `empty ${modality} price comparison has no explanation`);
      if (modality !== 'text') check(known.every(r => r.priceText.toLowerCase().includes(modality)), `${modality} price cell hides billed token modality`);
      evidence.push({ modality, count: known.length, first: known.slice(0, 5).map(r => ({ number: r.number, price: r.price, shown: r.priceText })) });
    }
    check(new Set(evidence.map(e => JSON.stringify(e.first.map(r => [r.number, r.price])))).size > 1, 'modality selection does not change prices');
    return evidence;
  });
  await test(engine, 'text-200-percent', async () => {
    await page.setViewportSize({ width: 390, height: 844 }); await go(page, '?lang=ru');
    await page.evaluate(() => { const values = [...document.querySelectorAll('body *')].map(e => [e, getComputedStyle(e).fontSize, getComputedStyle(e).lineHeight]); for (const [e, fontSize, lineHeight] of values) { e.style.fontSize = `${parseFloat(fontSize) * 2}px`; if (/^[\d.]+px$/.test(lineHeight)) e.style.lineHeight = `${parseFloat(lineHeight) * 2}px`; } });
    await capture(page, `${engine}-390-ru-text-200`); const m = await geometry(page); check(m.pageFits, `200% text overflow ${m.pageWidth}/390`); check(m.columnsDoNotOverlap, '200% text sticky columns overlap'); return m;
  });
  await test(engine, 'javascript-errors', async () => { check(!pageErrors.length, pageErrors.join('; ')); return pageErrors; });
  await ctx.close();
  const touch = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, ...(engine !== 'firefox' ? { isMobile: true } : {}) }); const tp = await touch.newPage();
  await test(engine, 'touch-portrait-landscape-detail', async () => {
    await go(tp, '?lang=ru&sort=number_desc'); await navigate(tp, () => tp.locator('thead .number-col a').first().tap()); assertOrder(await rows(tp), 'number');
    await navigate(tp, () => tp.locator('.model-name').first().tap()); await tp.locator('.model-detail').waitFor(); await capture(tp, `${engine}-touch-390-detail-ru`); check(await tp.locator('html').evaluate(e => e.scrollWidth <= innerWidth), 'portrait detail overflows');
    await navigate(tp, () => tp.locator('.back').tap()); await tp.setViewportSize({ width: 844, height: 390 }); await capture(tp, `${engine}-touch-landscape-ru`); const m = await geometry(tp); check(m.pageFits, 'landscape overflows'); return m;
  });
  await test(engine, 'touch-all-six-headers-both-directions', async () => {
    await tp.setViewportSize({ width: 390, height: 844 });
    const evidence = [];
    for (const lang of ['ru', 'en']) for (const [column, key] of [['number', 'number'], ['model', 'name'], ['purpose', 'purpose'], ['price', 'price'], ['access', 'access'], ['checks', 'score']]) {
      await go(tp, `?lang=${lang}&sort=number_desc`);
      for (let click = 0; click < 2; click++) {
        const target = tp.locator(`thead .${column}-col a[data-sort]`);
        await target.scrollIntoViewIfNeeded();
        await navigate(tp, () => target.tap());
        const visible = await rows(tp); assertOrder(visible, key, key === 'score' ? click === 0 : click === 1);
        evidence.push({ lang, column, click: click + 1, sort: new URL(tp.url()).searchParams.get('sort'), first: visible[0]?.number });
      }
    }
    return evidence;
  });
  await touch.close();
  const nojs = await browser.newContext({ javaScriptEnabled: false }); const np = await nojs.newPage();
  await test(engine, 'no-js-pagination-detail-sorting', async () => {
    await go(np, '?lang=en'); const first = (await rows(np))[0].number; await np.locator('.pagination nav a').last().click(); await np.waitForLoadState('domcontentloaded'); check((await rows(np))[0].number !== first, 'no-JS pagination does not change rows');
    await np.locator('.model-name').first().click(); await np.locator('.model-detail').waitFor(); await np.locator('.back').click(); await np.waitForLoadState('domcontentloaded');
    for (const column of ['number', 'model', 'purpose', 'price', 'access', 'checks']) check(await np.locator(`thead .${column}-col a`).count() > 0, `no-JS ${column} sorting unavailable`);
  }); await nojs.close();
}
async function nativeZoom() {
  const profile = path.resolve(output, 'native-zoom-profile');
  check(profile.startsWith(`${output}${path.sep}`), 'QA profile must stay inside current output directory');
  const ctx = await pw.chromium.launchPersistentContext(profile, { headless: true, executablePath: process.env.AIPEDIA_CHROMIUM_REGULAR_EXECUTABLE || pw.chromium.executablePath(), viewport: null, args: ['--window-size=1440,1000'] });
  try {
    const page = await ctx.newPage(); await page.goto('chrome://settings/appearance');
    await page.locator('#zoomLevel').selectOption({ label: '200%' });
    const cdp = await ctx.newCDPSession(page);
    const captureZoom = async name => {
      // At native page zoom, Playwright's automatic CSS clip crops the bitmap.
      // Unclipped CDP capture preserves the entire physical viewport instead.
      const result = await cdp.send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
      const file = `${name}.png`;
      fs.writeFileSync(path.join(output, file), Buffer.from(result.data, 'base64'));
      results.screenshots.push({ file, url: page.url(), viewport: await page.evaluate(() => ({ width: innerWidth, height: innerHeight, devicePixelRatio })), method: 'native zoom, full physical viewport via CDP' });
    };
    for (const lang of ['ru', 'en']) for (const theme of ['light', 'dark']) {
      await test('chromium', `native-zoom200-${lang}-${theme}`, async () => {
        await go(page, `?lang=${lang}&sort=number_desc`);
        if (await page.locator('html').getAttribute('data-theme') !== theme) await page.locator('#theme').click();
        const metrics = await page.evaluate(() => ({ innerWidth, outerWidth, devicePixelRatio, pageWidth: document.documentElement.scrollWidth }));
        check(metrics.devicePixelRatio === 2 && metrics.outerWidth >= 1400 && metrics.innerWidth < 800, `native zoom not applied: ${JSON.stringify(metrics)}`);
        await captureZoom(`chromium-native-zoom200-${lang}-${theme}`);
        check(metrics.pageWidth <= metrics.innerWidth + 1, 'native zoom causes outer page overflow');
        await navigate(page, () => page.locator('thead .number-col a[data-sort]').click()); assertOrder(await rows(page), 'number');
        await navigate(page, () => page.locator('.model-name').first().click());
        await captureZoom(`chromium-native-zoom200-card-${lang}-${theme}`);
        check(await page.locator('html').evaluate(e => e.scrollWidth <= innerWidth + 1), 'native zoom detail overflows');
        return metrics;
      });
    }
  } finally {
    await ctx.close();
    const allowedRoot = path.resolve('artifacts/acceptance-20260920/ui');
    const resolvedProfile = path.resolve(profile);
    check(resolvedProfile.startsWith(`${allowedRoot}${path.sep}`) && resolvedProfile === path.resolve(output, 'native-zoom-profile'), 'refusing to remove a QA profile outside the verified UI artifact root');
    fs.rmSync(resolvedProfile, { recursive: true, force: true, maxRetries: 4, retryDelay: 250 });
  }
}
async function runEngine(engine) {
  let browser;
  try {
    browser = await pw[engine].launch({ headless: true, ...(process.env[`AIPEDIA_${engine.toUpperCase()}_EXECUTABLE`] ? { executablePath: process.env[`AIPEDIA_${engine.toUpperCase()}_EXECUTABLE`] } : {}) });
    results.engines.push({ name: engine, version: browser.version() }); save();
    if (process.env.AIPEDIA_QA_MATRIX_ONLY !== '1' && process.env.AIPEDIA_QA_FLOWS_ONLY !== '1') await headerClicks(browser, engine);
    if (process.env.AIPEDIA_QA_HEADERS_ONLY !== '1') {
      if (process.env.AIPEDIA_QA_FLOWS_ONLY !== '1') await matrix(browser, engine);
      if (process.env.AIPEDIA_QA_MATRIX_ONLY !== '1') { await flows(browser, engine); if (engine === 'chromium' && !process.env.AIPEDIA_QA_CASE && !process.env.AIPEDIA_QA_CASE_PATTERN) await nativeZoom(); }
    }
  } catch (error) { results.checks.push({ engine, name: 'engine', status: 'BLOCKED', error: error.message }); save(); }
  finally { if (browser) await browser.close(); }
}
const requestedEngines = ['chromium', 'firefox', 'webkit'].filter(name => !process.env.AIPEDIA_QA_BROWSER || name === process.env.AIPEDIA_QA_BROWSER);
if (process.env.AIPEDIA_QA_PARALLEL === '1') await Promise.all(requestedEngines.map(runEngine));
else for (const engine of requestedEngines) await runEngine(engine);
results.completed = new Date().toISOString();
results.summary = Object.fromEntries(['PASS', 'FAIL', 'BLOCKED'].map(status => [status, results.checks.filter(r => r.status === status).length]));
save();
fs.writeFileSync(path.join(output, 'qa-matrix.csv'), ['engine,check,status,error', ...results.checks.map(r => [r.engine, r.name, r.status, r.error || ''].map(v => `"${String(v).replaceAll('"', '""')}"`).join(','))].join('\n'));
console.log(JSON.stringify({ output, ...results.summary }));
process.exitCode = results.summary.FAIL || results.summary.BLOCKED ? 1 : 0;
