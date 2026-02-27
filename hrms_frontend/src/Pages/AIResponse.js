// import React, { useEffect, useState } from "react";
// import { DataGrid, GridToolbar } from "@mui/x-data-grid";
// import { processAIConfig } from "../Utils/processAIConfig";
// import { CircularProgress } from "@mui/material";
// import {
//   Card,
//   CardContent,
//   Typography,
//   Box,
//   Divider,
//   Paper
// } from "@mui/material";
// import ChartRenderer from "./ChartRenderer";

// function AIResponse() {
//   const [configs, setConfigs] = useState([]);
//   const [data, setData] = useState([]);
//   const [loading, setLoading] = useState(true);

// //   useEffect(() => {
// //   const savedConfig = localStorage.getItem("aiConfig");
// //   const savedData = localStorage.getItem("aiChartData");

// //   if (savedConfig && savedData) {
// //     const parsed = JSON.parse(savedConfig);

// //     const configArray = parsed.suggestions
// //       ? parsed.suggestions
// //       : Array.isArray(parsed)
// //       ? parsed
// //       : [parsed];

// //     setConfigs(configArray);
// //     setData(JSON.parse(savedData));
// //   }
// // }, []);

// const validateAndFixConfig = (config, data) => {
//   if (!data || !data.length) return config;

//   const dataKeys = Object.keys(data[0]);

//   let updatedConfig = { ...config };

//   // Helper: find closest matching key
//   const findMatchingKey = (wrongKey) => {
//     if (!wrongKey) return null;

//     // Exact match
//     if (dataKeys.includes(wrongKey)) return wrongKey;

//     // Case-insensitive match
//     const lowerMatch = dataKeys.find(
//       key => key.toLowerCase() === wrongKey.toLowerCase()
//     );
//     if (lowerMatch) return lowerMatch;

//     // Partial match (example: count(*) -> number_of_employees)
//     const partialMatch = dataKeys.find(
//       key =>
//         key.toLowerCase().includes(wrongKey.toLowerCase()) ||
//         wrongKey.toLowerCase().includes(key.toLowerCase())
//     );

//     return partialMatch || null;
//   };

//   // Fix xKey
//   if (config.xKey && !dataKeys.includes(config.xKey)) {
//     const matchedX = findMatchingKey(config.xKey);
//     if (matchedX) updatedConfig.xKey = matchedX;
//   }

//   // Fix yKey
//   if (config.yKey && !dataKeys.includes(config.yKey)) {
//     const matchedY = findMatchingKey(config.yKey);
//     if (matchedY) updatedConfig.yKey = matchedY;
//   }

//   // Fix table columns
//   if (config.columns) {
//     updatedConfig.columns = config.columns.map(col => {
//       if (dataKeys.includes(col)) return col;

//       const matched = findMatchingKey(col);
//       return matched || col;
//     });
//   }

//   return updatedConfig;
// };

// // useEffect(() => {
// //   const checkData = () => {
// //     setLoading(true);
// //   setData(null);
// //   setConfigs(null);
// //     const savedData = localStorage.getItem("aiChartData");
// //     const savedConfig = localStorage.getItem("aiConfig");

// //     if (savedData && savedConfig) {
// //       const parsedData = JSON.parse(savedData);
// //       const parsedConfig = JSON.parse(savedConfig);

// //       const configArray = parsedConfig.suggestions || [parsedConfig];

// //       const fixedConfigs = configArray.map(cfg =>
// //         validateAndFixConfig(cfg, parsedData)
// //       );

// //       setData(parsedData);
// //       setConfigs(fixedConfigs);
// //       setLoading(false);

// //       return true;
// //     }
// //     return false;
// //   };

// //   if (!checkData()) {
// //     const interval = setInterval(() => {
// //       if (checkData()) clearInterval(interval);
// //     }, 500);

// //     return () => clearInterval(interval);
// //   }
// // }, []);

// // useEffect(() => {
// //   setLoading(true);

// //   const savedData = localStorage.getItem("aiChartData");
// //   const savedConfig = localStorage.getItem("aiConfig");

// //   if (savedData && savedConfig) {
// //     const parsedData = JSON.parse(savedData);
// //     const parsedConfig = JSON.parse(savedConfig);

// //     const configArray = parsedConfig.suggestions
// //       ? parsedConfig.suggestions
// //       : [parsedConfig];

// //     const fixedConfigs = configArray.map(cfg =>
// //       validateAndFixConfig(cfg, parsedData)
// //     );

// //     setData(parsedData);
// //     setConfigs(fixedConfigs);
// //   } else {
// //     setData([]);
// //     setConfigs([]);
// //   }

// //   setLoading(false);
// // }, []);

// useEffect(() => {
//   setLoading(true);

//   const handleMessage = (event) => {
//     // Security check
//     if (event.origin !== window.location.origin) return;

//     const { config, data, error } = event.data || {};

//     if (error) {
//       setData([]);
//       setConfigs([]);
//       setLoading(false);
//       return;
//     }

//     if (config && data) {
//       const configArray = config.suggestions
//         ? config.suggestions
//         : [config];

//       const fixedConfigs = configArray.map((cfg) =>
//         validateAndFixConfig(cfg, data)
//       );

//       setData(data);
//       setConfigs(fixedConfigs);
//       setLoading(false);
//     }
//   };

//   window.addEventListener("message", handleMessage);

//   return () => {
//     window.removeEventListener("message", handleMessage);
//   };
// }, []);
// if (loading) {
//   return (
//     <Box
//       sx={{
//         height: "100vh",
//         display: "flex",
//         alignItems: "center",
//         justifyContent: "center",
//         flexDirection: "column"
//       }}
//     >
//       <CircularProgress />
//       <Typography sx={{ mt: 2 }}>
//         Preparing AI Insights...
//       </Typography>
//     </Box>
//   );
// }
// if (loading) return <p>Loading AI Response...</p>;

//   if (!data || !configs) return <p>Loading AI Response...</p>;

//   const findBestMatchKey = (aiColumn, row) => {
//   const dataKeys = Object.keys(row);

//   // normalize function
//   const normalize = (str) =>
//     str.toLowerCase().replace(/[^a-z0-9]/g, "");

//   const normalizedAi = normalize(aiColumn);

//   // 1️⃣ Exact match
//   if (dataKeys.includes(aiColumn)) return aiColumn;

//   // 2️⃣ Normalized exact match
//   for (let key of dataKeys) {
//     if (normalize(key) === normalizedAi) return key;
//   }

//   // 3️⃣ Partial match (includes)
//   for (let key of dataKeys) {
//     if (
//       normalize(key).includes(normalizedAi) ||
//       normalizedAi.includes(normalize(key))
//     ) {
//       return key;
//     }
//   }

//   return null; // no match found
// };


//   // Dynamically generate table columns from raw data
//   const allColumns =
//     data && data.length > 0 ? Object.keys(data[0]) : [];

//   return (
//     <Box sx={{ padding: 4 }}>

//       {/* ================= AI CONFIG SECTION ================= */}
//       <Paper sx={{ p: 3, mb: 5, borderRadius: 4,background: "#f4f6f9",
//     boxShadow: "0 12px 30px rgba(0,0,0,0.06)"}} elevation={3}>
//         <Typography variant="h6"
//     sx={{
//       mb: 3,
//       fontWeight: 700,
//       color: "#0f172a",
//       letterSpacing: 0.5
//     }}>
//         </Typography>

//         {/* CHART VIEW */}
//        {configs.map((config, index) => (
//   <Paper
//     key={index}
//     sx={{
//       p: 3,
//       mb: 5,
//       borderRadius: 4,
//       background: "#f4f6f9",
//       boxShadow: "0 12px 30px rgba(0,0,0,0.06)"
//     }}
//   >
//     <Typography variant="h6" sx={{ mb: 3, fontWeight: 700 }}>
//       {config.title}
//     </Typography>

//     {/* CHART */}
//     {config.viewType === "chart" && (
//       <ChartRenderer
//         config={config}
//         data={data}
//       />
//     )}

//     {/* CARD */}
//     {config.viewType === "card" && (
//       <Card>
//         <CardContent>
//           <Typography variant="subtitle2">
//             {config.metric}
//           </Typography>
//           <Typography variant="h4">
//             {data.length}
//           </Typography>
//         </CardContent>
//       </Card>
//     )}

//     {/* TABLE */}
//     {config.viewType === "table" && (
//       <Box sx={{ overflowX: "auto" }}>
//         <table border="1" cellPadding="10" width="100%">
//           <thead>
//             <tr>
//               {config.columns.map((col) => (
//                 <th key={col}>{col}</th>
//               ))}
//             </tr>
//           </thead>
//           <tbody>
//             {data.map((row, i) => (
//               <tr key={i}>
//                 {config.columns.map((col) => {
//   const matchedKey = findBestMatchKey(col, row);
//   return (
//     <td key={col}>
//       {matchedKey ? row[matchedKey] : "-"}
//     </td>
//   );
// })}
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </Box>
//     )}
//   </Paper>
// ))}
//       </Paper>

//       {/* ================= RAW DATA SECTION ================= */}
// <Paper
//   elevation={0}
//   sx={{
//     p: 4,
//     borderRadius: 4,
//     background: "#f4f6f9",
//     boxShadow: "0 12px 30px rgba(0,0,0,0.06)"
//   }}
// >
//   <Typography
//     variant="h6"
//     sx={{
//       mb: 3,
//       fontWeight: 700,
//       color: "#0f172a",
//       letterSpacing: 0.5
//     }}
//   >
//     Query Generate Data
//   </Typography>

//   <Box
//     sx={{
//       height: 600,
//       width: "100%",
//       borderRadius: 3,
//       overflow: "hidden",
//       backgroundColor: "#e90707",
//       boxShadow: "0 8px 24px rgba(0,0,0,0.05)"
//     }}
//   >
//     <DataGrid
//       rows={data.map((row, index) => ({
//         id: row.id || index,
//         ...row
//       }))}
//       columns={
//         data && data.length > 0
//           ? Object.keys(data[0]).map((key) => ({
//               field: key,
//               headerName: key.replaceAll("_", " "),
//               flex: 1,
//               minWidth: 150,
//               sortable: true,
//               headerAlign: "left",
//               align: "left"
//             }))
//           : []
//       }
//       pageSizeOptions={[5, 10, 20, 50]}
//       initialState={{
//         pagination: {
//           paginationModel: { pageSize: 10, page: 0 }
//         }
//       }}
//       disableRowSelectionOnClick
//       slots={{ toolbar: GridToolbar }}
//       sx={{
//         border: "none",
//         fontSize: "0.9rem",

//         /* HEADER DESIGN */
//         "& .MuiDataGrid-columnHeaders": {
//           backgroundColor: "#1976d2",
//           color: "#4454b8",
//           fontSize: "0.95rem",
//           fontWeight: 600,
//           minHeight: "56px !important"
//         },

//         "& .MuiDataGrid-columnHeaderTitle": {
//           fontWeight: 600,
//           whiteSpace: "nowrap"
//         },

//         "& .MuiDataGrid-iconSeparator": {
//           display: "none"
//         },

//         "& .MuiDataGrid-sortIcon": {
//           color: "#ffffff"
//         },

//         /* ROW DESIGN */
//         "& .MuiDataGrid-row": {
//           minHeight: "52px !important"
//         },

//         "& .MuiDataGrid-cell": {
//           borderBottom: "1px solid #f1f5f9"
//         },

//         "& .MuiDataGrid-row:nth-of-type(even)": {
//           backgroundColor: "#f8fafc"
//         },

//         "& .MuiDataGrid-row:hover": {
//           backgroundColor: "#e3f2fd"
//         },

//         /* FOOTER */
//         "& .MuiDataGrid-footerContainer": {
//           backgroundColor: "#f9fafb",
//           borderTop: "1px solid #e5e7eb"
//         },

//         /* TOOLBAR */
//         "& .MuiDataGrid-toolbarContainer": {
//           padding: "12px 16px",
//           backgroundColor: "#f1f5f9",
//           borderBottom: "1px solid #e5e7eb"
//         }
//       }}
//     />
//   </Box>
// </Paper>

//     </Box>
//   );
// }

// export default AIResponse;



import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Card, CardContent, CircularProgress } from "@mui/material";
import ChartRenderer from "./ChartRenderer";

function AIResponse() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleMessage = (event) => {
      // Security check
      if (event.origin !== window.location.origin) return;

      const { configs: receivedConfigs, error } = event.data || {};

      if (error) {
        setConfigs([]);
        setLoading(false);
        return;
      }

      if (receivedConfigs && Array.isArray(receivedConfigs)) {
        setConfigs(receivedConfigs);
        setLoading(false);
      }
    };

    window.addEventListener("message", handleMessage);

    return () => {
      window.removeEventListener("message", handleMessage);
    };
  }, []);

  if (loading) {
    return (
      <Box
        sx={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column"
        }}
      >
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Preparing AI Insights...</Typography>
      </Box>
    );
  }

  if (!configs.length) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>No AI suggestions available.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 4 }}>
      {configs.map((config, index) => (
        <Paper
          key={index}
          sx={{
            p: 3,
            mb: 5,
            borderRadius: 4,
            background: "#f4f6f9",
            boxShadow: "0 12px 30px rgba(0,0,0,0.06)"
          }}
        >
          <Typography variant="h6" sx={{ mb: 3, fontWeight: 700 }}>
            {config.title}
          </Typography>

          {/* CHART */}
          {config.viewType === "chart" && <ChartRenderer config={config} />}

          {/* CARD */}
          {config.viewType === "card" && (
            <Card>
              <CardContent>
                <Typography variant="subtitle2">{config.metric || config.operation}</Typography>
                <Typography variant="h4">{config.value ?? "-"}</Typography>
              </CardContent>
            </Card>
          )}

          {/* TABLE */}
          {config.viewType === "table" && (
            <Box sx={{ overflowX: "auto" }}>
              <table border="1" cellPadding="10" width="100%">
                <thead>
                  <tr>
                    {config.columns?.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {config.data?.map((row, i) => (
                    <tr key={i}>
                      {config.columns?.map((col) => (
                        <td key={col}>{row[col] ?? "-"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          )}
        </Paper>
      ))}
    </Box>
  );
}

export default AIResponse;