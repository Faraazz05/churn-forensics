/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_KEY_ADMIN: string
  readonly VITE_API_KEY_READONLY: string
  readonly VITE_WATCHLIST_THRESHOLD: string
  readonly VITE_APP_NAME: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
