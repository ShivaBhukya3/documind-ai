"use client"

import { useState, useCallback, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Upload, FileText, Trash2, FileSpreadsheet, Presentation, File, RefreshCw, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { uploadDocument, listDocuments, deleteDocument, getDocumentStats, type DocumentRecord } from "@/lib/api"
import { toast } from "sonner"

const EXT_ICON: Record<string, React.ReactNode> = {
  pdf:  <FileText className="w-4 h-4 text-red-400" />,
  docx: <FileText className="w-4 h-4 text-blue-400" />,
  txt:  <File className="w-4 h-4 text-white/40" />,
  csv:  <FileSpreadsheet className="w-4 h-4 text-emerald-400" />,
  pptx: <Presentation className="w-4 h-4 text-orange-400" />,
  md:   <FileText className="w-4 h-4 text-indigo-400" />,
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  if (!iso) return ""
  try {
    return new Date(iso + "Z").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return iso
  }
}

export function DocumentManager() {
  const [docs, setDocs] = useState<DocumentRecord[]>([])
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState<string[]>([])
  const [stats, setStats] = useState({ total_vectors: 0, index_size_mb: 0 })
  const [deleting, setDeleting] = useState<string | null>(null)
  const [loadingDocs, setLoadingDocs] = useState(true)

  const refreshDocs = useCallback(async () => {
    try {
      const data = await listDocuments()
      setDocs(data.documents)
    } catch {
      // API may not be ready yet
    } finally {
      setLoadingDocs(false)
    }
  }, [])

  useEffect(() => {
    refreshDocs()
  }, [refreshDocs])

  useEffect(() => {
    getDocumentStats().then(setStats).catch(() => {})
  }, [docs])

  const processFiles = useCallback(async (files: File[]) => {
    const allowed = ["pdf", "docx", "txt", "csv", "pptx", "md"]
    const valid = files.filter((f) => allowed.includes(f.name.split(".").pop()?.toLowerCase() ?? ""))
    if (!valid.length) { toast.error("No supported file types selected."); return }

    setUploading(valid.map((f) => f.name))

    for (const file of valid) {
      const warmupToast = setTimeout(
        () => toast.info("Server is waking up — this may take up to 60 s on first upload…", { duration: 55_000, id: "warmup" }),
        6_000
      )
      try {
        await uploadDocument(file)
        clearTimeout(warmupToast)
        toast.dismiss("warmup")
        toast.success(`Indexed ${file.name}`)
      } catch (e: unknown) {
        clearTimeout(warmupToast)
        toast.dismiss("warmup")
        toast.error(`Failed: ${e instanceof Error ? e.message : String(e)}`)
      }
    }

    setUploading([])
    await refreshDocs()
  }, [refreshDocs])

  const handleDelete = useCallback(async (filename: string) => {
    setDeleting(filename)
    try {
      await deleteDocument(filename)
      toast.success(`Removed ${filename}`)
      await refreshDocs()
    } catch (e: unknown) {
      toast.error(`Delete failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setDeleting(null)
    }
  }, [refreshDocs])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    processFiles(Array.from(e.dataTransfer.files))
  }, [processFiles])

  const onInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) processFiles(Array.from(e.target.files))
  }

  const successCount = docs.filter((d) => d.status === "success" || d.status === "indexed").length
  const totalChunks = docs.reduce((sum, d) => sum + (d.chunks ?? 0), 0)

  const STAT_CARDS = [
    { label: "Documents", value: docs.length, sub: "total indexed" },
    { label: "Chunks",    value: totalChunks, sub: "text segments" },
    { label: "Vectors",   value: stats.total_vectors, sub: "embeddings" },
    { label: "Successful", value: successCount, sub: "ready to query" },
  ]

  return (
    <div className="h-screen overflow-y-auto bg-[#0a0a0a]">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-[22px] font-semibold text-white tracking-tight mb-1">Documents</h1>
          <p className="text-[13px] text-white/35">Upload and index files to query with DocuMind AI</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mb-8">
          {STAT_CARDS.map((s) => (
            <motion.div
              key={s.label}
              whileHover={{ y: -2 }}
              className="bg-white/[0.03] border border-white/[0.07] rounded-xl p-4"
            >
              <p className="text-[20px] font-bold text-white">{s.value}</p>
              <p className="text-[11px] text-white/35 mt-0.5">{s.label}</p>
              <p className="text-[10px] text-white/20">{s.sub}</p>
            </motion.div>
          ))}
        </div>

        {/* Drop zone */}
        <motion.label
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          animate={{ borderColor: dragging ? "rgba(99,102,241,0.6)" : "rgba(255,255,255,0.07)" }}
          className={cn(
            "flex flex-col items-center justify-center gap-3 p-10 rounded-2xl border-2 border-dashed cursor-pointer transition-colors mb-8",
            dragging ? "bg-indigo-500/5" : "bg-white/[0.02] hover:bg-white/[0.04]"
          )}
        >
          <input type="file" multiple accept=".pdf,.docx,.txt,.csv,.pptx,.md" className="hidden" onChange={onInput} />
          <div className="w-10 h-10 rounded-xl bg-white/[0.05] border border-white/[0.09] flex items-center justify-center">
            <Upload className="w-5 h-5 text-white/40" />
          </div>
          <div className="text-center">
            <p className="text-[13px] font-medium text-white/60">Drop files here or click to browse</p>
            <p className="text-[11px] text-white/25 mt-0.5">PDF, DOCX, TXT, CSV, PPTX, MD · max {process.env.NEXT_PUBLIC_MAX_UPLOAD_MB ?? 50} MB</p>
          </div>
        </motion.label>

        {/* Uploading in progress */}
        <AnimatePresence>
          {uploading.map((name) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="flex items-center gap-3 px-4 py-3 bg-indigo-500/8 border border-indigo-500/20 rounded-xl mb-2"
            >
              <RefreshCw className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
              <span className="text-[12px] text-white/60">{name}</span>
              <span className="ml-auto text-[11px] text-indigo-400">Indexing…</span>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Document list */}
        {loadingDocs ? (
          <div className="flex items-center justify-center py-12 gap-2 text-white/25">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span className="text-[13px]">Loading documents…</span>
          </div>
        ) : docs.length > 0 ? (
          <div className="space-y-1.5">
            <p className="text-[11px] font-semibold text-white/25 uppercase tracking-widest mb-3">
              Indexed files
            </p>
            <AnimatePresence>
              {docs.map((doc) => {
                const ext = doc.filename.split(".").pop()?.toLowerCase() ?? ""
                const isDeleting = deleting === doc.filename
                const isFailed = doc.status === "failed" || doc.status === "error" || doc.status === "partial"
                return (
                  <motion.div
                    key={doc.filename}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 8, height: 0 }}
                    className="flex items-center gap-3 px-4 py-3 bg-white/[0.03] hover:bg-white/[0.05] border border-white/[0.06] rounded-xl transition-colors group"
                  >
                    <div className="w-7 h-7 rounded-lg bg-white/[0.05] flex items-center justify-center shrink-0">
                      {isFailed
                        ? <AlertCircle className="w-4 h-4 text-red-400" />
                        : (EXT_ICON[ext] ?? <File className="w-4 h-4 text-white/30" />)
                      }
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-white/80 truncate">{doc.filename}</p>
                      <p className="text-[11px] text-white/30">
                        {isFailed
                          ? (doc.error || "Processing failed")
                          : `${doc.chunks} chunks · ${formatBytes(doc.file_size_bytes)} · ${formatDate(doc.uploaded_at)}`
                        }
                      </p>
                    </div>
                    <span className={cn(
                      "text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0",
                      isFailed
                        ? "bg-red-500/10 text-red-400 border-red-500/20"
                        : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    )}>
                      {isFailed ? "failed" : "indexed"}
                    </span>
                    <button
                      onClick={() => handleDelete(doc.filename)}
                      disabled={isDeleting}
                      className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 text-white/25 hover:text-red-400 transition-all disabled:opacity-50"
                    >
                      {isDeleting
                        ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        : <Trash2 className="w-3.5 h-3.5" />
                      }
                    </button>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        ) : (
          <div className="text-center py-12 text-white/25">
            <File className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p className="text-[13px]">No documents indexed yet</p>
            <p className="text-[11px] mt-1">Upload a file above to get started</p>
          </div>
        )}
      </div>
    </div>
  )
}
