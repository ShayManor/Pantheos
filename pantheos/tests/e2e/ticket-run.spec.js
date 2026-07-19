import { test, expect } from "./utils.js";

test("launching Delphi streams a run, completes, and persists", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await expect(page.getByRole("heading", { name: "TMLR camera-ready revisions" })).toBeVisible();

  await page.getByRole("button", { name: "Launch Delphi" }).click();

  // Activity strip appears with chain of thought + tool chips + output.
  await expect(page.getByText("DELPHI ACTIVITY", { exact: false })).toBeVisible();
  await expect(page.locator(".gs-toolchip").first()).toBeVisible();
  await expect(page.getByText("Run summary for GRD-0182", { exact: false })).toBeVisible();

  // Ticket lands in needs_review (RESULT box written).
  await expect(page.getByText("RESULT")).toBeVisible();

  // Full-run page shows the same transcript.
  await page.getByText("View full run").click();
  await expect(page).toHaveURL(/\/tickets\/GRD-0182\/delphi$/);
  await expect(page.getByText("Run summary for GRD-0182", { exact: false })).toBeVisible();

  // Back to the ticket, reload → transcript replays from persistence.
  await page.getByRole("button", { name: "Back to ticket" }).click();
  await page.reload();
  await expect(page.getByText("DELPHI ACTIVITY", { exact: false })).toBeVisible();
  await expect(page.getByText("Run summary for GRD-0182", { exact: false })).toBeVisible();
});

test("a failed launch request surfaces an error instead of doing nothing", async ({ page }) => {
  // Simulate the API being unreachable/erroring for the launch call.
  await page.route("**/api/tickets/*/launch", (route) =>
    route.fulfill({ status: 500, contentType: "text/plain", body: "boom" }));

  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await page.getByRole("button", { name: "Launch Delphi" }).click();

  // The user gets explicit feedback, not a silent no-op.
  await expect(page.getByText("Couldn't launch Delphi", { exact: false })).toBeVisible();
});

test("a run whose stream fails does not stay stuck at 'running…'", async ({ page }) => {
  // Launch succeeds, but the run stream connection fails.
  await page.route("**/api/tickets/*/run/stream", (route) =>
    route.fulfill({ status: 500, contentType: "text/plain", body: "boom" }));

  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  await page.getByRole("button", { name: "Launch Delphi" }).click();

  await expect(page.getByText("Delphi run failed")).toBeVisible();
  // The activity strip must not be frozen mid-run.
  await expect(page.getByText("DELPHI ACTIVITY · running", { exact: false })).toHaveCount(0);
});
