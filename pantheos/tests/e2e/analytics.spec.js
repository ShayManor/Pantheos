import { test, expect, navTo } from "./utils.js";

test("analytics shows gh-stats history, embeds and a user's timeline", async ({ page }) => {
  await navTo(page, "Analytics");
  await expect(page.getByRole("heading", { name: "gh-stats analytics" })).toBeVisible();
  await expect(page.locator(".gs-an-tile", { hasText: "Live embeds" }).locator(".v")).toHaveText("20");
  await expect(page.getByText("HISTORY · PER DAY")).toBeVisible();
  await expect(page.getByText("EMBEDS STARTED VS STOPPED · PER WEEK")).toBeVisible();

  await page.locator(".gs-filter", { hasText: "Stopped" }).click();
  const rows = page.locator(".gs-an-row:not(.head)");
  await expect(rows).toHaveCount(6);
  await expect(rows.first().locator(".pill.flt")).toHaveText(/^Stopped · [A-Z][a-z]{2} \d+$/);
  await rows.first().click();
  await expect(page.getByText(/EMBED LOADS PER DAY/)).toBeVisible();

  await page.locator(".gs-filter", { hasText: "Never embedded" }).click();
  await expect(rows).toHaveCount(4);
  await rows.first().click();
  await expect(page.getByText(/never pulled this user's widget/)).toBeVisible();

  await page.locator(".gs-an-search input").fill("octocat");
  await page.locator(".gs-filter", { hasText: "All" }).click();
  await expect(rows).toHaveCount(1);
});

test("analytics user table sorts by a clicked column, ascending then descending", async ({ page }) => {
  await navTo(page, "Analytics");
  const head = page.locator(".gs-an-row.head .sort", { hasText: "Loads" });
  const loads = async () => (await page.locator(".gs-an-row:not(.head) > :nth-child(5)").allTextContents())
    .map((t) => Number(t.replace(/,/g, "")));
  await head.click();
  await expect(head).toHaveText("Loads ↑");
  let v = await loads();
  expect(v.length).toBeGreaterThan(1);
  expect(v).toEqual([...v].sort((a, b) => a - b));
  await head.click();
  await expect(head).toHaveText("Loads ↓");
  v = await loads();
  expect(v).toEqual([...v].sort((a, b) => b - a));
  expect(v[0]).toBeGreaterThan(v[v.length - 1]);

  await page.locator(".gs-toggle button", { hasText: "GPUFindr" }).click();
  const visits = page.locator(".gs-an-row.head .sort", { hasText: "Visits" });
  await visits.click();
  await expect(visits).toHaveText("Visits ↑");
});

test("analytics GPUFindr shows searches and visitors", async ({ page }) => {
  await navTo(page, "Analytics");
  await page.locator(".gs-toggle button", { hasText: "GPUFindr" }).click();
  await expect(page.getByRole("heading", { name: "GPUFindr analytics" })).toBeVisible();
  await expect(page.getByText("MOST SEARCHED GPUS")).toBeVisible();
  await expect(page.locator(".gs-an-tile", { hasText: "Visitors" })).toBeVisible();
  await page.locator(".gs-toggle button", { hasText: "7D" }).click();
  await expect(page.locator(".gs-an-dim", { hasText: "→" })).toHaveText("Nov 4 → Nov 10");
});
