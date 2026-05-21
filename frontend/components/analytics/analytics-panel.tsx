"use client"

import { useMemo } from "react"
import { motion } from "framer-motion"
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts"

const COLORS = ["#6366f1", "#a855f7", "#06b6d4", "#10b981", "#f59e0b"]

function rand(min: number, max: number) { return Math.floor(Math.random() * (max - min + 1)) + min }

function useDemo() {
  return useMemo(() => {
    const days = Array.from({ length: 14 }, (_, i) => {
      const d = new Date(); d.setDate(d.getDate() - (13 - i))
      return {
        date: d.toLocaleDateString("en", { month: "short", day: "numeric" }),
        questions: rand(4, 45),
        response_ms: rand(300, 1800),
        tokens: rand(400, 3200),
      }
    })
    const confidence = Array.from({ length: 60 }, () => +(Math.random() * 0.5 + 0.45).toFixed(2))
    const methods = [
      { name: "MMR", value: 52 }, { name: "Similarity", value: 28 },
      { name: "Hybrid", value: 14 }, { name: "Compressed", value: 6 },
    ]
    const top_docs = [
      { name: "policy.pdf", refs: 42 }, { name: "report.pdf", refs: 31 },
      { name: "handbook.pdf", refs: 25 }, { name: "manual.pdf", refs: 19 },
      { name: "tech_docs.pdf", refs: 14 },
    ]
    return { days, confidence, methods, top_docs }
  }, [])
}

const TT_STYLE = {
  backgroundColor: "#111",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "10px",
  fontSize: "12px",
  color: "#e2e8f0",
}

const KPI = [
  { label: "Questions",     getValue: (d: ReturnType<typeof useDemo>) => d.days.reduce((a, r) => a + r.questions, 0),        suffix: "" },
  { label: "Avg Response",  getValue: (d: ReturnType<typeof useDemo>) => `${Math.round(d.days.reduce((a, r) => a + r.response_ms, 0) / d.days.length)} ms`, suffix: "" },
  { label: "Avg Confidence",getValue: (d: ReturnType<typeof useDemo>) => `${Math.round(d.confidence.reduce((a, c) => a + c, 0) / d.confidence.length * 100)}%`, suffix: "" },
  { label: "Total Tokens",  getValue: (d: ReturnType<typeof useDemo>) => d.days.reduce((a, r) => a + r.tokens, 0).toLocaleString(), suffix: "" },
]

export function AnalyticsPanel() {
  const data = useDemo()

  return (
    <div className="h-screen overflow-y-auto bg-[#0a0a0a]">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-[22px] font-semibold text-white tracking-tight mb-1">Analytics</h1>
          <p className="text-[13px] text-white/35">Usage metrics and performance insights — demo data</p>
        </div>

        {/* KPI row */}
        <div className="grid grid-cols-4 gap-3 mb-8">
          {KPI.map((k, i) => (
            <motion.div
              key={k.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.07 }}
              whileHover={{ y: -2 }}
              className="bg-white/[0.03] border border-white/[0.07] rounded-xl p-4 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-indigo-500/0 via-indigo-500/60 to-indigo-500/0" />
              <p className="text-[20px] font-bold text-white">{k.getValue(data)}</p>
              <p className="text-[11px] text-white/35 mt-0.5">{k.label}</p>
            </motion.div>
          ))}
        </div>

        {/* Row 1 — Questions + Response time */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <ChartCard title="Questions / Day">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data.days}>
                <defs>
                  <linearGradient id="gQ" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} interval={2} />
                <YAxis tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TT_STYLE} cursor={{ stroke: "rgba(99,102,241,0.2)" }} />
                <Area type="monotone" dataKey="questions" stroke="#6366f1" strokeWidth={2} fill="url(#gQ)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Response Time (ms)">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.days} barSize={10}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} interval={2} />
                <YAxis tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TT_STYLE} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="response_ms" fill="#06b6d4" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Row 2 — Token usage + Top docs */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <ChartCard title="Token Usage">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={data.days}>
                <defs>
                  <linearGradient id="gT" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#a855f7" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} interval={2} />
                <YAxis tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={TT_STYLE} cursor={{ stroke: "rgba(168,85,247,0.2)" }} />
                <Area type="monotone" dataKey="tokens" stroke="#a855f7" strokeWidth={2} fill="url(#gT)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Top Source Documents">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.top_docs} layout="vertical" barSize={8}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: "#475569" }} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={80} />
                <Tooltip contentStyle={TT_STYLE} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                <Bar dataKey="refs" radius={[0, 3, 3, 0]}>
                  {data.top_docs.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Row 3 — Search methods donut */}
        <ChartCard title="Search Method Distribution">
          <div className="flex items-center justify-center gap-10 py-4">
            <PieChart width={180} height={180}>
              <Pie data={data.methods} cx={85} cy={85} innerRadius={52} outerRadius={80}
                dataKey="value" stroke="none">
                {data.methods.map((_, i) => (
                  <Cell key={i} fill={COLORS[i]} fillOpacity={0.9} />
                ))}
              </Pie>
            </PieChart>
            <div className="space-y-2">
              {data.methods.map((m, i) => (
                <div key={m.name} className="flex items-center gap-2.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i] }} />
                  <span className="text-[12px] text-white/60">{m.name}</span>
                  <span className="text-[12px] font-semibold text-white/80 ml-auto pl-4">{m.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/[0.025] border border-white/[0.07] rounded-2xl p-5"
    >
      <p className="text-[12px] font-semibold text-white/45 uppercase tracking-wider mb-4">{title}</p>
      {children}
    </motion.div>
  )
}
