"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Settings2, Trash2, Zap, Sparkles, Columns, Square, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useDeployments } from "@/hooks/use-api"

interface Message {
  role: "user" | "assistant"
  content: string
  modelId?: string
}

export default function PlaygroundPage() {
  const { data: deployments } = useDeployments()
  const [isComparisonMode, setIsComparisonMode] = useState(false)
  const [selectedModelA, setSelectedModelIdA] = useState("")
  const [selectedModelB, setSelectedModelIdB] = useState("")

  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! Select a model and start testing your fine-tuned assistant." }
  ])
  
  // Separate states for comparison responses
  const [messagesA, setMessagesA] = useState<Message[]>([])
  const [messagesB, setMessagesB] = useState<Message[]>([])

  const [input, setInput] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, messagesA, messagesB])

  const handleSend = async () => {
    if (!input.trim() || (!selectedModelA && !isComparisonMode)) return

    const userMessage: Message = { role: "user", content: input }
    
    if (isComparisonMode) {
        setMessagesA(prev => [...prev, userMessage])
        setMessagesB(prev => [...prev, userMessage])
    } else {
        setMessages(prev => [...prev, userMessage])
    }
    
    setInput("")
    setIsTyping(true)

    // Simulate AI response for Model A
    setTimeout(() => {
      const responseA: Message = { 
        role: "assistant", 
        content: `Response from ${deployments?.find((d:any) => d.id === selectedModelA)?.name || 'Model A'}: I've analyzed "${input}" using my specialized weights.` 
      }
      if (isComparisonMode) setMessagesA(prev => [...prev, responseA])
      else setMessages(prev => [...prev, responseA])
      
      if (!isComparisonMode) setIsTyping(false)
    }, 1200)

    // Simulate AI response for Model B (if comparison)
    if (isComparisonMode) {
        setTimeout(() => {
            const responseB: Message = { 
              role: "assistant", 
              content: `Response from ${deployments?.find((d:any) => d.id === selectedModelB)?.name || 'Model B'}: My fine-tuning on this task suggests a slightly different approach for "${input}".` 
            }
            setMessagesB(prev => [...prev, responseB])
            setIsTyping(false)
          }, 1800)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] gap-4">
      {/* Top Controls */}
      <div className="flex items-center justify-between bg-card border rounded-xl p-3 px-6 shadow-sm">
         <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 border-r pr-6">
                <button 
                    onClick={() => setIsComparisonMode(false)}
                    className={cn("p-2 rounded-lg transition-colors", !isComparisonMode ? "bg-primary/10 text-primary" : "hover:bg-muted text-muted-foreground")}
                >
                    <Square size={18} />
                </button>
                <button 
                    onClick={() => setIsComparisonMode(true)}
                    className={cn("p-2 rounded-lg transition-colors", isComparisonMode ? "bg-primary/10 text-primary" : "hover:bg-muted text-muted-foreground")}
                >
                    <Columns size={18} />
                </button>
                <span className="text-xs font-semibold uppercase tracking-wider ml-2">Mode</span>
            </div>

            <div className="flex items-center gap-4">
                <div className="flex flex-col">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase">Model A</span>
                    <select 
                        className="bg-transparent text-sm font-semibold focus:outline-none"
                        value={selectedModelA}
                        onChange={(e) => setSelectedModelIdA(e.target.value)}
                    >
                        <option value="">Select Endpoint</option>
                        {deployments?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                </div>
                {isComparisonMode && (
                    <div className="flex flex-col border-l pl-4">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase">Model B</span>
                        <select 
                            className="bg-transparent text-sm font-semibold focus:outline-none"
                            value={selectedModelB}
                            onChange={(e) => setSelectedModelIdB(e.target.value)}
                        >
                            <option value="">Select Endpoint</option>
                            {deployments?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
                        </select>
                    </div>
                )}
            </div>
         </div>

         <button 
            onClick={() => { setMessages([]); setMessagesA([]); setMessagesB([]); }}
            className="text-muted-foreground hover:text-destructive p-2 transition-colors"
         >
            <Trash2 size={18} />
         </button>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Chat Area(s) */}
        <div className={cn(
            "flex-1 flex gap-4 transition-all duration-500",
            isComparisonMode ? "flex-row" : "flex-col"
        )}>
            {/* Model A View */}
            <div className="flex-1 flex flex-col rounded-xl border bg-card shadow-sm overflow-hidden relative">
                <div className="absolute top-2 right-4 text-[10px] font-bold text-primary/40 uppercase pointer-events-none">Model A Output</div>
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6">
                {(isComparisonMode ? messagesA : messages).map((msg, i) => (
                    <div key={i} className={cn(
                    "flex gap-4 max-w-[85%]",
                    msg.role === "user" ? "ml-auto flex-row-reverse" : ""
                    )}>
                    <div className={cn(
                        "w-7 h-7 rounded-lg flex items-center justify-center shrink-0",
                        msg.role === "assistant" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                    )}>
                        {msg.role === "assistant" ? <Bot size={16} /> : <User size={16} />}
                    </div>
                    <div className={cn(
                        "rounded-2xl px-4 py-2 text-sm leading-relaxed",
                        msg.role === "assistant" ? "bg-muted/50" : "bg-primary text-primary-foreground shadow-sm"
                    )}>
                        {msg.content}
                    </div>
                    </div>
                ))}
                </div>
            </div>

            {/* Model B View */}
            {isComparisonMode && (
                <div className="flex-1 flex flex-col rounded-xl border bg-card shadow-sm overflow-hidden relative">
                    <div className="absolute top-2 right-4 text-[10px] font-bold text-primary/40 uppercase pointer-events-none">Model B Output</div>
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messagesB.map((msg, i) => (
                        <div key={i} className={cn(
                        "flex gap-4 max-w-[85%]",
                        msg.role === "user" ? "ml-auto flex-row-reverse" : ""
                        )}>
                        <div className={cn(
                            "w-7 h-7 rounded-lg flex items-center justify-center shrink-0",
                            msg.role === "assistant" ? "bg-amber-500/10 text-amber-500" : "bg-muted text-muted-foreground"
                        )}>
                            {msg.role === "assistant" ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className={cn(
                            "rounded-2xl px-4 py-2 text-sm leading-relaxed",
                            msg.role === "assistant" ? "bg-amber-500/5 border border-amber-500/10" : "bg-primary text-primary-foreground shadow-sm"
                        )}>
                            {msg.content}
                        </div>
                        </div>
                    ))}
                    </div>
                </div>
            )}
        </div>

        {/* Settings Panel */}
        <div className="w-72 rounded-xl border bg-card p-6 shadow-sm flex flex-col gap-6 overflow-y-auto hidden lg:flex">
            <h3 className="font-bold flex items-center gap-2">
            <Settings2 size={18} /> Parameters
            </h3>
            
            <div className="space-y-4">
            <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium text-muted-foreground">
                <span>Temperature</span>
                <span className="text-primary">0.7</span>
                </div>
                <input type="range" min="0" max="2" step="0.1" defaultValue="0.7" className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" />
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium text-muted-foreground">
                <span>Top-P</span>
                <span className="text-primary">0.9</span>
                </div>
                <input type="range" min="0" max="1" step="0.05" defaultValue="0.9" className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" />
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium text-muted-foreground">
                <span>Max Tokens</span>
                <span className="text-primary">1024</span>
                </div>
                <input type="range" min="128" max="4096" step="128" defaultValue="1024" className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary" />
            </div>
            </div>

            <div className="mt-auto pt-6 border-t">
                <div className="rounded-lg bg-primary/5 p-4 border border-primary/10">
                    <div className="flex items-center gap-2 text-primary font-bold text-[10px] uppercase mb-2">
                        <Sparkles size={12} /> Optimization
                    </div>
                    <p className="text-[10px] text-muted-foreground leading-relaxed">
                        Comparison mode uses shared VRAM caching to minimize latency when testing multiple LoRA adapters.
                    </p>
                </div>
            </div>
        </div>
      </div>

      {/* Input Bar */}
      <div className="max-w-4xl mx-auto w-full">
        <div className="relative group">
            <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
                placeholder={selectedModelA || isComparisonMode ? "Type your prompt..." : "Select a model above to start"}
                disabled={!selectedModelA && !isComparisonMode}
                className="w-full rounded-2xl border bg-card px-6 py-4 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none shadow-lg transition-all"
            />
            <button 
                onClick={handleSend}
                disabled={isTyping || (!selectedModelA && !isComparisonMode)}
                className="absolute right-3 top-3 p-2 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all disabled:opacity-50 shadow-md"
            >
                {isTyping ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send size={20} />}
            </button>
        </div>
      </div>
    </div>
  )
}
