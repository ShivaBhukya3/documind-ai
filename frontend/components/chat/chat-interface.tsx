"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, RotateCcw, Sparkles, FileText, ChevronDown } from "lucide-react"
import { cn, generateSessionId } from "@/lib/utils"
import { sendChat, resetChat, listDocuments, type Message } from "@/lib/api"
import { toast } from "sonner"

const STATIC_SUGGESTIONS = [
  "Summarise all documents",
  "What are the key findings?",
  "List all dates mentioned",
  "What actions are required?",
]

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState("")
  const [tokens, setTokens] = useState(0)
  const [suggestions, setSuggestions] = useState<string[]>(STATIC_SUGGESTIONS)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setSessionId(generateSessionId())
  }, [])

  useEffect(() => {
    listDocuments().then(({ documents }) => {
      if (documents.length === 0) return
      const docSuggestions = documents
        .filter((d) => d.status === "success" || d.status === "indexed")
        .slice(0, 2)
        .map((d) => `Summarise ${d.filename}`)
      setSuggestions([...docSuggestions, ...STATIC_SUGGESTIONS].slice(0, 4))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  async function submit(query: string) {
    if (!query.trim() || loading) return
    setInput("")
    setMessages((p) => [...p, { role: "user", content: query }])
    setLoading(true)
    try {
      const res = await sendChat(query, sessionId)
      setMessages((p) => [...p, {
        role: "assistant",
        content: res.answer || "No answer returned.",
        sources: res.sources ?? [],
        confidence: res.confidence_score ?? 0,
        response_time_ms: res.response_time_ms,
      }])
      setTokens((t) => t + (res.tokens_used ?? 0))
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error"
      toast.error(`Failed: ${msg}. Is the API running on port 8000?`)
      setMessages((p) => p.slice(0, -1))
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  async function handleReset() {
    await resetChat(sessionId)
    setMessages([])
    setTokens(0)
    toast.success("Conversation cleared")
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      submit(input)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a]">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h1 className="text-[14px] font-semibold text-white">Chat</h1>
          <span className="text-[11px] text-white/25 font-mono">#{sessionId}</span>
        </div>
        <div className="flex items-center gap-3">
          {tokens > 0 && (
            <span className="text-[11px] text-white/30 font-mono">{tokens.toLocaleString()} tokens</span>
          )}
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 text-[12px] text-white/35 hover:text-white/70 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full gap-6 text-center"
          >
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-white/[0.08] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-[18px] font-semibold text-white/80 mb-1">Ask anything about your documents</h2>
              <p className="text-[13px] text-white/30">Upload documents first, then ask questions.</p>
            </div>
            <div className="grid grid-cols-2 gap-2 max-w-md w-full">
              {suggestions.map((s) => (
                <motion.button
                  key={s}
                  whileHover={{ scale: 1.02, y: -1 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => submit(s)}
                  className="text-left text-[12px] text-white/50 hover:text-white/80 bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.07] rounded-lg px-3 py-2.5 transition-all"
                >
                  {s}
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, ease: [0.4, 0, 0.2, 1] }}
              className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}
            >
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 mt-0.5 shadow-md shadow-indigo-500/20">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
              )}
              <div className={cn("max-w-[72%] space-y-2", msg.role === "user" ? "items-end flex flex-col" : "")}>
                {msg.role === "user" ? (
                  <div className="bg-indigo-600/90 text-white rounded-2xl rounded-br-sm px-4 py-2.5 text-[13.5px] leading-relaxed shadow-lg shadow-indigo-500/15">
                    {msg.content}
                  </div>
                ) : (
                  <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl rounded-bl-sm px-4 py-3 text-[13.5px] leading-relaxed text-white/85">
                    {msg.content}
                    {(msg.sources ?? []).length > 0 && (
                      <SourceList sources={msg.sources!} confidence={msg.confidence ?? 0} />
                    )}
                  </div>
                )}
                {msg.response_time_ms && (
                  <p className="text-[10px] text-white/20 px-1">{msg.response_time_ms}ms</p>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-7 h-7 rounded-full bg-white/[0.08] flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold text-white/60">
                  U
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-md shadow-indigo-500/20">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="bg-white/[0.04] border border-white/[0.07] rounded-2xl rounded-bl-sm px-4 py-3">
              <TypingDots />
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="shrink-0 px-6 pb-6 pt-3">
        <div className="flex gap-2 items-end bg-white/[0.04] border border-white/[0.09] rounded-2xl px-4 py-3 focus-within:border-indigo-500/50 focus-within:bg-white/[0.05] transition-all shadow-lg">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about your documents…"
            rows={1}
            className="flex-1 bg-transparent text-[13.5px] text-white placeholder-white/25 resize-none outline-none leading-relaxed max-h-32 py-0.5"
            style={{ scrollbarWidth: "none" }}
          />
          <motion.button
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.94 }}
            onClick={() => submit(input)}
            disabled={!input.trim() || loading}
            className={cn(
              "w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-all",
              input.trim() && !loading
                ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/30 hover:bg-indigo-400"
                : "bg-white/[0.06] text-white/25 cursor-not-allowed"
            )}
          >
            <Send className="w-3.5 h-3.5" />
          </motion.button>
        </div>
        <p className="text-[10px] text-white/18 text-center mt-2">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center h-4">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-indigo-400"
          animate={{ scale: [0.6, 1.1, 0.6], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  )
}

function SourceList({ sources, confidence }: { sources: NonNullable<Message["sources"]>; confidence: number }) {
  const [open, setOpen] = useState(false)
  const confColor = confidence > 0.7 ? "text-emerald-400" : confidence > 0.4 ? "text-yellow-400" : "text-red-400"

  return (
    <div className="mt-3 pt-3 border-t border-white/[0.07]">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-[11px] text-white/35 hover:text-white/60 transition-colors"
      >
        <FileText className="w-3 h-3" />
        {sources.length} source{sources.length !== 1 ? "s" : ""}
        <span className={cn("font-semibold", confColor)}>{Math.round(confidence * 100)}% conf.</span>
        <ChevronDown className={cn("w-3 h-3 transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            <div className="mt-2 space-y-1.5">
              {sources.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-[11px] text-white/40">
                  <span className="text-white/20 shrink-0">#{i + 1}</span>
                  <span className="text-indigo-400/70">{s.filename}</span>
                  {s.page && <span className="text-white/25">p.{s.page}</span>}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
