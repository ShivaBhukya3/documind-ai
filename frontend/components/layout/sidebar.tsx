"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import {
  MessageSquare, FileText, BarChart3, Settings, Brain, Zap,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useEffect, useState } from "react"
import { getHealth } from "@/lib/api"

const NAV = [
  { href: "/chat",      icon: MessageSquare, label: "Chat" },
  { href: "/documents", icon: FileText,      label: "Documents" },
  { href: "/analytics", icon: BarChart3,     label: "Analytics" },
  { href: "/settings",  icon: Settings,      label: "Settings" },
]

export function Sidebar() {
  const path = usePathname()
  const [status, setStatus] = useState<"healthy" | "degraded" | "loading">("loading")

  useEffect(() => {
    getHealth()
      .then((d) => setStatus(d.status === "healthy" ? "healthy" : "degraded"))
      .catch(() => setStatus("degraded"))
  }, [])

  return (
    <aside className="w-[220px] shrink-0 flex flex-col h-screen bg-[#0d0d0d] border-r border-white/[0.06]">
      {/* Logo */}
      <div className="px-4 pt-6 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-white tracking-tight">DocuMind AI</p>
            <p className="text-[10px] text-white/30 tracking-wide uppercase">RAG Platform</p>
          </div>
        </div>
      </div>

      <div className="px-2 mb-2">
        <p className="px-2 text-[10px] font-semibold text-white/25 uppercase tracking-widest mb-1">
          Navigation
        </p>
        <nav className="space-y-0.5">
          {NAV.map(({ href, icon: Icon, label }) => {
            const active = path === href || path.startsWith(href + "/")
            return (
              <Link key={href} href={href}>
                <motion.div
                  whileHover={{ x: 2 }}
                  whileTap={{ scale: 0.98 }}
                  className={cn(
                    "flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13px] font-medium transition-colors cursor-pointer select-none",
                    active
                      ? "bg-white/[0.07] text-white"
                      : "text-white/45 hover:text-white/80 hover:bg-white/[0.04]"
                  )}
                >
                  <Icon className={cn("w-[15px] h-[15px] shrink-0", active ? "text-indigo-400" : "")} />
                  {label}
                  {active && (
                    <motion.div
                      layoutId="active-dot"
                      className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400"
                    />
                  )}
                </motion.div>
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Status */}
      <div className="px-4 pb-5 space-y-3">
        <div className="flex items-center gap-2 px-2.5 py-2 rounded-md bg-white/[0.03] border border-white/[0.06]">
          <div className={cn(
            "w-1.5 h-1.5 rounded-full",
            status === "healthy" ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" :
            status === "loading" ? "bg-yellow-400 animate-pulse" : "bg-red-400"
          )} />
          <span className="text-[11px] text-white/35">
            {status === "loading" ? "Connecting…" : status === "healthy" ? "API Online" : "API Degraded"}
          </span>
          <Zap className="w-3 h-3 text-white/20 ml-auto" />
        </div>
        <p className="text-[10px] text-white/20 text-center">
          DocuMind AI v1.0
        </p>
      </div>
    </aside>
  )
}
