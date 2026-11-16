"use client";
import { useState } from "react";
import { Send, Sparkles, Paperclip, Mic, ChevronDown, ChevronUp, Bot, User } from "lucide-react";
import { Card, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";

export function ExpandableInputPanel() {
  const [expanded, setExpanded] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role:"user"|"assistant", text:string}[]>([
    { role: "assistant", text: "Hi! I'm your dashboard assistant. Ask me anything about your workspace, reports, or metrics." },
    { role: "user", text: "Show me the latest performance summary." },
    { role: "assistant", text: "Sure — last 7 days: 12.4k views (+18%), 3.2k active sessions. Peak was Tuesday 2pm. Want a detailed breakdown?" },
  ]);

  const send = () => {
    if(!input.trim()) return;
    setMessages(m=> [...m, { role:"user", text: input }, { role:"assistant", text: "Got it — analyzing “"+input.slice(0,40)+"” across your connected data. (This is a placeholder response — connect your API to make it live.)" }]);
    setInput("");
  };

  return (
    <Card className="overflow-hidden flex flex-col" hover={false}>
      <CardHeader className="pb-3">
        <CardTitle>
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--gradient-from)] to-[var(--gradient-to)] grid place-items-center text-white">
            <Bot size={14} />
          </div>
          Assistant
          <span className="ml-2 text-[10px] font-bold tracking-widest uppercase bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full dark:bg-emerald-950/40 dark:text-emerald-400">LIVE</span>
        </CardTitle>
        <button onClick={()=>setExpanded(!expanded)} className="w-7 h-7 grid place-items-center rounded-full hover:bg-[var(--card-bg-soft)] border border-transparent hover:border-[var(--border)] transition">
          {expanded ? <ChevronDown size={14}/> : <ChevronUp size={14}/>}
        </button>
      </CardHeader>

      {/* Messages */}
      <div className={`px-5 flex-1 space-y-3 overflow-auto transition-all duration-300 ${expanded ? "max-h-[280px] opacity-100 pb-2" : "max-h-0 opacity-0"} scrollbar-thin`}>
        {messages.map((m,i)=>(
          <div key={i} className={`flex gap-2.5 ${m.role==="user" ? "justify-end" : "justify-start"}`}>
            {m.role==="assistant" && <div className="w-6 h-6 rounded-full bg-[var(--card-bg-soft)] border border-[var(--border)] grid place-items-center flex-shrink-0 mt-0.5"><Bot size={12} className="text-[var(--text-dim)]"/></div>}
            <div className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${m.role==="user" ? "bg-[var(--primary)] text-white rounded-br-md" : "bg-[var(--card-bg-soft)] border border-[var(--border)] text-[var(--text)] rounded-bl-md"}`}>
              {m.text}
            </div>
            {m.role==="user" && <div className="w-6 h-6 rounded-full bg-[var(--primary)] grid place-items-center flex-shrink-0 mt-0.5"><User size={12} className="text-white"/></div>}
          </div>
        ))}
        {expanded && (
          <div className="flex gap-1.5 pt-1">
            {["Summarize today","Show trends","Export report"].map(chip=>(
              <button key={chip} onClick={()=>setInput(chip)} className="text-[11px] font-medium bg-[var(--card-bg)] border border-[var(--border)] px-3 py-1.5 rounded-full hover:border-[var(--primary)] hover:text-[var(--primary)] transition">
                {chip}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Expandable input panel — as spec */}
      <div className="p-3 bg-[var(--card-bg-soft)] border-t border-[var(--border-soft)]">
        <div className={`bg-[var(--card-bg)] border border-[var(--border)] rounded-2xl p-2 flex items-end gap-2 focus-within:border-[var(--primary)] focus-within:shadow-[0_0_0_3px_var(--primary-ring)] transition-all duration-200 ${expanded ? "shadow-sm" : ""}`}>
          <button className="w-8 h-8 grid place-items-center rounded-full hover:bg-[var(--card-bg-soft)] text-[var(--text-faint)] flex-shrink-0">
            <Paperclip size={16} />
          </button>
          <textarea
            value={input}
            onChange={e=>setInput(e.target.value)}
            onFocus={()=>setExpanded(true)}
            onKeyDown={e=>{ if(e.key==="Enter" && !e.shiftKey){ e.preventDefault(); send(); }}}
            placeholder="Ask anything… (try: ‘summarize performance’)"
            rows={expanded ? 2 : 1}
            className="flex-1 bg-transparent outline-none resize-none text-[13px] placeholder:text-[var(--text-faint)] py-1.5 min-h-[24px] max-h-[80px]"
          />
          <div className="flex items-center gap-1 flex-shrink-0">
            <button className="w-8 h-8 grid place-items-center rounded-full hover:bg-[var(--card-bg-soft)] text-[var(--text-faint)]">
              <Mic size={16} />
            </button>
            <button onClick={send} className="w-8 h-8 grid place-items-center rounded-full bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] transition shadow-sm">
              <Send size={14} />
            </button>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 px-1">
          <span className="text-[11px] text-[var(--text-faint)] font-medium hidden sm:block">Press Enter to send • Shift+Enter for new line</span>
          <span className="text-[11px] font-medium text-[var(--text-faint)] flex items-center gap-1"><Sparkles size={12}/> Powered by your API</span>
        </div>
      </div>
    </Card>
  );
}
