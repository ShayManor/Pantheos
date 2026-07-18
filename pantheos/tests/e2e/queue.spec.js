import { test, expect, navTo } from "./utils.js";

test("queue lists all tickets, score-ranked", async ({ page }) => {
  await expect(page.locator(".gs-trow")).toHaveCount(9);
  await expect(page.locator(".gs-trow", { hasText: "GHS-0311" })).toBeVisible();
  await expect(page.getByText("500-rate breach on api container")).toBeVisible();
  // top of the list is a P0 (GHS-0311 now / GRD-0182)
  await expect(page.locator(".gs-trow").first().locator(".pri")).toHaveText("P0");
});

test("archived tickets leave the queue and live under the Archived horizon", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "STA-0044" }).click();
  await page.getByRole("button", { name: "Done" }).click();
  await expect(page.locator(".gs-toast")).toContainText("archived");
  await navTo(page, "Queue");
  await expect(page.locator(".gs-trow", { hasText: "STA-0044" })).toHaveCount(0);
  await page.locator(".gs-filter", { hasText: "Archived" }).click();
  await expect(page.locator(".gs-trow", { hasText: "STA-0044" })).toBeVisible();
});

test("Someday horizon shows only backburner tickets", async ({ page }) => {
  await page.locator(".gs-filter", { hasText: "Someday" }).click();
  await expect(page.locator(".gs-trow", { hasText: "MER-0088" })).toBeVisible();
  await expect(page.locator(".gs-trow", { hasText: "GRD-0182" })).toHaveCount(0);
});

test("search box filters the queue", async ({ page }) => {
  await page.getByPlaceholder("Filter tickets…").fill("motor");
  await expect(page.locator(".gs-trow")).toHaveCount(1);
  await expect(page.locator(".gs-trow", { hasText: "EVC-0074" })).toBeVisible();
});

test("sort by priority keeps a P0 on top", async ({ page }) => {
  await page.locator(".gs-sort").selectOption("priority");
  await expect(page.locator(".gs-trow").first().locator(".pri")).toHaveText("P0");
});

test("opening a ticket shows its detail", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await expect(page.getByRole("heading", { name: "TMLR camera-ready revisions" })).toBeVisible();
  await expect(page.getByText("Launch Delphi")).toBeVisible();
  await expect(page.getByText("Ablation confirms the teacher gate")).toBeVisible();
});
