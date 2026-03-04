// AISuggestions.jsx
// ─────────────────────────────────────────────────────────────────────────────
// Shows 3-5 AI suggestion cards. User clicks one → chart renders below.
// Works with any schema — all driven by data from backend.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from "react";
import {
  Box, Typography, Paper, Chip, CircularProgress, Grid
} from "@mui/material";
import {
  BarChart2, PieChart, TrendingUp, Table2,
  FileText, LayoutDashboard, Activity
} from "lucide-react";
import ChartRenderer from "./ChartRenderer";

// ── Icon map for each chart type ─────────────────────────────────────────────
const CHART_ICONS = {
  bar:   <BarChart2  size={22} />,
  pie:   <PieChart   size={22} />,
  line:  <TrendingUp size={22} />,
  area:  <Activity   size={22} />,
  table: <Table2     size={22} />,
  text:  <FileText   size={22} />,
  card:  <LayoutDashboard size={22} />,
};

// ── Color per chart type ─────────────────────────────────────────────────────
const CHART_COLORS = {
  bar:   { bg: "#eff6ff", border: "#2563eb", icon: "#2563eb" },
  pie:   { bg: "#f0fdf4", border: "#10b981", icon: "#10b981" },
  line:  { bg: "#fdf4ff", border: "#8b5cf6", icon: "#8b5cf6" },
  area:  { bg: "#fff7ed", border: "#f59e0b", icon: "#f59e0b" },
  table: { bg: "#f8fafc", border: "#64748b", icon: "#64748b" },
  text:  { bg: "#fefce8", border: "#ca8a04", icon: "#ca8a04" },
  card:  { bg: "#fff1f2", border: "#ef4444", icon: "#ef4444" },
};

// ── Label for aggregation type ────────────────────────────────────────────────
const AGG_LABEL = {
  count: "Count",
  sum:   "Sum",
  avg:   "Average",
  none:  "Raw",
};


// ─────────────────────────────────────────────────────────────────────────────
// SUGGESTION CARD
// ─────────────────────────────────────────────────────────────────────────────

function SuggestionCard({ suggestion, isSelected, onClick }) {
  const type   = suggestion.chartType || "bar";
  const colors = CHART_COLORS[type] || CHART_COLORS.bar;

  return (
    <Paper
      onClick={onClick}
      elevation={0}
      sx={{
        p: 2.5,
        borderRadius: 3,
        cursor: "pointer",
        border: `2px solid ${isSelected ? colors.border : "#e2e8f0"}`,
        background: isSelected ? colors.bg : "#fff",
        transition: "all 0.2s ease",
        "&:hover": {
          border: `2px solid ${colors.border}`,
          background: colors.bg,
          transform: "translateY(-2px)",
          boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
        },
      }}
    >
      {/* Icon + type badge */}
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
        <Box sx={{ color: colors.icon }}>
          {CHART_ICONS[type] || CHART_ICONS.bar}
        </Box>
        <Box sx={{ display: "flex", gap: 0.5 }}>
          <Chip
            label={type.toUpperCase()}
            size="small"
            sx={{
              fontSize: "0.65rem",
              fontWeight: 700,
              background: colors.border,
              color: "#fff",
              height: 20,
            }}
          />
          {suggestion.aggregation && suggestion.aggregation !== "none" && (
            <Chip
              label={AGG_LABEL[suggestion.aggregation] || suggestion.aggregation}
              size="small"
              sx={{ fontSize: "0.65rem", height: 20, background: "#f1f5f9" }}
            />
          )}
        </Box>
      </Box>

      {/* Title */}
      <Typography
        sx={{
          fontWeight: 700,
          fontSize: "0.9rem",
          color: "#1e293b",
          mb: 0.5,
          lineHeight: 1.3,
        }}
      >
        {suggestion.title}
      </Typography>

      {/* Description */}
      <Typography
        sx={{ fontSize: "0.75rem", color: "#64748b", lineHeight: 1.4 }}
      >
        {suggestion.description}
      </Typography>

      {/* Row count */}
      {suggestion.rowCount > 0 && (
        <Typography
          sx={{ fontSize: "0.7rem", color: "#94a3b8", mt: 1 }}
        >
          {suggestion.rowCount} data point{suggestion.rowCount !== 1 ? "s" : ""}
        </Typography>
      )}
    </Paper>
  );
}


// ─────────────────────────────────────────────────────────────────────────────
// MAIN — AISuggestions
// ─────────────────────────────────────────────────────────────────────────────

function AISuggestions({ suggestions = [], loading = false }) {
  const [selected, setSelected] = useState(null);

  // Auto-select first suggestion when suggestions load
  React.useEffect(() => {
    if (suggestions.length > 0 && !selected) {
      setSelected(suggestions[0]);
    }
  }, [suggestions]);

  // ── Loading state ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <Box sx={{ textAlign: "center", py: 6 }}>
        <CircularProgress size={32} sx={{ color: "#2563eb", mb: 2 }} />
        <Typography sx={{ color: "#64748b", fontSize: "0.9rem" }}>
          AI is analyzing your data...
        </Typography>
      </Box>
    );
  }

  // ── No suggestions yet ─────────────────────────────────────────────────────
  if (!suggestions.length) return null;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 2.5 }}>
        <Typography
          sx={{ fontWeight: 700, fontSize: "1rem", color: "#1e293b", mb: 0.5 }}
        >
          AI Suggestions
        </Typography>
        <Typography sx={{ fontSize: "0.8rem", color: "#64748b" }}>
          {suggestions.length} ways to view your data — click one to render
        </Typography>
      </Box>

      {/* Suggestion cards grid */}
      <Grid container spacing={1.5} sx={{ mb: 3 }}>
        {suggestions.map((s) => (
          <Grid item xs={12} sm={6} md={4} key={s.id}>
            <SuggestionCard
              suggestion={s}
              isSelected={selected?.id === s.id}
              onClick={() => setSelected(s)}
            />
          </Grid>
        ))}
      </Grid>

      {/* Rendered chart for selected suggestion */}
      {selected && (
        <Box>
          {/* Selected suggestion label */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              mb: 2,
              pb: 1.5,
              borderBottom: "1px solid #e2e8f0",
            }}
          >
            <Box sx={{ color: CHART_COLORS[selected.chartType]?.border || "#2563eb" }}>
              {CHART_ICONS[selected.chartType] || CHART_ICONS.bar}
            </Box>
            <Typography sx={{ fontWeight: 700, fontSize: "1rem", color: "#1e293b" }}>
              {selected.title}
            </Typography>
            <Typography sx={{ fontSize: "0.8rem", color: "#64748b" }}>
              — {selected.description}
            </Typography>
          </Box>

          {/* ChartRenderer — passes selected suggestion config directly */}
          {selected.reactCode ? (
  // HTML from viz agent — render in iframe
  <Box sx={{ width: "100%", height: 520, borderRadius: 3, overflow: "hidden" }}>
    <iframe
      srcDoc={selected.reactCode}
      style={{ width: "100%", height: "100%", border: "none" }}
      title={selected.title}
    />
  </Box>
) : (
  // JSON data from ai suggestions — render with ChartRenderer
  <ChartRenderer config={selected} />
)}
        </Box>
      )}
    </Box>
  );
}

export default AISuggestions;
