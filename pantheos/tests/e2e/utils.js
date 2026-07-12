import { test as base, expect } from "@playwright/test";

// Every test starts from a freshly reseeded DB on the queue view, so tests are
// order-independent and deterministic.
export const test = base.extend({
  page: async ({ page, request }, use) => {
    const res = await request.post("/api/admin/reseed");
    expect(res.ok()).toBeTruthy();
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
    await use(page);
  },
});

export { expect };

// Sidebar station navigation (unambiguous: only nav items carry .gs-nav-item).
export const navTo = (page, label) => page.locator(".gs-nav-item", { hasText: label }).click();
