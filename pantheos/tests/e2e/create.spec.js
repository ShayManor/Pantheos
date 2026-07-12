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

test("Delphi drafts the ticket live, then the user edits and creates", async ({ page }) => {
  await page.getByRole("button", { name: "New ticket" }).click();
  await page.getByPlaceholder("What needs doing?").fill("port to rubik pi");

  await page.getByRole("button", { name: "Call Delphi" }).click();

  // Delphi overwrites the form with a full draft (fields fill live)
  await expect(page.getByPlaceholder("What needs doing?")).toHaveValue("Port MERLIN inference to Rubik Pi");
  await expect(page.locator(".gs-pal select").first()).toHaveValue("project:merlin");
  await expect(page.locator(".gs-pal select").nth(2)).toHaveValue("168"); // deadline: this week
  await expect(page.getByPlaceholder("One line — what this ticket is")).not.toHaveValue("");

  // the user tweaks the draft, then creates
  await page.getByPlaceholder("What needs doing?").fill("Port MERLIN inference to Rubik Pi 5");
  await page.getByRole("button", { name: "Create ticket" }).click();

  await expect(page.getByRole("heading", { name: "Port MERLIN inference to Rubik Pi 5" })).toBeVisible();
  await expect(page.locator(".gs-toast")).toContainText("Created");
});

test("the new-ticket create button is disabled until a title is entered", async ({ page }) => {
  await page.getByRole("button", { name: "New ticket" }).click();
  await expect(page.getByRole("button", { name: "Create ticket" })).toBeDisabled();
  await page.getByPlaceholder("What needs doing?").fill("x");
  await expect(page.getByRole("button", { name: "Create ticket" })).toBeEnabled();
});
