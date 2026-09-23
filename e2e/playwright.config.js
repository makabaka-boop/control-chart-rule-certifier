import { defineConfig } from '@playwright/test'

// Exactly one browser main-flow verification exists in this project.
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
  },
  webServer: [
    {
      command: 'python3 -m uvicorn api.main:app --port 8000',
      port: 8000,
      cwd: '..',
      reuseExistingServer: true,
    },
    {
      command: 'npm run dev',
      port: 5173,
      cwd: '../web',
      reuseExistingServer: true,
    },
  ],
})
