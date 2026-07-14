import { test, expect, navTo } from "./utils.js";

test("delphi streams a markdown answer with chain-of-thought and tools", async ({ page }) => {
  await navTo(page, "Delphi");
  await expect(page.getByText("Talk to Delphi")).toBeVisible();

  await page.getByPlaceholder(/Ask Delphi/).fill("What is due this week?");
  await page.getByPlaceholder(/Ask Delphi/).press("Enter");

  // Streamed answer renders as markdown (bold + code + KaTeX).
  const bubble = page.locator(".gs-msg.flight .gs-md").last();
  await expect(bubble.locator("strong")).toContainText("Priority math");
  await expect(bubble.locator("code").first()).toBeVisible();
  await expect(bubble.locator(".katex").first()).toBeVisible();

  // Chain-of-thought panel expands on click.
  const cot = page.locator(".gs-cot").last();
  await expect(cot.locator(".gs-cot-head")).toContainText("Thought process");
  await cot.locator(".gs-cot-head").click();
  await expect(cot.locator(".gs-cot-body")).toContainText("highest-leverage");

  // Tool chips surfaced.
  await expect(page.locator(".gs-toolchip", { hasText: "Calendar" })).toBeVisible();

  // Ticket ref inside markdown is clickable.
  await expect(bubble.locator(".gs-ref", { hasText: "GRD-0182" })).toBeVisible();
});

test("delphi history persists across reload", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByPlaceholder(/Ask Delphi/).fill("Status of MERLIN");
  await page.getByPlaceholder(/Ask Delphi/).press("Enter");
  await expect(page.locator(".gs-msg.flight .gs-md").last()).toContainText("MERLIN");

  await page.reload();
  await navTo(page, "Delphi");
  await page.getByTitle("Chat history").click();
  await expect(page.locator(".gs-sess")).toContainText(["Status of MERLIN"]);
});

test("connectors: add, toggle and delete", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByRole("button", { name: "Connectors, skills & memory" }).click();
  // The real, seeded connector — Pantheos itself (the MCP server).
  await expect(page.locator(".gs-conn", { hasText: "Pantheos" })).toBeVisible();

  await page.getByPlaceholder("Connector name").fill("TestConn");
  await page.getByPlaceholder("server URL").fill("t.local");
  await page.getByRole("button", { name: "Add" }).click();
  await expect(page.locator(".gs-conn", { hasText: "TestConn" })).toBeVisible();
  await expect(page.locator(".gs-toast")).toContainText("Connected TestConn");

  const pantheos = page.locator(".gs-conn", { hasText: "Pantheos" });
  await expect(pantheos.locator(".gs-switch")).toHaveClass(/on/);
  await pantheos.locator(".gs-switch").click();
  await expect(pantheos.locator(".gs-switch")).not.toHaveClass(/on/);

  const testConn = page.locator(".gs-conn", { hasText: "TestConn" });
  await expect(testConn).toHaveCount(1);
  await testConn.getByTitle("Delete connector").click();
  await expect(testConn).toHaveCount(0);
});

test("skills and memory tabs render", async ({ page }) => {
  await navTo(page, "Delphi");
  await page.getByRole("button", { name: "Connectors, skills & memory" }).click();
  await page.locator(".gs-toggle button", { hasText: "Skills" }).click();
  await expect(page.getByText("debug-issue")).toBeVisible();
  await expect(page.getByText("fix-project")).toBeVisible();
  await expect(page.getByText("triage-ticket")).toBeVisible();
  await page.locator(".gs-toggle button", { hasText: "Memory" }).click();
  await expect(page.getByText("LEARNED FACTS")).toBeVisible();
  await expect(page.getByText("Prefers terse, technically precise replies")).toBeVisible();
});

test("switching the agent model updates the selector", async ({ page }) => {
  await navTo(page, "Delphi");
  await expect(page.locator(".gs-model")).toContainText("GPT Terra");
  await page.locator(".gs-model").click();
  await page.locator(".gs-menu-item", { hasText: "GPT Luna" }).click();
  await expect(page.locator(".gs-model")).toContainText("GPT Luna");
  await expect(page.locator(".gs-toast")).toContainText("Switched to GPT Luna");
});
