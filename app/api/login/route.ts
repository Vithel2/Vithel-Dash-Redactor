import { neon } from "@neondatabase/serverless"
import { scryptSync, randomBytes, timingSafeEqual } from "crypto"

const sql = neon(process.env.DATABASE_URL!)

function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(":")
  if (!salt || !hash) return false
  const candidate = scryptSync(password, salt, 64)
  const expected = Buffer.from(hash, "hex")
  return candidate.length === expected.length && timingSafeEqual(candidate, expected)
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const username = String(body.username ?? "").trim()
    const password = String(body.password ?? "")

    const rows = await sql`SELECT id, username, password_hash FROM game_accounts WHERE lower(username) = lower(${username})`
    if (rows.length === 0 || !verifyPassword(password, rows[0].password_hash)) {
      return Response.json({ error: "Неверное имя или пароль" }, { status: 401 })
    }

    const token = randomBytes(32).toString("hex")
    await sql`UPDATE game_accounts SET token = ${token} WHERE id = ${rows[0].id}`

    return Response.json({ username: rows[0].username, token })
  } catch {
    return Response.json({ error: "Ошибка сервера" }, { status: 500 })
  }
}
