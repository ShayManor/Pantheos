import { test, expect, navTo } from "./utils.js";

test("delphi greets and replies to a suggestion with tool chips", async ({ page }) => {
  await navTo(page, "Delphi");
  await expect(page.getByRole("heading", { name: "Talk to Delphi" })).toBeVisible();
  await page.locator(".gs-sugg button", { hasText: "What's due this week?" }).click();
  await expect(page.locator(".gs-bub").filter({ hasText: "This week:" })).toBeVisible();
  await expect(page.locator(".gs-toolchip", { hasText: "Calendar" })).toBeVisible();
});

test("delphi free-text chat routes to the gh-stats answer", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByPlaceholder("Ask Delphi, attach a file, or dictate…").fill("did the gh-stats fix pass canary");
  await page.getByPlaceholder("Ask Delphi, attach a file, or dictate…").press("Enter");
  await expect(page.locator(".gs-bub").filter({ hasText: "5XX hit 6.1%" })).toBeVisible();
  await expect(page.locator(".gs-toolchip", { hasText: "GitHub" })).toBeVisible();
});

test("connectors: add, toggle and delete", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByRole("button", { name: "Connectors, skills & memory" }).click();
  await expect(page.locator(".gs-conn", { hasText: "GitHub" })).toBeVisible();

  await page.getByPlaceholder("Connector name").fill("TestConn");
  await page.getByPlaceholder("server URL").fill("t.local");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.locator(".gs-conn", { hasText: "TestConn" })).toBeVisible();
  await expect(page.locator(".gs-toast")).toContainText("Connected TestConn");

  const github = page.locator(".gs-conn", { hasText: "GitHub" });
  await expect(github.locator(".gs-switch")).toHaveClass(/on/);
  await github.locator(".gs-switch").click();
  await expect(github.locator(".gs-switch")).not.toHaveClass(/on/);

  await page.locator(".gs-conn", { hasText: "TestConn" }).locator(".gs-icon-btn").click();
  await expect(page.locator(".gs-conn", { hasText: "TestConn" })).toHaveCount(0);
});

test("skills and memory tabs render", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByRole("button", { name: "Connectors, skills & memory" }).click();
  await page.locator(".gs-toggle button", { hasText: "Skills" }).click();
  await expect(page.getByText("enrich-ticket")).toBeVisible();
  await page.locator(".gs-toggle button", { hasText: "Memory" }).click();
  await expect(page.getByText("LEARNED FACTS")).toBeVisible();
  await expect(page.getByText("Prefers terse, technically precise replies")).toBeVisible();
});

test("switching the agent model updates the selector", async ({ page }) => {
  await navTo(page, "Delphi");
  await expect(page.locator(".gs-model")).toContainText("Hermes 4 70B");
  await page.locator(".gs-model").click();
  await page.locator(".gs-menu-item", { hasText: "Claude Opus 4.8" }).click();
  await expect(page.locator(".gs-model")).toContainText("Claude Opus 4.8");
  await expect(page.locator(".gs-toast")).toContainText("Switched to Claude Opus 4.8");
});
