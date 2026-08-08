import { expect, test } from "@playwright/test";

// The gate is off for the rest of the suite, so stub the config endpoint to
// prove the frontend closes when it is on. No Firebase network call is needed:
// with no persisted user, onAuthStateChanged resolves to signed-out locally.
test("the gate hides the app until sign-in", async ({ page }) => {
  await page.route("**/api/auth/config", (route) =>
    route.fulfill({
      json: {
        enabled: true,
        projectId: "pantheos-8d962",
        apiKey: "test-api-key",
        authDomain: "pantheos-8d962.firebaseapp.com",
      },
    }));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Authentication required" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in with Google" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Queue" })).toHaveCount(0);
});
