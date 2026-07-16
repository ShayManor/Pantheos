import { test, expect, navTo } from "./utils.js";

test("projects are grouped by area", async ({ page }) => {
  await navTo(page, "Projects");
  await expect(page.getByText("IDEAS LAB").first()).toBeVisible();
  await expect(page.locator(".gs-pcard", { hasText: "MERLIN" })).toBeVisible();
  await expect(page.locator(".gs-pcard", { hasText: "GPUFindr" })).toBeVisible();
});

test("project detail renders usage chart, containers and tickets", async ({ page }) => {
  await navTo(page, "Projects");
  await page.locator(".gs-pcard", { hasText: "GitHub README widgets" }).click();
  await expect(page.getByRole("heading", { name: "gh-stats" })).toBeVisible();
  await expect(page.getByText("DAILY ACTIVE · LAST 14 DAYS")).toBeVisible();
  await expect(page.locator(".recharts-surface").first()).toBeVisible();
  await expect(page.locator(".gs-svc", { hasText: "ghstats-edge" })).toBeVisible();
  await expect(page.locator(".gs-trow", { hasText: "GHS-0311" })).toBeVisible();
});
