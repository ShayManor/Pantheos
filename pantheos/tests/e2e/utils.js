import { test as base, expect } from "@playwright/test";

// Every test starts from a freshly reseeded DB on the queue view, so tests are
// order-independent and deterministic.
export const test = base.extend({
  page: async ({ page, request }, use) => {
    // Reseed (drop + recreate + seed) with a few retries: it can transiently
    // race a just-closed page's in-flight request for a table lock. Retrying
    // yields a clean DB — this hardens only the test setup, never the app code.
    let ok = false;
    for (let i = 0; i < 6 && !ok; i++) {
      const res = await request.post("/api/admin/reseed");
      ok = res.ok();
      if (!ok) await new Promise((r) => setTimeout(r, 250));
    }
    expect(ok, "reseed should succeed within retries").toBeTruthy();
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
    await use(page);
  },
});

export { expect };

// Sidebar station navigation (unambiguous: only nav items carry .gs-nav-item).
export const navTo = (page, label) => page.locator(".gs-nav-item", { hasText: label }).click();
