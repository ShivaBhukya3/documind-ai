const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
const KEY = process.env.NEXT_PUBLIC_API_KEY ?? ""

const headers = () => ({
  "Content-Type": "application/json",
  ...(KEY ? { "X-API-Key": KEY } : {}),
})

export interface Message {
  role: "user" | "assistant"
  content: string
  sources?: Source[]
  confidence?: number
  response_time_ms?: number
}

export interface Source {
  filename: string
  page?: number
  preview?: string
  score?: number
}

export interface HealthData {
  status: string
  components: Record<string, string>
  embedding_stats?: { provider: string; model_name: string; dimension: number }
}

export async function getHealth(): Promise<HealthData> {
  const r = await fetch(`${API}/health`)
  if (!r.ok) throw new Error("Health check failed")
  return r.json()
}

export async function sendChat(query: string, sessionId: string) {
  const r = await fetch(`${API}/api/v1/chat`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ question: query, session_id: sessionId, stream: false }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? `HTTP ${r.status}`)
  }
  const data = await r.json()
  return {
    answer: data.answer ?? "",
    sources: (data.sources ?? []) as Source[],
    confidence_score: data.confidence_score ?? 0,
    response_time_ms: (data.retrieval_time_ms ?? 0) + (data.generation_time_ms ?? 0),
    tokens_used: data.tokens_used ?? 0,
  }
}

export async function resetChat(sessionId: string) {
  await fetch(`${API}/api/v1/chat/reset`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export async function uploadDocument(file: File) {
  const fd = new FormData()
  fd.append("file", file)
  const r = await fetch(`${API}/api/v1/documents/upload`, {
    method: "POST",
    headers: KEY ? { "X-API-Key": KEY } : {},
    body: fd,
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? `HTTP ${r.status}`)
  }
  return r.json()
}

export interface DocumentRecord {
  id: number
  filename: string
  file_type: string
  file_size_bytes: number
  chunks: number
  status: string
  uploaded_at: string
  error: string
  s3_url: string
}

export async function listDocuments(): Promise<{ documents: DocumentRecord[]; total: number }> {
  const r = await fetch(`${API}/api/v1/documents/list`, { headers: headers() })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}

export async function deleteDocument(docId: string) {
  await fetch(`${API}/api/v1/documents/${encodeURIComponent(docId)}`, {
    method: "DELETE",
    headers: headers(),
  })
}

export async function getDocumentStats() {
  const r = await fetch(`${API}/api/v1/documents/stats`, { headers: headers() })
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}
