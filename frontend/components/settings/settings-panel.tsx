"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Brain, Search, Sliders, Key, Save, RotateCcw } from "lucide-react"
import { toast } from "sonner"

const TABS = [
  { id: "llm",       label: "LLM",       icon: Brain },
  { id: "retrieval", label: "Retrieval", icon: Search },
  { id: "system",    label: "System",    icon: Sliders },
]

const GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "gemma2-9b-it"]
const PROVIDERS   = ["groq", "openai", "huggingface", "ollama"]

export function SettingsPanel() {
  const [tab, setTab] = useState("llm")
  const [provider, setProvider]     = useState("groq")
  const [model, setModel]           = useState("llama-3.1-8b-instant")
  const [temperature, setTemp]      = useState(0.1)
  const [maxTokens, setMaxTokens]   = useState(1000)
  const [streaming, setStreaming]   = useState(true)
  const [topK, setTopK]             = useState(5)
  const [searchType, setSearchType] = useState("mmr")
  const [threshold, setThreshold]   = useState(0.3)
  const [chunkSize, setChunkSize]   = useState(1000)
  const [freeMode, setFreeMode]     = useState(false)
  const [groqKey, setGroqKey]       = useState("")
  const [openaiKey, setOpenaiKey]   = useState("")

  function save() { toast.success("Settings saved — restart API to apply") }
  function reset() { toast.info("Reset to defaults") }

  return (
    <div className="h-screen overflow-y-auto bg-[#0a0a0a]">
      <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-[22px] font-semibold text-white tracking-tight mb-1">Settings</h1>
          <p className="text-[13px] text-white/35">Configure LLM, retrieval, and system behaviour</p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 p-1 bg-white/[0.03] border border-white/[0.07] rounded-xl mb-8">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[12.5px] font-medium transition-all ${
                tab === id
                  ? "bg-white/[0.08] text-white shadow-sm"
                  : "text-white/35 hover:text-white/60"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.18 }}
          className="space-y-5"
        >
          {tab === "llm" && (
            <>
              <Section title="Language Model" icon={<Brain className="w-3.5 h-3.5" />}>
                <Field label="Provider">
                  <Select value={provider} onChange={setProvider} options={PROVIDERS} />
                </Field>
                <Field label="Model">
                  <Select value={model} onChange={setModel} options={GROQ_MODELS} />
                </Field>
                <Field label={`Temperature: ${temperature}`}>
                  <input type="range" min={0} max={1} step={0.05} value={temperature}
                    onChange={(e) => setTemp(+e.target.value)}
                    className="w-full accent-indigo-500 cursor-pointer" />
                </Field>
                <Field label={`Max Tokens: ${maxTokens}`}>
                  <input type="range" min={256} max={4096} step={128} value={maxTokens}
                    onChange={(e) => setMaxTokens(+e.target.value)}
                    className="w-full accent-indigo-500 cursor-pointer" />
                </Field>
                <Field label="Streaming">
                  <Toggle value={streaming} onChange={setStreaming} />
                </Field>
              </Section>

              <Section title="API Keys" icon={<Key className="w-3.5 h-3.5" />}>
                <Field label="Groq API Key">
                  <TextInput type="password" value={groqKey} onChange={setGroqKey} placeholder="gsk_…" />
                </Field>
                <Field label="OpenAI API Key">
                  <TextInput type="password" value={openaiKey} onChange={setOpenaiKey} placeholder="sk-…" />
                </Field>
              </Section>
            </>
          )}

          {tab === "retrieval" && (
            <Section title="Retrieval Configuration" icon={<Search className="w-3.5 h-3.5" />}>
              <Field label="Search Type">
                <Select value={searchType} onChange={setSearchType} options={["mmr","similarity","hybrid"]} />
              </Field>
              <Field label={`Top-K: ${topK}`}>
                <input type="range" min={1} max={20} step={1} value={topK}
                  onChange={(e) => setTopK(+e.target.value)}
                  className="w-full accent-indigo-500 cursor-pointer" />
              </Field>
              <Field label={`Score Threshold: ${threshold}`}>
                <input type="range" min={0} max={1} step={0.05} value={threshold}
                  onChange={(e) => setThreshold(+e.target.value)}
                  className="w-full accent-indigo-500 cursor-pointer" />
              </Field>
              <Field label={`Chunk Size: ${chunkSize}`}>
                <input type="range" min={256} max={2000} step={128} value={chunkSize}
                  onChange={(e) => setChunkSize(+e.target.value)}
                  className="w-full accent-indigo-500 cursor-pointer" />
              </Field>
            </Section>
          )}

          {tab === "system" && (
            <>
              <Section title="Runtime" icon={<Sliders className="w-3.5 h-3.5" />}>
                <Field label="FREE MODE (no API keys)">
                  <Toggle value={freeMode} onChange={setFreeMode} />
                </Field>
              </Section>
              <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/15 space-y-3">
                <p className="text-[11px] font-semibold text-red-400 uppercase tracking-wide">Danger Zone</p>
                <button
                  onClick={() => toast.error("Cleared all data")}
                  className="w-full text-left text-[12.5px] text-red-400/70 hover:text-red-400 transition-colors py-1"
                >
                  Clear all indexed data →
                </button>
              </div>
            </>
          )}
        </motion.div>

        {/* Actions */}
        <div className="flex gap-3 mt-8">
          <button
            onClick={save}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl text-[13px] font-medium transition-colors"
          >
            <Save className="w-3.5 h-3.5" />
            Save
          </button>
          <button
            onClick={reset}
            className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] hover:bg-white/[0.08] text-white/60 hover:text-white rounded-xl text-[13px] font-medium transition-colors border border-white/[0.07]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white/[0.025] border border-white/[0.07] rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/[0.06]">
        <span className="text-indigo-400">{icon}</span>
        <p className="text-[12px] font-semibold text-white/60">{title}</p>
      </div>
      <div className="p-4 space-y-4">{children}</div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[140px_1fr] items-center gap-4">
      <label className="text-[12px] text-white/40">{label}</label>
      {children}
    </div>
  )
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-white/[0.05] border border-white/[0.09] text-white/80 text-[12.5px] rounded-lg px-3 py-1.5 outline-none focus:border-indigo-500/50 transition-colors"
    >
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

function TextInput({ type="text", value, onChange, placeholder }: { type?: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-white/[0.05] border border-white/[0.09] text-white/80 text-[12.5px] rounded-lg px-3 py-1.5 outline-none focus:border-indigo-500/50 transition-colors placeholder-white/20"
    />
  )
}

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className={`w-10 h-5.5 rounded-full transition-colors relative ${value ? "bg-indigo-500" : "bg-white/[0.1]"}`}
    >
      <motion.div
        animate={{ x: value ? 20 : 2 }}
        transition={{ type: "spring", stiffness: 500, damping: 35 }}
        className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm"
      />
    </button>
  )
}
