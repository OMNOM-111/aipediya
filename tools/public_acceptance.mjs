import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium, firefox, webkit } = require("playwright");

const base = process.env.AIPEDIA_PUBLIC_URL || "https://aipediya.com";
const output = path.resolve("artifacts", "public-acceptance-2026-09-19");
fs.mkdirSync(output, { recursive: true });

function check(condition, message) {
  if (!condition) throw new Error(message);
}

async function tableChecks(page, width, height) {
  await page.setViewportSize({ width, height });
  await page.goto(`${base}/?lang=ru`, { waitUntil: "networkidle" });
  await page.locator(".model-name").first().waitFor();
  const metrics = await page.locator(".table-scroll").evaluate((element) => {
    const number = element.querySelector("tbody .number-col");
    const model = element.querySelector("tbody .model-col");
    const headerNumber = element.querySelector("thead .number-col");
    const headerModel = element.querySelector("thead .model-col");
    const before = model.getBoundingClientRect().x;
    element.scrollLeft = 200;
    const after = model.getBoundingClientRect().x;
    const numberAfter = number.getBoundingClientRect();
    const modelAfter = model.getBoundingClientRect();
    const headerNumberAfter = headerNumber.getBoundingClientRect();
    const headerModelAfter = headerModel.getBoundingClientRect();
    element.scrollLeft = 0;
    const numberRange = document.createRange();
    numberRange.selectNodeContents(number);
    return {
      pageFits: document.documentElement.scrollWidth <= window.innerWidth,
      tableScrolls: element.scrollWidth > element.clientWidth,
      stickyDelta: Math.abs(after - before),
      numberWidth: number.getBoundingClientRect().width,
      numberOneLine: numberRange.getClientRects().length === 1,
      rowColumnsDoNotOverlap: numberAfter.right <= modelAfter.left + 1,
      headerColumnsDoNotOverlap: headerNumberAfter.right <= headerModelAfter.left + 1,
      matchingColumnWidths: Math.abs(numberAfter.width - headerNumberAfter.width) < 1
        && Math.abs(modelAfter.width - headerModelAfter.width) < 1,
    };
  });
  check(metrics.pageFits, `page overflow at ${width}px`);
  check(metrics.numberWidth >= 84, `number column too narrow at ${width}px`);
  check(metrics.numberOneLine, `number wraps at ${width}px`);
  check(metrics.rowColumnsDoNotOverlap, `number overlaps model at ${width}px`);
  check(metrics.headerColumnsDoNotOverlap, `number header overlaps model header at ${width}px`);
  check(metrics.matchingColumnWidths, `headers and cells differ in width at ${width}px`);
  if (width <= 600) {
    check(metrics.tableScrolls, `table does not provide inner scroll at ${width}px`);
    check(metrics.stickyDelta < 2, `model column is not sticky at ${width}px`);
  }
  return metrics;
}

async function headerControlsCheck(page) {
  await page.goto(`${base}/?lang=en`, { waitUntil: "networkidle" });
  const category = page.locator('select[name="category"]');
  await category.selectOption({ index: 1 });
  await page.waitForURL("**category=**");
  check(await page.locator('[data-filter-control="category"]').evaluate((item) => item.classList.contains("is-active")), "category header is not active");

  const access = page.locator('select[name="access"]');
  await access.selectOption("api");
  await page.waitForURL("**access=api**");
  check(await page.locator('[data-filter-control="access"]').evaluate((item) => item.classList.contains("is-active")), "access header is not active");

  const unit = page.locator('select[name="price_unit"]');
  await unit.selectOption({ index: 1 });
  await page.waitForURL("**price_unit=**");
  const priceHeader = page.locator('[data-filter-control="price_unit"]');
  await priceHeader.click();
  await page.waitForURL("**sort=price_asc**");
  await priceHeader.click();
  await page.waitForURL("**sort=price_desc**");
  check(await page.locator('select[name="price_scope"]').inputValue() === "standard", "standard price scope is not the default");

  const benchmark = page.locator('select[name="benchmark"]');
  check(await benchmark.locator('option').count() > 1, "no published benchmark is available");
  await benchmark.selectOption({ index: 1 });
  await page.waitForURL("**benchmark=**");
  const benchmarkHeader = page.locator('[data-filter-control="benchmark"]');
  await benchmarkHeader.click();
  await page.waitForURL("**sort=check_best**");
  await benchmarkHeader.click();
  await page.waitForURL("**sort=check_worst**");

  const numberHeader = page.locator("thead .number-col a");
  await numberHeader.click();
  await page.waitForURL("**sort=number_asc**");
  await page.locator("thead .model-col a").click();
  await page.waitForURL("**sort=name_asc**");
}

async function loadAllRows(page) {
  await page.goto(`${base}/?lang=en`, { waitUntil: "networkidle" });
  const totalText = await page.locator(".pagination").first().innerText();
  const total = Number(totalText.match(/\/\s*(\d+)\s+entries/)?.[1]);
  check(Number.isInteger(total) && total > 25, "could not read catalogue total");
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const count = await page.locator("#model-rows .model-name").count();
    if (count >= total) break;
    const previous = count;
    await page.locator("#infinite-scroll").scrollIntoViewIfNeeded();
    await page.waitForFunction((oldCount) => document.querySelectorAll("#model-rows .model-name").length > oldCount, previous, { timeout: 10000 });
  }
  const links = await page.locator("#model-rows .model-name").evaluateAll((items) => items.map((item) => item.getAttribute("href")));
  check(links.length === total, `infinite scroll loaded ${links.length} of ${total}`);
  check(new Set(links).size === links.length, "infinite scroll produced duplicate model rows");
  return total;
}

async function retryCheck(page) {
  let failedOnce = false;
  await page.route("**/*partial=rows*", async (route) => {
    if (!failedOnce) {
      failedOnce = true;
      await route.fulfill({ status: 503, contentType: "text/plain", body: "temporary failure" });
      return;
    }
    await route.continue();
  });
  await page.goto(`${base}/?lang=en`, { waitUntil: "networkidle" });
  await page.locator("#infinite-scroll").scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "Retry" }).waitFor({ timeout: 10000 });
  await page.getByRole("button", { name: "Retry" }).click();
  await page.waitForFunction(() => document.querySelectorAll("#model-rows .model-name").length > 25, { timeout: 10000 });
  await page.unroute("**/*partial=rows*");
}

async function runEngine(name, browserType) {
  const executablePath = process.env[`AIPEDIA_${name.toUpperCase()}_EXECUTABLE`];
  const browser = await browserType.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const desktop = await browser.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  const page = await desktop.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const viewportMetrics = [];
  for (const [width, height] of [[320, 844], [360, 844], [390, 844], [430, 844], [768, 1024], [1024, 768], [1440, 1000], [1920, 1080], [844, 390]]) {
    viewportMetrics.push({ width, height, ...(await tableChecks(page, width, height)) });
  }
  await page.goto(`${base}/?lang=ru`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Тема" }).click();
  check(await page.locator("html").getAttribute("data-theme") === "dark", `${name}: theme did not change`);
  await page.getByRole("link", { name: "EN", exact: true }).click();
  await page.waitForURL("**/?lang=en");
  check(await page.locator("html").getAttribute("lang") === "en", `${name}: language did not change`);
  await page.selectOption('select[name="sort"]', "name_desc");
  await page.waitForURL("**sort=name_desc**");
  await page.screenshot({ path: path.join(output, `${name}-desktop-en-dark.png`), fullPage: true });

  await headerControlsCheck(page);

  await page.goto(`${base}/?lang=en&q=claude&sort=name_desc`, { waitUntil: "networkidle" });
  const card = page.locator(".model-name").first();
  const cardHref = await card.getAttribute("href");
  check(cardHref.includes("q=claude") && cardHref.includes("sort=name_desc"), `${name}: catalogue state missing from detail link`);
  await card.click();
  await page.locator("article.model-detail").waitFor();
  check(await page.locator(".record-number").count() === 1, `${name}: detail card has no permanent number`);
  const backHref = await page.locator(".back").getAttribute("href");
  check(backHref.includes("q=claude") && backHref.includes("sort=name_desc"), `${name}: catalogue state missing from back link`);
  await page.locator(".back").click();
  await page.waitForURL("**q=claude**sort=name_desc**");

  await page.goto(`${base}/?lang=en&page=2`, { waitUntil: "networkidle" });
  check(await page.locator('link[rel="canonical"]').getAttribute("href") === `${base}/?lang=en&page=2`, `${name}: page 2 canonical is wrong`);
  check(await page.locator('meta[name="robots"]').count() === 0, `${name}: ordinary page 2 is noindex`);
  await page.goto(`${base}/?lang=en&q=claude`, { waitUntil: "networkidle" });
  check(await page.locator('meta[name="robots"]').getAttribute("content") === "noindex,follow", `${name}: filtered page is indexable`);

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const mobilePage = await mobile.newPage();
  await mobilePage.addInitScript(() => localStorage.setItem("aipedia-theme", "light"));
  await mobilePage.goto(`${base}/?lang=ru`, { waitUntil: "networkidle" });
  await mobilePage.screenshot({ path: path.join(output, `${name}-mobile-ru-light.png`), fullPage: true });
  await mobilePage.getByRole("link", { name: "EN", exact: true }).click();
  await mobilePage.getByRole("button", { name: "Theme" }).click();
  await mobilePage.screenshot({ path: path.join(output, `${name}-mobile-en-dark.png`), fullPage: true });

  const noJs = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1280, height: 900 } });
  const noJsPage = await noJs.newPage();
  await noJsPage.goto(`${base}/?lang=en&page=2`, { waitUntil: "domcontentloaded" });
  check(await noJsPage.locator(".model-name").count() > 0, `${name}: server pagination unavailable without JavaScript`);
  await noJsPage.locator(".model-name").first().click();
  await noJsPage.locator("article.model-detail").waitFor();

  let allRows = null;
  let retry = null;
  if (name === "chromium") {
    allRows = await loadAllRows(page);
    await retryCheck(page);
  }
  check(errors.length === 0, `${name}: page errors: ${errors.join(" | ")}`);
  await noJs.close();
  await mobile.close();
  await desktop.close();
  await browser.close();
  return { name, viewportMetrics, allRows, retry: name === "chromium" ? "passed" : "not_run", pageErrors: errors };
}

const result = [];
const engines = [["chromium", chromium], ["firefox", firefox], ["webkit", webkit]];
for (const [name, browserType] of engines.filter(([engine]) => !process.env.AIPEDIA_QA_BROWSER || process.env.AIPEDIA_QA_BROWSER === engine)) {
  result.push(await runEngine(name, browserType));
}
fs.writeFileSync(path.join(output, "results.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify({ status: "PASS", output, browsers: result.map((item) => item.name), rows: result[0].allRows }));
