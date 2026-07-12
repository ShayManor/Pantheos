import { test, expect } from "./utils.js";

test("edit and save a project's context, and it persists", async ({ page }) => {
  await page.locator(".gs-nav-item", { hasText: "Projects" }).click();
  await page.locator(".gs-pcard", { hasText: "GitHub profile analytics" }).click();
  await page.getByRole("button", { name: "Context" }).click();

  const box = page.locator("textarea");
  await expect(box).toHaveValue(/gh-stats/);          // seeded starter content loads
  await box.fill("# gh-stats\n\nAlways run the linter before pushing.");
  await page.getByRole("button", { name: "Save context" }).click();
  await expect(page.locator(".gs-toast")).toContainText("Saved context");

  // reopen → the edit persisted
  await page.getByRole("button", { name: "Context" }).click();
  await expect(page.locator("textarea")).toHaveValue("# gh-stats\n\nAlways run the linter before pushing.");
});

test("edit an area's context from the projects list", async ({ page }) => {
  await page.locator(".gs-nav-item", { hasText: "Projects" }).click();
  await page.locator('button[title="Edit area context"]').first().click();
  await expect(page.getByText("IDEAS LAB · context")).toBeVisible();
  await expect(page.locator("textarea")).toHaveValue(/IDEAS LAB/);
  await page.locator("textarea").fill("Shared lab rules.");
  await page.getByRole("button", { name: "Save context" }).click();
  await expect(page.locator(".gs-toast")).toContainText("Saved context for IDEAS LAB");
});
