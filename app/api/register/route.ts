import { neon } from "@neondatabase/serverless"
import { scryptSync, randomBytes } from "crypto"

function hashPassword(password: string): string {
  const salt = randomBytes(16).toString("hex")
  const hash = scryptSync(password, salt, 64).toString("hex")
  return `${salt}:${hash}`
}

export async function POST(req: Request) {
  try {
    const sql = neon(process.env.DATABASE_URL!)
    const body = await req.json()
    const username = String(body.username ?? "").trim()
    const password = String(body.password ?? "")

    if (username.length < 3 || username.length > 20) {
      return Response.json({ error: "Имя должно быть от 3 до 20 символов" }, { status: 400 })
    }
    if (!/^[a-zA-Z0-9_а-яА-ЯёЁ-]+$/.test(username)) {
      return Response.json({ error: "Имя содержит недопустимые символы" }, { status: 400 })
    }
    if (password.length < 6) {
      return Response.json({ error: "Пароль минимум 6 символов" }, { status: 400 })
    }

    const existing = await sql`SELECT id FROM game_accounts WHERE lower(username) = lower(${username})`
    if (existing.length > 0) {
      return Response.json({ error: "Это имя уже занято" }, { status: 409 })
    }

    const token = randomBytes(32).toString("hex")
    const passwordHash = hashPassword(password)
    await sql`INSERT INTO game_accounts (username, password_hash, token) VALUES (${username}, ${passwordHash}, ${token})`

    return Response.json({ username, token })
  } catch {
    return Response.json({ error: "Ошибка сервера" }, { status: 500 })
  }
}
