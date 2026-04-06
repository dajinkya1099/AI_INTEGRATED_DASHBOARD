import { useState, useRef, useEffect } from "react";

// ── Inline SVG icons ──────────────────────────────────────────────────────────
const IconChat    = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
const IconClose   = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
const IconSend    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>;
const IconBot     = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.38-1 1.73V7h1a7 7 0 0 1 7 7H4a7 7 0 0 1 7-7h1V5.73c-.6-.35-1-.99-1-1.73a2 2 0 0 1 2-2M7 14v2H5v-2h2m6 0v2h-2v-2h2m6 0v2h-2v-2h2M4 21v-2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2H4z"/></svg>;
const IconUser    = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>;
const IconClear   = () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>;
const IconChevron = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>;
const IconSpin    = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    style={{ animation: "cb-spin 0.8s linear infinite" }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
);

// ── Typing dots ───────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div style={{ display: "flex", gap: 5, alignItems: "center", padding: "2px 0" }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: "50%", background: "#93c5fd",
          animation: `cb-bounce 1.2s ease-in-out ${i * 0.2}s infinite`
        }} />
      ))}
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isBot = msg.role === "bot";
  return (
    <div style={{
      display: "flex", flexDirection: isBot ? "row" : "row-reverse",
      gap: 8, alignItems: "flex-end", marginBottom: 14,
      animation: "cb-slide 0.22s ease-out"
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
        display: "flex", alignItems: "center", justifyContent: "center",
        background: isBot
          ? "linear-gradient(135deg,#1976d2,#42a5f5)"
          : "linear-gradient(135deg,#10b981,#34d399)",
        color: "#fff"
      }}>
        {isBot ? <IconBot /> : <IconUser />}
      </div>

      <div style={{ maxWidth: "78%" }}>
        <div style={{
          padding: "10px 14px",
          borderRadius: isBot ? "4px 16px 16px 16px" : "16px 4px 16px 16px",
          background: isBot ? "#fff" : "linear-gradient(135deg,#1976d2,#42a5f5)",
          color: isBot ? "#1e293b" : "#fff",
          fontSize: 13.5, lineHeight: 1.65,
          boxShadow: isBot
            ? "0 2px 8px rgba(0,0,0,0.07)"
            : "0 2px 10px rgba(25,118,210,0.35)",
          border: isBot ? "1px solid #e2e8f0" : "none",
          wordBreak: "break-word"
        }}>
          {msg.typing ? <TypingDots /> : msg.text}
        </div>
        {!msg.typing && (
          <div style={{
            fontSize: 10.5, color: "#cbd5e1", marginTop: 3,
            textAlign: isBot ? "left" : "right",
            paddingLeft: isBot ? 3 : 0
          }}>
            {msg.time}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Schema dropdown ───────────────────────────────────────────────────────────
function SchemaSelector({ schemas, value, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: "flex", alignItems: "center", gap: 5,
          padding: "5px 10px", borderRadius: 8,
          border: "1px solid rgba(255,255,255,0.25)",
          background: "rgba(255,255,255,0.12)", color: "#e2e8f0",
          cursor: "pointer", fontSize: 12, fontWeight: 600,
          transition: "background 0.15s", whiteSpace: "nowrap"
        }}
      >
        🗄 {value || "Select Schema"}
        <span style={{ marginLeft: 2, opacity: 0.7 }}><IconChevron /></span>
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "calc(100% + 6px)", left: 0,
          background: "#1e293b", borderRadius: 10, minWidth: 180,
          boxShadow: "0 8px 24px rgba(0,0,0,0.3)",
          border: "1px solid rgba(255,255,255,0.1)",
          zIndex: 10, overflow: "hidden",
          animation: "cb-slide 0.15s ease-out"
        }}>
          {schemas.length === 0 ? (
            <div style={{ padding: "10px 14px", color: "#64748b", fontSize: 12 }}>
              Loading schemas...
            </div>
          ) : (
            schemas.map(s => (
              <button key={s}
                onClick={() => { onChange(s); setOpen(false); }}
                style={{
                  display: "block", width: "100%", textAlign: "left",
                  padding: "10px 14px",
                  background: s === value ? "rgba(25,118,210,0.4)" : "transparent",
                  border: "none",
                  color: s === value ? "#93c5fd" : "#cbd5e1",
                  cursor: "pointer", fontSize: 13,
                  fontWeight: s === value ? 700 : 400
                }}
              >
                {s}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN — DashboardChatbot
// No props needed — manages schema selection internally
// ─────────────────────────────────────────────────────────────────────────────
export default function DashboardChatbot() {
  const [open, setOpen]                   = useState(false);
  const [input, setInput]                 = useState("");
  const [loading, setLoading]             = useState(false);
  const [schemas, setSchemas]             = useState([]);
  const [selectedSchema, setSelectedSchema] = useState("");
  const [messages, setMessages]           = useState([
    {
      role: "bot",
      text: "👋 Hi! Select a schema above, then ask me anything about your data.",
      time: getTime()
    }
  ]);

  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // Auto-scroll
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  // Focus on open
  useEffect(() => { if (open) setTimeout(() => inputRef.current?.focus(), 150); }, [open]);

  // Fetch schemas
  useEffect(() => {
    fetch("http://localhost:8282/schemas")
      .then(r => r.json())
      .then(d => {
        console.log("[Chatbot] /schemas raw:", d);
        // Handle: { schemas:[...] } OR plain array
        const list = Array.isArray(d) ? d : (d.schemas || d.data || []);
        setSchemas(list);
        if (list.length === 1) setSelectedSchema(list[0]);
      })
      .catch(err => console.error("[Chatbot] schemas error:", err));
  }, []);

  function getTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // ── Send ──────────────────────────────────────────────────────────────────
  const sendMessage = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    if (!selectedSchema) {
      setMessages(prev => [...prev, {
        role: "bot",
        text: "⚠️ Please select a schema from the dropdown first.",
        time: getTime()
      }]);
      return;
    }

    setInput("");
    setMessages(prev => [...prev, { role: "user", text: question, time: getTime() }]);

    const typingId = `t-${Date.now()}`;
    setMessages(prev => [...prev, { id: typingId, role: "bot", typing: true, text: "", time: getTime() }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8282/dashboard-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          schemaName: selectedSchema,
          textQue:    question
        })
      });

      const data = await res.json();

      setMessages(prev => [
        ...prev.filter(m => m.id !== typingId),
        {
          role: "bot",
          text: data.answer || "Sorry, I couldn't find an answer.",
          time: getTime()
        }
      ]);

    } catch {
      setMessages(prev => [
        ...prev.filter(m => m.id !== typingId),
        { role: "bot", text: "⚠️ Connection error. Is the backend running?", time: getTime() }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const clearChat = () => setMessages([{
    role: "bot", text: "Chat cleared! Ask me anything.", time: getTime()
  }]);

  const SUGGESTIONS = [
    "How many employees are there?",
    "Show department wise count",
    "Who joined recently?",
  ];

  return (
    <>
      <style>{`
        @keyframes cb-spin   { to { transform: rotate(360deg); } }
        @keyframes cb-bounce { 0%,80%,100% { transform:translateY(0); } 40% { transform:translateY(-5px); } }
        @keyframes cb-slide  { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes cb-pop    { from { opacity:0; transform:scale(0.88) translateY(16px); } to { opacity:1; transform:scale(1) translateY(0); } }
        @keyframes cb-pulse  { 0%,100% { box-shadow:0 0 0 0 rgba(25,118,210,0.5); } 60% { box-shadow:0 0 0 12px rgba(25,118,210,0); } }
        .cb-chip:hover { background:#1976d2 !important; color:#fff !important; border-color:#1976d2 !important; }
        .cb-send:hover:not(:disabled) { background:#1565c0 !important; transform:scale(1.06); }
        .cb-send:disabled { opacity:0.4; cursor:not-allowed; }
        .cb-msgs::-webkit-scrollbar { width:3px; }
        .cb-msgs::-webkit-scrollbar-thumb { background:#e2e8f0; border-radius:4px; }
        .cb-input:focus { outline:none; border-color:#1976d2 !important; box-shadow:0 0 0 3px rgba(25,118,210,0.1); }
        .cb-input::placeholder { color:#94a3b8; }
        .cb-iconbtn:hover { background:rgba(255,255,255,0.2) !important; }
      `}</style>

      {/* ── FAB ── */}
      <button
        onClick={() => setOpen(o => !o)}
        title="Ask AI"
        style={{
          position: "fixed", bottom: 88, right: 24, zIndex: 1300,
          width: 54, height: 54, borderRadius: "50%", border: "none",
          background: "linear-gradient(135deg,#1976d2,#42a5f5)",
          color: "#fff", cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 18px rgba(25,118,210,0.5)",
          animation: open ? "none" : "cb-pulse 2.2s infinite",
          transition: "transform 0.18s"
        }}
      >
        {open ? <IconClose /> : <IconChat />}
        {!open && (
          <span style={{
            position: "absolute", top: 5, right: 5,
            width: 9, height: 9, borderRadius: "50%",
            background: "#ef4444", border: "2px solid #fff"
          }} />
        )}
      </button>

      {/* ── Chat panel ── */}
      {open && (
        <div style={{
          position: "fixed", bottom: 154, right: 24, zIndex: 1200,
          width: 370, height: 545,
          borderRadius: 20, background: "#f1f5f9",
          boxShadow: "0 20px 60px rgba(0,0,0,0.18)",
          display: "flex", flexDirection: "column",
          overflow: "hidden", animation: "cb-pop 0.22s ease-out"
        }}>

          {/* Header */}
          <div style={{
            background: "linear-gradient(135deg,#1e293b 0%,#1976d2 100%)",
            padding: "14px 16px", flexShrink: 0
          }}>
            {/* Row 1 */}
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: "50%",
                background: "rgba(255,255,255,0.15)",
                display: "flex", alignItems: "center", justifyContent: "center", color: "#fff"
              }}>
                <IconBot />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ color: "#fff", fontWeight: 700, fontSize: 14 }}>Dashboard AI</div>
                <div style={{ color: "#93c5fd", fontSize: 11 }}>Ask anything about your data</div>
              </div>
              <button className="cb-iconbtn" onClick={clearChat} title="Clear"
                style={{ background: "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: 6, color: "#93c5fd", cursor: "pointer", display: "flex" }}>
                <IconClear />
              </button>
              <button className="cb-iconbtn" onClick={() => setOpen(false)}
                style={{ background: "rgba(255,255,255,0.1)", border: "none", borderRadius: 8, padding: 6, color: "#93c5fd", cursor: "pointer", display: "flex" }}>
                <IconClose />
              </button>
            </div>

            {/* Row 2 — Schema selector */}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <SchemaSelector
                schemas={schemas}
                value={selectedSchema}
                onChange={setSelectedSchema}
              />
              {selectedSchema && (
                <span style={{ fontSize: 11, color: "#4ade80", display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#4ade80", display: "inline-block" }} />
                  Ready
                </span>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="cb-msgs" style={{ flex: 1, overflowY: "auto", padding: "14px 12px" }}>
            {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
            <div ref={bottomRef} />
          </div>

          {/* Suggestion chips */}
          {!loading && messages.length <= 2 && (
            <div style={{ padding: "0 12px 8px", display: "flex", flexWrap: "wrap", gap: 6 }}>
              {SUGGESTIONS.map(s => (
                <button key={s} className="cb-chip"
                  onClick={() => sendMessage(s)}
                  style={{
                    padding: "5px 11px", borderRadius: 20, fontSize: 11.5,
                    border: "1px solid #1976d2", background: "#eff6ff",
                    color: "#1976d2", cursor: "pointer",
                    transition: "all 0.15s", fontWeight: 500
                  }}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input bar */}
          <div style={{
            padding: "10px 12px", background: "#fff",
            borderTop: "1px solid #e2e8f0",
            display: "flex", alignItems: "flex-end", gap: 8, flexShrink: 0
          }}>
            <textarea
              ref={inputRef}
              className="cb-input"
              rows={1}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedSchema ? "Ask about your data..." : "Select a schema first..."}
              disabled={loading}
              style={{
                flex: 1, border: "1.5px solid #e2e8f0", borderRadius: 12,
                padding: "9px 12px", fontSize: 13.5, resize: "none",
                fontFamily: "inherit", background: "#f8fafc",
                color: "#1e293b", lineHeight: 1.5,
                transition: "border-color 0.18s, box-shadow 0.18s",
                maxHeight: 80, minHeight: 40
              }}
            />
            <button
              className="cb-send"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{
                width: 40, height: 40, borderRadius: 12, border: "none",
                background: "linear-gradient(135deg,#1976d2,#42a5f5)",
                color: "#fff", cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0, transition: "all 0.18s",
                boxShadow: "0 2px 8px rgba(25,118,210,0.3)"
              }}>
              {loading ? <IconSpin /> : <IconSend />}
            </button>
          </div>

        </div>
      )}
    </>
  );
}