import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "url";
import path from "path";

const dir = path.dirname(fileURLToPath(import.meta.url)); // the pantheos/ frontend dir
const apiDir = path.join(dir, "..", "pantheos-api");

// Non-flaky by construction: serial, no retries (a flake must fail, not be masked),
// each test reseeds the DB for isolation. Run 20× via scripts/e2e-loop.sh.
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["line"]],
  timeout: 30000,
  expect: { timeout: 10000 },
  use: {
    baseURL: "http://localhost:5173",
    trace: "off",
    ...devices["Desktop Chrome"],
  },
  webServer: [
    {
      command: "venv/bin/python wsgi.py",
      cwd: apiDir,
      env: { PANTHEOS_ALLOW_RESEED: "1" },
      url: "http://localhost:8000/api/health",
      reuseExistingServer: true,
      timeout: 30000,
    },
    {
      command: "npm run dev",
      cwd: dir,
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
});
