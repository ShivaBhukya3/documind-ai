"use client"
import { Toaster as Sonner, type ToasterProps } from "sonner"

export function Toaster(props: ToasterProps) {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: "group toast bg-[#111] border border-white/10 text-white shadow-lg rounded-xl text-sm",
          description: "text-white/50",
          actionButton: "bg-indigo-500 text-white",
          cancelButton: "bg-white/10 text-white/70",
        },
      }}
      {...props}
    />
  )
}
