// CustomResponse.jsx
// Open this page in a NEW TAB via: window.open("/custom-response", "_blank")
// Data is passed via localStorage: "generatedReactCode" and "generatedMeta"

import { useEffect, useState } from "react";

const CustomResponse = () => {
  const [reactCode, setReactCode] = useState(null);
  const [meta, setMeta]           = useState(null);
  const [error, setError]         = useState(null);

  
  useEffect(() => {
    const timer = setTimeout(() => {
      const code    = localStorage.getItem("generatedReactCode");
      const metaRaw = localStorage.getItem("generatedMeta");

      if (!code) {
        setError("No visualization data found. Please generate a chart first.");
        return;
      }

      setReactCode(code);
      if (metaRaw) {
        try { setMeta(JSON.parse(metaRaw)); } catch {}
      }
    }, 300);

    return () => clearTimeout(timer);
  }, []);

  /* ── Error ── */
  if (error) {
    return (
      <div style={S.centered}>
        <div style={S.errorBox}>
          <div style={S.errorIcon}>⚠️</div>
          <h3 style={S.errorTitle}>No Data Found</h3>
          <p style={S.errorMsg}>{error}</p>
        </div>
      </div>
    );
  }

  /* ── Loading ── */
  if (!reactCode) {
    return (
      <div style={S.centered}>
        <div style={S.loadingBox}>
          <div style={S.pulse}>📊</div>
          <p style={S.loadingText}>Rendering visualization...</p>
        </div>
      </div>
    );
  }

  /* ── Main ── */
  return (
    <div style={S.page}>
      {/* Slim top bar - schema + question only, no buttons */}
      <div style={S.topBar}>
        <div style={S.topLeft}>
          <span style={S.logo}>📊</span>
          <span style={S.topTitle}>AI Visualization</span>
          {meta?.schema && <span style={S.chip}>🗄 {meta.schema}</span>}
          {meta?.question && (
            <span style={{ ...S.chip, background: "rgba(99,179,237,0.15)", color: "#63b3ed" }}>
              💬 {meta.question}
            </span>
          )}
        </div>
        {meta?.generatedAt && (
          <span style={S.time}>
            {new Date(meta.generatedAt).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Full screen iframe - no padding, edge to edge */}
      <div style={S.iframeWrapper}>
        <iframe
          srcDoc={reactCode}
          title="AI Visualization"
          sandbox="allow-scripts"
          style={S.iframe}
        />
      </div>
    </div>
  );
};

/* ── Styles ── */
const S = {
  page: {
    display:       "flex",
    flexDirection: "column",
    height:        "100vh",
    width:         "100vw",
    overflow:      "hidden",
    background:    "#0f172a",
    fontFamily:    "'Segoe UI', sans-serif",
  },
  topBar: {
    display:        "flex",
    alignItems:     "center",
    justifyContent: "space-between",
    padding:        "10px 20px",
    background:     "#1e293b",
    borderBottom:   "1px solid #334155",
    flexShrink:     0,
    gap:            "12px",
  },
  topLeft: {
    display:    "flex",
    alignItems: "center",
    gap:        "10px",
    flexWrap:   "wrap",
  },
  logo:      { fontSize: "20px" },
  topTitle:  { color: "#f1f5f9", fontWeight: 700, fontSize: "15px" },
  chip: {
    background:   "rgba(148,163,184,0.1)",
    color:        "#94a3b8",
    padding:      "3px 10px",
    borderRadius: "20px",
    fontSize:     "12px",
    border:       "1px solid rgba(148,163,184,0.2)",
  },
  time: {
    color:     "#475569",
    fontSize:  "12px",
    flexShrink: 0,
  },
  iframeWrapper: {
    flex:     1,
    overflow: "hidden",
  },
  iframe: {
    width:   "100%",
    height:  "100%",
    border:  "none",
    display: "block",
  },
  centered: {
    display:        "flex",
    justifyContent: "center",
    alignItems:     "center",
    height:         "100vh",
    background:     "#0f172a",
  },
  loadingBox: {
    textAlign: "center",
    color:     "#94a3b8",
  },
  pulse: {
    fontSize:  "48px",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  loadingText: {
    marginTop: "16px",
    fontSize:  "16px",
    color:     "#64748b",
  },
  errorBox: {
    textAlign:    "center",
    padding:      "40px",
    background:   "#1e293b",
    borderRadius: "16px",
    border:       "1px solid #334155",
    maxWidth:     "400px",
  },
  errorIcon:  { fontSize: "40px", marginBottom: "12px" },
  errorTitle: { color: "#f1f5f9", margin: "0 0 8px", fontSize: "18px" },
  errorMsg:   { color: "#64748b", fontSize: "14px", margin: 0 },
};

export default CustomResponse;
