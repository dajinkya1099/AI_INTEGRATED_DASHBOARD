// import React from "react";
// import {
//   LineChart,
//   Line,
//   BarChart,
//   Bar,
//   PieChart,
//   Pie,
//   AreaChart,
//   Area,
//   XAxis,
//   YAxis,
//   Tooltip,
//   CartesianGrid,
//   ResponsiveContainer,
//   Legend,
//   Cell
// } from "recharts";
// import { Box, Paper, Typography } from "@mui/material";

// const COLORS = [
//   "#2563eb",
//   "#0ea5e9",
//   "#10b981",
//   "#f59e0b",
//   "#ef4444",
//   "#8b5cf6"
// ];

// const CustomTooltip = ({ active, payload, label }) => {
//   if (active && payload && payload.length) {
//     return (
//       <Box
//         sx={{
//           background: "#ffffff",
//           padding: 2,
//           borderRadius: 2,
//           boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
//           fontSize: "0.85rem"
//         }}
//       >
//         <Typography variant="subtitle2">{label}</Typography>
//         <Typography variant="body2" sx={{ fontWeight: 600 }}>
//           {payload[0].value}
//         </Typography>
//       </Box>
//     );
//   }
//   return null;
// };

// function ChartRenderer({ config, data }) {
//   if (!config || !data || data.length === 0) {
//     return <p>No chart data available</p>;
//   }

//   const { chartType, xKey, yKey, title } = config;

//   return (
//     <Paper
//       elevation={0}
//       sx={{
//         p: 4,
//         borderRadius: 4,
//         background: "#ffffff",
//         boxShadow: "0 12px 30px rgba(0,0,0,0.06)",
//         height: 480
//       }}
//     >
//       <Typography
//         variant="h6"
//         sx={{ mb: 3, fontWeight: 600, color: "#0f172a" }}
//       >
//         {title}
//       </Typography>

//       <ResponsiveContainer width="100%" height="85%">

//         {/* ================= LINE CHART ================= */}
//         {chartType === "line" && (
//           <LineChart data={data}>
//             <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
//             <XAxis dataKey={xKey} tick={{ fill: "#64748b" }} />
//             <YAxis tick={{ fill: "#64748b" }} />
//             <Tooltip content={<CustomTooltip />} />
//             <Legend />
//             <Line
//               type="monotone"
//               dataKey={yKey}
//               stroke="#2563eb"
//               strokeWidth={3}
//               dot={{ r: 4 }}
//             />
//           </LineChart>
//         )}

//         {/* ================= BAR CHART ================= */}
//         {chartType === "bar" && (
//           <BarChart data={data}>
//             <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
//             <XAxis dataKey={xKey} tick={{ fill: "#64748b" }} />
//             <YAxis tick={{ fill: "#64748b" }} />
//             <Tooltip content={<CustomTooltip />} />
//             <Legend />
//             <Bar
//               dataKey={yKey}
//               radius={[8, 8, 0, 0]}
//               fill="#2563eb"
//             />
//           </BarChart>
//         )}

//         {/* ================= AREA CHART ================= */}
//         {chartType === "area" && (
//           <AreaChart data={data}>
//             <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
//             <XAxis dataKey={xKey} tick={{ fill: "#64748b" }} />
//             <YAxis tick={{ fill: "#64748b" }} />
//             <Tooltip content={<CustomTooltip />} />
//             <Legend />
//             <Area
//               type="monotone"
//               dataKey={yKey}
//               stroke="#0ea5e9"
//               fill="#bfdbfe"
//               strokeWidth={3}
//             />
//           </AreaChart>
//         )}

//         {/* ================= PIE CHART ================= */}
//         {chartType === "pie" && (() => {

//           let pieData = data;

//           if (!yKey && xKey) {
//             const grouped = {};
//             data.forEach(item => {
//               const key = item[xKey];
//               if (key) {
//                 grouped[key] = (grouped[key] || 0) + 1;
//               }
//             });

//             pieData = Object.keys(grouped).map(key => ({
//               [xKey]: key,
//               count: grouped[key]
//             }));
//           }

//           return (
//             <PieChart>
//               <Tooltip content={<CustomTooltip />} />
//               <Legend />
//               <Pie
//                 data={pieData}
//                 dataKey={yKey || "count"}
//                 nameKey={xKey}
//                 outerRadius={150}
//                 innerRadius={60}
//                 paddingAngle={4}
//               >
//                 {pieData.map((entry, index) => (
//                   <Cell
//                     key={`cell-${index}`}
//                     fill={COLORS[index % COLORS.length]}
//                   />
//                 ))}
//               </Pie>
//             </PieChart>
//           );
//         })()}

//       </ResponsiveContainer>
//     </Paper>
//   );
// }

// export default ChartRenderer;




















// ChartRenderer.js  (updated)
// ─────────────────────────────────────────────────────────────────────────────
// Handles two render modes:
//
//   Mode 1 — AI Suggestion (config.data exists, Recharts renders directly)
//     config = { chartType, xKey, yKey, data: [...], title, description }
//
//   Mode 2 — Viz Agent HTML (config.reactCode exists, renders in iframe)
//     config = { reactCode: "<html>...</html>", outputType }
//
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie,
  AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Legend, Cell
} from "recharts";
import { Box, Typography, Paper } from "@mui/material";

const COLORS = ["#2563eb","#0ea5e9","#10b981","#f59e0b","#ef4444","#8b5cf6","#f97316","#84cc16"];

// ── Custom Tooltip ─────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <Box sx={{
        background: "#fff", padding: 2, borderRadius: 2,
        boxShadow: "0 6px 18px rgba(0,0,0,0.08)", fontSize: "0.85rem"
      }}>
        <Typography variant="subtitle2">{label}</Typography>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {payload[0].value?.toLocaleString?.() ?? payload[0].value}
        </Typography>
      </Box>
    );
  }
  return null;
};


// ── Table renderer (for chartType = "table") ──────────────────────────────────
function TableView({ data }) {
  if (!data || !data.length) return <Typography>No data</Typography>;
  const cols = Object.keys(data[0]);

  return (
    <Box sx={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
        <thead>
          <tr>
            {cols.map(col => (
              <th key={col} style={{
                padding: "8px 12px", textAlign: "left",
                background: "#f8fafc", borderBottom: "2px solid #e2e8f0",
                fontWeight: 700, color: "#374151",
                whiteSpace: "nowrap"
              }}>
                {col.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? "#fff" : "#f8fafc" }}>
              {cols.map(col => (
                <td key={col} style={{
                  padding: "7px 12px", borderBottom: "1px solid #e2e8f0", color: "#374151"
                }}>
                  {row[col] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  );
}


// ── Text/Summary renderer (for chartType = "text" or "card") ─────────────────
// function StatsView({ data }) {
//   if (!data || !data.length) return <Typography>No data</Typography>;

//   return (
//     <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2 }}>
//       {data.map((item, i) => (
//         <Paper key={i} elevation={0} sx={{
//           p: 2, borderRadius: 2, minWidth: 140, flex: "1 1 140px",
//           background: "#f8fafc", border: "1px solid #e2e8f0"
//         }}>
//           <Typography sx={{ fontSize: "0.72rem", color: "#64748b", mb: 0.5, fontWeight: 600 }}>
//             {item.metric}
//           </Typography>
//           <Typography sx={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b" }}>
//             {typeof item.value === "number"
//               ? item.value.toLocaleString()
//               : item.value}
//           </Typography>
//         </Paper>
//       ))}
//     </Box>
//   );
// }

function StatsView({ data, chartType }) {
  if (!data || !data.length) return <Typography>No data</Typography>;

  // Separate metric cards from text items
  const metrics = data.filter(d => d.metric && d.value !== undefined);

  return (
    <Box>
      {/* Stat Cards */}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, mb: 3 }}>
        {metrics.map((item, i) => (
          <Paper key={i} elevation={0} sx={{
            p: 2, borderRadius: 2, minWidth: 140, flex: "1 1 140px",
            background: "#f8fafc", border: "1px solid #e2e8f0"
          }}>
            <Typography sx={{ fontSize: "0.72rem", color: "#64748b", mb: 0.5, fontWeight: 600 }}>
              {item.metric}
            </Typography>
            <Typography sx={{ fontSize: "1.1rem", fontWeight: 700, color: "#1e293b" }}>
              {typeof item.value === "number"
                ? item.value.toLocaleString()
                : item.value}
            </Typography>
          </Paper>
        ))}
      </Box>

      {/* Text paragraph — only for "text" type */}
      {chartType === "text" && metrics.length > 0 && (
        <Paper elevation={0} sx={{
          p: 2.5, borderRadius: 2,
          background: "#eff6ff",
          border: "1px solid #bfdbfe"
        }}>
          <Typography sx={{ fontSize: "0.82rem", color: "#1e40af", fontWeight: 700, mb: 1 }}>
            📊 Summary
          </Typography>
          <Typography sx={{ fontSize: "0.82rem", color: "#374151", lineHeight: 1.7 }}>
            {metrics.map(m => `${m.metric}: ${m.value}`).join("  ·  ")}
          </Typography>
        </Paper>
      )}
    </Box>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN — ChartRenderer
// ─────────────────────────────────────────────────────────────────────────────

function ChartRenderer({ config }) {
  if (!config) return null;

  // ── MODE 2: Viz agent returned full HTML → render in iframe ───────────────
  if (config.reactCode) {
    return (
      <Paper elevation={0} sx={{
        borderRadius: 4, overflow: "hidden",
        boxShadow: "0 12px 30px rgba(0,0,0,0.06)", height: 520
      }}>
        <iframe
          srcDoc={config.reactCode}
          style={{ width: "100%", height: "100%", border: "none" }}
          title="Visualization"
        />
      </Paper>
    );
  }

  // ── MODE 1: AI Suggestion — Recharts renders from config.data ─────────────
  const { chartType, xKey, yKey, data: rawData = [], title } = config;

  if (!rawData.length) {
    return (
      <Paper elevation={0} sx={{ p: 4, borderRadius: 4, textAlign: "center" }}>
        <Typography color="text.secondary">No data available</Typography>
      </Paper>
    );
  }

  // TABLE
  if (chartType === "table") {
    return (
      <Paper elevation={0} sx={{
        p: 3, borderRadius: 4,
        boxShadow: "0 12px 30px rgba(0,0,0,0.06)"
      }}>
        <TableView data={rawData} />
      </Paper>
    );
  }

  // TEXT / CARD
  if (chartType === "text" || chartType === "card") {
    return (
      <Paper elevation={0} sx={{
        p: 3, borderRadius: 4,
        boxShadow: "0 12px 30px rgba(0,0,0,0.06)"
      }}>
         <StatsView data={rawData} chartType={chartType} /> 
      </Paper>
    );
  }

  // PIE — data comes as [{name, value}]
  if (chartType === "pie") {
    return (
      <Paper elevation={0} sx={{
        p: 4, borderRadius: 4,
        boxShadow: "0 12px 30px rgba(0,0,0,0.06)",
        height: 420
      }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Pie
              data={rawData}
              dataKey="value"
              nameKey="name"
              outerRadius={150}
              innerRadius={60}
              paddingAngle={4}
            >
              {rawData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </Paper>
    );
  }

  // BAR / LINE / AREA — data comes as [{xKey: ..., yKey: ...}]
  // Detect actual y key from data (might be total_xxx or avg_xxx)
  const actualYKey = yKey && rawData[0]?.[yKey] !== undefined
    ? yKey
    : Object.keys(rawData[0] || {}).find(k => k !== xKey) || yKey;

  const actualXKey = xKey && rawData[0]?.[xKey] !== undefined
    ? xKey
    : Object.keys(rawData[0] || {})[0] || xKey;

  const labelAngle  = rawData.length > 6 ? -35 : 0;
  const labelAnchor = rawData.length > 6 ? "end" : "middle";
  const marginBottom = rawData.length > 6 ? 80 : 40;

  return (
    <Paper elevation={0} sx={{
      p: 4, borderRadius: 4,
      boxShadow: "0 12px 30px rgba(0,0,0,0.06)",
      height: 420
    }}>
      <ResponsiveContainer width="100%" height="100%">

        {chartType === "bar" && (
          <BarChart data={rawData} margin={{ bottom: marginBottom }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
            <XAxis
              dataKey={actualXKey}
              angle={labelAngle}
              textAnchor={labelAnchor}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey={actualYKey} radius={[8, 8, 0, 0]} maxBarSize={80}>
              {rawData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        )}

        {chartType === "line" && (
          <LineChart data={rawData} margin={{ bottom: marginBottom }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
            <XAxis dataKey={actualXKey} angle={labelAngle} textAnchor={labelAnchor} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line type="monotone" dataKey={actualYKey} stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} />
          </LineChart>
        )}

        {chartType === "area" && (
          <AreaChart data={rawData} margin={{ bottom: marginBottom }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
            <XAxis dataKey={actualXKey} angle={labelAngle} textAnchor={labelAnchor} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area type="monotone" dataKey={actualYKey} stroke="#0ea5e9" fill="#bfdbfe" strokeWidth={3} />
          </AreaChart>
        )}

      </ResponsiveContainer>
    </Paper>
  );
}

export default ChartRenderer;