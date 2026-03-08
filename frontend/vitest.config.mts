import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './') },
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        // Build / tooling — no executable logic
        '**/*.config.{mjs,mts,ts,js}',
        'vitest.setup.ts',
        '__tests__/**',
        // TypeScript interfaces only — no JS output
        'lib/types.ts',
        // Pure fetch wrapper — mocked in every test
        'lib/api.ts',
        // Next.js boilerplate
        'app/layout.tsx',
        // Root landing page — out of scope for this PR
        'app/page.tsx',
        // WebGL/D3 graph — requires Playwright E2E, not testable in happy-dom
        'components/Neo4jGraph.tsx',
      ],
      thresholds: { lines: 80, functions: 80, branches: 75 },
    },
  },
})
