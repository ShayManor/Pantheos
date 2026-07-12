import { test, expect } from "./utils.js";

test("create a ticket via the modal", async ({ page }) => {
  await expect(page.locator(".gs-trow")).toHaveCount(9);
  await page.getByRole("button", { name: "New ticket" }).click();
  await expect(page.getByPlaceholder("What needs doing?")).toBeVisible();

  await page.getByPlaceholder("What needs doing?").fill("Wire up OAuth");
  await page.locator(".gs-pal select").first().selectOption("project:ghstats");
  await page.locator(".gs-pal select").nth(1).selectOption("1"); // P1
  await page.locator(".gs-pal select").nth(2).selectOption("72"); // in 3 days
  await page.getByRole("button", { name: "Create ticket" }).click();

  // navigates to the new ticket's detail
  await expect(page.getByRole("heading", { name: "Wire up OAuth" })).toBeVisible();
  await expect(page.locator(".gs-toast")).toContainText("Created");
  await expect(page.getByText("in 3d")).toBeVisible(); // derived due label

  // back to the queue — now 10 tickets, the new one present
  await page.locator(".gs-nav-item", { hasText: "Queue" }).click();
  await expect(page.locator(".gs-trow")).toHaveCount(10);
  await expect(page.locator(".gs-trow", { hasText: "Wire up OAuth" })).toBeVisible();
});

test("the new-ticket create button is disabled until a title is entered", async ({ page }) => {
  await page.getByRole("button", { name: "New ticket" }).click();
  await expect(page.getByRole("button", { name: "Create ticket" })).toBeDisabled();
  await page.getByPlaceholder("What needs doing?").fill("x");
  await expect(page.getByRole("button", { name: "Create ticket" })).toBeEnabled();
});
