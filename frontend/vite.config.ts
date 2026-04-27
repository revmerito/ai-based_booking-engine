import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        secure: false,
      },
      "/static": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    sourcemap: false,
    target: "esnext",
    cssCodeSplit: true,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("recharts") || id.includes("d3-")) {
            return "chunk-charts";
          }
          if (id.includes("framer-motion")) {
            return "chunk-framer";
          }
          if (id.includes("@supabase")) {
            return "chunk-supabase";
          }
          if (id.includes("@radix-ui")) {
            return "chunk-radix";
          }
          if (id.includes("react-dom") || id.includes("react-router")) {
            return "chunk-react";
          }
          if (id.includes("jspdf")) {
            return "chunk-pdf";
          }
          if (id.includes("node_modules")) {
            return "chunk-vendor";
          }
        },
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
