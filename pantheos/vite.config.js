import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Pin to IPv4 throughout: Flask binds 127.0.0.1, so the proxy target and the
// dev-server host must too — otherwise `localhost`→`::1` races cause ECONNREFUSED.
const api = { "/api": "http://127.0.0.1:8000" };

export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, proxy: api },
  preview: { host: "127.0.0.1", port: 5173, proxy: api },
});
