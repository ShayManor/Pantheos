import { test, expect } from "./utils.js";

test("ticket github links are real external anchors", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "GRD-0182" }).click();
  const link = page.locator("a.gs-link", { hasText: "ideas-lab/guardrail #182" });
  await expect(link).toHaveAttribute("href", "https://github.com/ideas-lab/guardrail/issues/182");
  await expect(link).toHaveAttribute("target", "_blank");
});

test("a targetless ticket link stays a non-navigating element", async ({ page }) => {
  await page.locator(".gs-trow", { hasText: "STA-0044" }).click();
  // brightspace/file links have no live URL → rendered as a div, not an anchor
  await expect(page.locator("div.gs-link", { hasText: "ps4.pdf" })).toBeVisible();
  await expect(page.locator("a.gs-link", { hasText: "ps4.pdf" })).toHaveCount(0);
});

test("downloading container logs saves a real file", async ({ page }) => {
  await page.locator(".gs-nav-item", { hasText: "Monitor" }).click();
  await page.locator(".gs-pcard", { hasText: "GitHub README widgets" }).click();
  await page.locator(".gs-svc", { hasText: "ghstats-edge" }).click();
  await page.getByRole("button", { name: "View logs" }).click();
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download" }).click(),
  ]);
  expect(download.suggestedFilename()).toBe("ghstats-edge.log");
});
