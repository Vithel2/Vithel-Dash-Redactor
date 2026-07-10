export default function Home() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 12,
        textAlign: "center",
        padding: 24,
      }}
    >
      <h1 style={{ color: "#5ad6ff", margin: 0 }}>Vithel Dash Redactor</h1>
      <p style={{ margin: 0, color: "#9a9ab0" }}>Сервер аккаунтов — Beta 1.6</p>
      <p style={{ margin: 0, color: "#6dd66d" }}>Сервер работает</p>
      <div style={{ marginTop: 16, color: "#78788c", fontSize: 14 }}>
        <p style={{ margin: 4 }}>POST /api/register — регистрация</p>
        <p style={{ margin: 4 }}>POST /api/login — вход</p>
      </div>
    </main>
  )
}
