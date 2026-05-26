/**
 * Headless check: initIndexPage fills birth selects and history links work.
 * Run: node scripts/verify_birth_form.mjs
 */
import fs from "fs";
import path from "path";
import vm from "vm";
import { fileURLToPath } from "url";
import { JSDOM } from "jsdom";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");

const indexHtml = fs.readFileSync(path.join(root, "templates/index.html"), "utf8");
const appJs = fs.readFileSync(path.join(root, "static/js/app.js"), "utf8");

const formMatch = indexHtml.match(/<form id="chart-form"[\s\S]*?<\/form>/);
if (!formMatch) {
  console.error("FAIL: chart-form not found in index.html");
  process.exit(1);
}

const dom = new JSDOM(
  `<!DOCTYPE html><html><body>
    ${formMatch[0]}
    <div class="card hidden" id="history-card"><ul id="history-list"></ul></div>
  </body></html>`,
  { url: "http://localhost/", runScripts: "dangerously" }
);

const ctx = dom.getInternalVMContext();
const { localStorage } = dom.window;

try {
  vm.runInContext(appJs, ctx, { filename: "app.js" });
} catch (e) {
  console.error("FAIL: app.js threw on load:", e.message);
  process.exit(1);
}

const { Wenyuan, document } = dom.window;
if (!Wenyuan?.initIndexPage) {
  console.error("FAIL: Wenyuan.initIndexPage missing");
  process.exit(1);
}

Wenyuan.initIndexPage();

const form = document.getElementById("chart-form");
const checks = [
  ["birth_year", 111],
  ["birth_month", 12],
  ["birth_day", 28],
  ["birth_hour", 24],
  ["birth_minute", 60],
];

let failed = false;
for (const [name, minOpts] of checks) {
  const el = form.elements.namedItem(name);
  const n = el?.options?.length ?? 0;
  if (!el || n < minOpts) {
    console.error(`FAIL: ${name} options=${n} (expected >= ${minOpts})`);
    failed = true;
  } else {
    console.log(`OK: ${name} options=${n} value=${el.value}`);
  }
}

const hour = form.elements.namedItem("birth_hour");
const minute = form.elements.namedItem("birth_minute");
hour.value = "7";
minute.value = "23";
const h = String(hour.value).padStart(2, "0");
const mi = String(minute.value).padStart(2, "0");
if (`${h}:${mi}` !== "07:23") {
  console.error(`FAIL: birth_time=${h}:${mi} expected 07:23`);
  failed = true;
} else {
  console.log("OK: birth_time=07:23");
}

localStorage.setItem(
  "wenyuan_history",
  JSON.stringify([
  {
    input: {
      date_type: "solar",
      birth_date: "1990-01-01",
      birth_time: "12:00",
      gender: "male",
    },
    label: "test",
    ts: Date.now(),
  },
  ])
);
Wenyuan.initIndexPage();
const href = document.querySelector("#history-list a.history-link")?.href || "";
if (!href.includes("/chart?s=")) {
  console.error("FAIL: history link:", href || "(empty)");
  failed = true;
} else {
  console.log("OK: history link generated");
}

if (failed) process.exit(1);
console.log("\nAll birth form checks passed.");
