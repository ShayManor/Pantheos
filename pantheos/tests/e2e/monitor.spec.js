import { test, expect, navTo } from "./utils.js";

test("monitor overview and compute toggle", async ({ page }) => {
  await navTo(page, "Monitor");
  await expect(page.getByText("FAULTS").first()).toBeVisible();
  await expect(page.locator(".gs-pcard", { hasText: "gh-stats" })).toBeVisible();
  await page.locator(".gs-toggle button", { hasText: "Compute" }).click();
  await expect(page.locator(".gs-pcard", { hasText: "minipc" })).toBeVisible();
  await expect(page.locator(".gs-pcard", { hasText: "Jetson Orin Nano" })).toBeVisible();
});

test("project monitor detail shows the 5xx breach chart", async ({ page }) => {
  await navTo(page, "Monitor");
  await page.locator(".gs-pcard", { hasText: "GitHub README widgets" }).click();
  await expect(page.locator(".gs-ref", { hasText: "GHS-0311" })).toBeVisible();
  await expect(page.locator(".recharts-surface").first()).toBeVisible();
});

test("container detail shows metric tiles and cpu chart", async ({ page }) => {
  await navTo(page, "Monitor");
  await page.locator(".gs-pcard", { hasText: "GitHub README widgets" }).click();
  await page.locator(".gs-svc", { hasText: "ghstats-edge" }).click();
  await expect(page.getByRole("heading", { name: "ghstats-edge" })).toBeVisible();
  await expect(page.getByText("CPU · LAST 20 MIN")).toBeVisible();
  await expect(page.locator(".recharts-surface").first()).toBeVisible();
});

test("container logs render and filter by level (dropdown)", async ({ page }) => {
  await navTo(page, "Monitor");
  await page.locator(".gs-pcard", { hasText: "MERLIN" }).click();
  await page.locator(".gs-svc", { hasText: "merlin-planner" }).click();
  await page.getByRole("button", { name: "View logs" }).click();
  await expect(page.getByRole("heading", { name: "Logs" })).toBeVisible();
  await expect(page.locator(".gs-logline").first()).toBeVisible();
  await page.locator(".gs-model", { hasText: "Level" }).click();
  await page.locator(".gs-menu-item", { hasText: "Errors" }).click();
  await expect(page.locator(".gs-logline .lv.err").first()).toBeVisible();
  await expect(page.locator(".gs-logline .lv.info")).toHaveCount(0);
});

test("host detail lists that host's containers", async ({ page }) => {
  await navTo(page, "Monitor");
  await page.locator(".gs-toggle button", { hasText: "Compute" }).click();
  await page.locator(".gs-pcard", { hasText: "minipc" }).click();
  await expect(page.getByRole("heading", { name: "minipc" })).toBeVisible();
  await expect(page.locator(".gs-svc", { hasText: "pantheos-app-1" })).toBeVisible();
});

test("smart view collapses info runs and expands gaps", async ({ page }) => {
  await navTo(page, "Monitor");
  await page.locator(".gs-pcard", { hasText: "GitHub README widgets" }).click();
  await page.locator(".gs-svc", { hasText: "ghstats-edge" }).click();
  await page.getByRole("button", { name: "View logs" }).click();
  await expect(page.getByRole("heading", { name: "Logs" })).toBeVisible();
  // Smart (default): a collapsed info run and a surfaced error
  const gap = page.locator(".gs-loggap", { hasText: "info lines" }).first();
  await expect(gap).toBeVisible();
  await expect(page.locator(".gs-logline .lv.err").first()).toBeVisible();
  const before = await page.locator(".gs-logline").count();
  // Expand the gap → more lines appear
  await gap.click();
  await expect.poll(() => page.locator(".gs-logline").count()).toBeGreaterThan(before);
  // Raw view shows an uncollapsed stream (no gaps)
  await page.locator(".gs-model", { hasText: "View" }).click();
  await page.locator(".gs-menu-item", { hasText: "Raw" }).click();
  await expect(page.locator(".gs-loggap", { hasText: "info lines" })).toHaveCount(0);
});
