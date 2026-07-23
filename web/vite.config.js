import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 개발 중 /api 요청을 FastAPI(8000)로 프록시.
// 빌드 결과(dist)는 FastAPI가 직접 서빙하므로 프로덕션에선 프록시 불필요.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
