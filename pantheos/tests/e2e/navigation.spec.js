import { test, expect, navTo } from "./utils.js";

test("navigate between all stations", async ({ page }) => {
  await navTo(page, "Projects");
  await expect(page.getByRole("heading", { name: "Projects" })).toBeVisible();
  await navTo(page, "Monitor");
  await expect(page.getByRole("heading", { name: "Monitor" })).toBeVisible();
  await navTo(page, "Delphi");
  await expect(page.getByRole("heading", { name: "Talk to Delphi" })).toBeVisible();
  await navTo(page, "Queue");
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
});

test("breadcrumb returns from a ticket to the queue", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await expect(page.getByRole("heading", { name: "TMLR camera-ready revisions" })).toBeVisible();
  await page.locator(".gs-crumb button", { hasText: "Queue" }).click();
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
});

test("command palette searches and navigates", async ({ page }) => {
  await page.locator(".gs-kbtn").click();
  await expect(page.locator(".gs-pal")).toBeVisible();
  await page.locator(".gs-pal-in input").fill("merlin");
  await expect(page.locator(".gs-pal-item").first()).toContainText("MERLIN");
  await page.locator(".gs-pal-in input").press("Enter");
  await expect(page.getByRole("heading", { name: "MERLIN" })).toBeVisible();
});

test("cmd+k opens the palette and escape closes it", async ({ page }) => {
  await page.keyboard.press("ControlOrMeta+k");
  await expect(page.locator(".gs-pal")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".gs-pal")).toHaveCount(0);
});
