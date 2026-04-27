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
    // Reduce chunk size warnings threshold
    chunkSizeWarningLimit: 500,
    minify: "esbuild",
    rollupOptions: {
      output: {
        // --- MANUAL CHUNK SPLITTING ---
        // Separates vendor libs so browsers can cache them independently.
        // This is the single biggest win for repeat visits.
        manualChunks(id) {
          // Charting library (heavy, rarely changes)
          if (id.includes("recharts") || id.includes("d3-")) {
            return "chunk-charts";
          }
          // Animation library
          if (id.includes("framer-motion")) {
            return "chunk-framer";
          }
          // Supabase (auth/db client - stable)
          if (id.includes("@supabase")) {
            return "chunk-supabase";
          }
          // All Radix UI primitives together
          if (id.includes("@radix-ui")) {
            return "chunk-radix";
          }
          // React core
          if (id.includes("react-dom") || id.includes("react-router")) {
            return "chunk-react";
          }
          // PDF export (only needed on demand, but bundle separately)
          if (id.includes("jspdf")) {
            return "chunk-pdf";
          }
          // Everything else in node_modules → vendor chunk
          if (id.includes("node_modules")) {
            return "chunk-vendor";
          }
        },
      },
    },
    // Strip console.log in production
    ...(mode === "production" && {
      esbuildOptions: {
        drop: ["console", "debugger"],
      },
    }),
  },
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
