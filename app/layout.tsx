import type { Metadata } from "next"
import type React from "react"

export const metadata: Metadata = {
  title: "Vithel Dash Redactor — сервер аккаунтов",
  description: "Сервер аккаунтов для игры Vithel Dash Redactor Beta 1.6",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" style={{ background: "#1a1a24" }}>
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", color: "#e8e8f0" }}>{children}</body>
    </html>
  )
}
