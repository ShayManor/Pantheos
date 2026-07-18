import { test, expect } from "./utils.js";

test("launching a propose-level ticket shows a PR-only toast", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "EVC-0074" }).click();
  await expect(page.getByText("auto-pr")).toHaveCount(0); // EVC is propose
  await page.getByRole("button", { name: "Launch Delphi" }).click();
  await expect(page.locator(".gs-toast")).toContainText("PR-only");
  await expect(page.getByText("Delphi is running…")).toBeVisible();
});

test("launching a full-autonomy ticket spawns a Claude Code session", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GHS-0308" }).click();
  await page.getByRole("button", { name: "Launch Delphi" }).click();
  await expect(page.locator(".gs-toast")).toContainText("Claude Code session");
});

test("backburner a queued ticket", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "STA-0044" }).click();
  await page.getByRole("button", { name: "Backburner" }).click();
  await expect(page.locator(".gs-toast")).toContainText("backburner");
});

test("propose ticket surfaces the PR-only guard", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "EVC-0074" }).click();
  await expect(page.getByText("Opens a pull request and stops for your review.")).toBeVisible();
});

test("delete a ticket removes it from the queue", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  // Cancel leaves the ticket intact.
  await page.getByRole("button", { name: "Delete ticket" }).click();
  await page.locator(".gs-overlay").getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByRole("heading", { name: "TMLR camera-ready revisions" })).toBeVisible();
  // Confirm deletes it and returns to the queue.
  await page.getByRole("button", { name: "Delete ticket" }).click();
  await page.locator(".gs-overlay").getByRole("button", { name: "Delete ticket" }).click();
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
  await expect(page.locator(".gs-toast")).toContainText("GRD-0182 deleted");
  await expect(page.locator(".gs-trow", { hasText: "GRD-0182" })).toHaveCount(0);
});

test("clicking a ticket source filters the queue by it", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await page.locator(".gs-linkable", { hasText: "manual" }).click();
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
  await expect(page.locator(".gs-chip-x")).toContainText("source: manual");
});
