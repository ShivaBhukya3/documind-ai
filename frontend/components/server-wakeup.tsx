"use client"

import { useEffect } from "react"

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export function ServerWakeup() {
  useEffect(() => {
    fetch(`${API}/health`, { method: "GET" }).catch(() => {})
  }, [])
  return null
}
