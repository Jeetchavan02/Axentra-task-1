import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  // Fixed port, because the backend's CORS settings allow exactly this origin.
  server: { port: 5173, strictPort: true },
});
