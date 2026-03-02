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

import React from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie,
  AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, Legend, Cell
} from "recharts";
import { Box, Typography, Paper } from "@mui/material";

const COLORS = ["#2563eb","#0ea5e9","#10b981","#f59e0b","#ef4444","#8b5cf6"];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <Box sx={{ background: "#fff", padding: 2, borderRadius: 2, boxShadow: "0 6px 18px rgba(0,0,0,0.08)", fontSize: "0.85rem" }}>
        <Typography variant="subtitle2">{label}</Typography>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>{payload[0].value}</Typography>
      </Box>
    );
  }
  return null;
};

function ChartRenderer({ config }) {

  if (!config) return null;
  const { chartType, xKey, yKey, title } = config;

  const rawData = config.data || [];

  let data = [];

if (chartType === "pie") {
  // Pie already comes in correct format
  data = rawData;
} else {
  // Bar / Line / Area format conversion
  data = rawData.map((item) => ({
    [xKey]: item.x,
    [yKey]: item.y
  }));
}

  if (!data.length) {
    return <Typography>No chart data available</Typography>;
  }

  return (
    <Paper elevation={0} sx={{ p: 4, borderRadius: 4, background: "#fff", boxShadow: "0 12px 30px rgba(0,0,0,0.06)", height: 480 }}>
      <ResponsiveContainer width="100%" height="85%">
        {chartType === "line" && <LineChart data={data}>
          <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke="#2563eb" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>}

        {chartType === "bar" && <BarChart data={data}>
          <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Bar dataKey={yKey} radius={[8, 8, 0, 0]}>
      {data.map((entry, index) => (
        <Cell
          key={`cell-${index}`}
          fill={COLORS[index % COLORS.length]}
        />
      ))}
    </Bar>
        </BarChart>}

        {chartType === "area" && <AreaChart data={data}>
          <CartesianGrid stroke="#e5e7eb" strokeDasharray="4 4" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Area type="monotone" dataKey={yKey} stroke="#0ea5e9" fill="#bfdbfe" strokeWidth={3} />
        </AreaChart>}

        {/* {chartType === "pie" && <PieChart>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Pie data={data} dataKey={yKey} nameKey={xKey} outerRadius={150} innerRadius={60} paddingAngle={4}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>} */}

        {chartType === "pie" && (
  <PieChart width={400} height={400}>
    <Tooltip content={<CustomTooltip />} />
    <Legend />
    <Pie
      data={data}
      dataKey="value"
      nameKey="name"
      outerRadius={150}
      innerRadius={60}
      paddingAngle={4}
    >
      {data.map((entry, index) => (
        <Cell
          key={`cell-${index}`}
          fill={COLORS[index % COLORS.length]}
        />
      ))}
    </Pie>
  </PieChart>
)}

        {(!data || data.length === 0) && <Typography>No chart data available</Typography>}
      </ResponsiveContainer>
    </Paper>
  );
}

export default ChartRenderer;