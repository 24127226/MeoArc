/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL của backend thật. Bỏ trống = chạy mock (xem src/lib/api.ts). */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
