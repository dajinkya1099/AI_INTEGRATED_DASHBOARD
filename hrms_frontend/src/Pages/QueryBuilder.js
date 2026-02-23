import React, { useState, useEffect } from "react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coy } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { okaidia } from "react-syntax-highlighter/dist/esm/styles/prism";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { DataGrid } from "@mui/x-data-grid";
import { SnackbarProvider, useSnackbar } from "notistack";
import CircularProgress from "@mui/material/CircularProgress";
import DownloadIcon from "@mui/icons-material/Download";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import { modernSelectStyle, menuItemStyle, selectMenuProps } from "../Styles/FormStyles";
import Tooltip from "@mui/material/Tooltip";
import WorkIcon from "@mui/icons-material/Work";
import PeopleIcon from "@mui/icons-material/People";
import AssessmentIcon from "@mui/icons-material/Assessment";
import PaymentsIcon from "@mui/icons-material/Payments";
import BusinessIcon from "@mui/icons-material/Business";

import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Radio,
  RadioGroup,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  TextField,
  Collapse,
  Button,
  IconButton,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

export default function QueryBuilder() {

  /* ---------------- SAMPLE DATA ---------------- */


  /* ---------------- STATE ---------------- */

  const [selectedSchema, setSelectedSchema] = useState("");
  const [selectedTable, setSelectedTable] = useState("");
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [aggregates, setAggregates] = useState({});
  const [whereConditions, setWhereConditions] = useState([]);
  const [havingConditions, setHavingConditions] = useState([]);
  const [groupBy, setGroupBy] = useState([]);
  const [orderBy, setOrderBy] = useState([]);
  const [limit, setLimit] = useState("");
  const [generatedQuery, setGeneratedQuery] = useState("");
  const [copied, setCopied] = useState(false);
  const [queryResult, setQueryResult] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const [schemas, setSchemas] = useState([]);
const [schemaData, setSchemaData] = useState(null); // stores full schema JSON
const [joinTable, setJoinTable] = useState("");
const [joinType, setJoinType] = useState("INNER JOIN");
const [joinCondition, setJoinCondition] = useState("");
const [autoJoinConditions, setAutoJoinConditions] = useState([]);
const [useCustomJoin, setUseCustomJoin] = useState(false);
const [availableColumns, setAvailableColumns] = useState([]);
const [openDialog, setOpenDialog] = useState(false);
const [formValue, setFormValue] = useState("");
const [columnSearch, setColumnSearch] = useState("");
const [inputMode, setInputMode] = useState("query"); 
const [manualQuestion, setManualQuestion] = useState("");
const [placeholderText, setPlaceholderText] = useState("");
const [errorMsg, setErrorMsg] = useState("");
 const [aiLoading, setAiLoading] = useState(false);

console.log("style",modernSelectStyle);
  const rowsPerPage = 4;

  useEffect(() => {
  fetch("http://localhost:8282/schemas")
    .then((res) => res.json())
    .then((data) => {
      console.log("Schemas:", data);
      setSchemas(data.schemas || []);
    })
    .catch((err) => {
      console.error("Error fetching schemas:", err);
    });
}, []);

useEffect(() => {
  if (!selectedTable || !joinTable || !schemaData?.tables) return;

  const mainTableObj = schemaData.tables.find(
    (t) => t.name === selectedTable
  );

  const joinTableObj = schemaData.tables.find(
    (t) => t.name === joinTable
  );

  let detectedConditions = [];

  // Check FK in main table
  mainTableObj?.columns?.forEach((col) => {
    col.constraints?.forEach((c) => {
      if (
        c.type === "FOREIGN KEY" &&
        c.references?.table === joinTable
      ) {
        detectedConditions.push(
          `${selectedTable}.${col.name} = ${joinTable}.${c.references.column}`
        );
      }
    });
  });

  // Check FK in join table
  joinTableObj?.columns?.forEach((col) => {
    col.constraints?.forEach((c) => {
      if (
        c.type === "FOREIGN KEY" &&
        c.references?.table === selectedTable
      ) {
        detectedConditions.push(
          `${joinTable}.${col.name} = ${selectedTable}.${c.references.column}`
        );
      }
    });
  });

  setAutoJoinConditions(detectedConditions);
  setJoinCondition("");
  setUseCustomJoin(false);

}, [selectedTable, joinTable, schemaData]);

useEffect(() => {
  if (!schemaData?.tables) return;

  const getColumnsFromTable = (tableName) => {
    const tableObj = schemaData.tables.find(t => t.name === tableName);
    if (!tableObj?.columns) return [];

    return tableObj.columns.map(col => ({
      label: `${tableName}.${col.name}`,
      value: `${tableName}.${col.name}`
    }));
  };

  const mainCols = selectedTable ? getColumnsFromTable(selectedTable) : [];
  const joinCols = joinTable ? getColumnsFromTable(joinTable) : [];

  setAvailableColumns([...mainCols, ...joinCols]);

}, [selectedTable, joinTable, schemaData]);

const handleRunQuery = async () => {
  if (!generatedQuery || !selectedSchema) return;
console.log("Selected Schema:", selectedSchema);
  console.log("Generated Query:", generatedQuery);
  setLoading(true);

  try {
    const response = await fetch(
      "http://localhost:8282/get-db-level-data-by-schemaName-and-query",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          schemaName: selectedSchema,
          query: generatedQuery,
          textQue: "",
          dbJsonData: ""
        })
      }
    );
    console.log("Raw Response:", response);
    const data = await response.json();
    console.log("Backend Data:", data);

    if (data.error) {
      enqueueSnackbar(data.error, { variant: "error" });
      setQueryResult([]);
    } else {
       setQueryResult(data.rows || []); 
      enqueueSnackbar("Query executed successfully!", {
        variant: "success"
      });
    }

  } catch (error) {
    console.error("Error executing query:", error);
    enqueueSnackbar("Backend connection failed!", {
      variant: "error"
    });
  }

  setLoading(false);
};

  /* ---------------- HELPERS ---------------- */

  const handleColumnCheck = (col) => {
    if (selectedColumns.includes(col)) {
      setSelectedColumns(selectedColumns.filter((c) => c !== col));
    } else {
      setSelectedColumns([...selectedColumns, col]);
    }
  };

  const addCondition = (setter, conditions) => {
    setter([
      ...conditions,
      { column: "", operator: "=", value: "", condition: "AND" }
    ]);
  };

  const removeCondition = (setter, conditions, index) => {
    const updated = [...conditions];
    updated.splice(index, 1);
    setter(updated);
  };

  const addGroupBy = () => {
    setGroupBy([...groupBy, ""]);
  };

  const addOrderBy = () => {
    setOrderBy([...orderBy, { column: "", direction: "ASC" }]);
  };

  /* ---------------- GENERATE QUERY ---------------- */

  const generateQuery = () => {
    if (!selectedTable) return;

    let selectClause =
      selectedColumns.length > 0
        ? selectedColumns
            .map((col) =>
              aggregates[col] ? `${aggregates[col]}(${col})` : col
            )
            .join(", ")
        : "*";

    let query = `SELECT ${selectClause} FROM ${selectedTable}`;

    if (joinTable && joinCondition) {
  query += ` ${joinType} ${joinTable} ON ${joinCondition}`;
}

    const buildClause = (conditions) =>
      conditions
        .map((cond, index) => {
          const value = isNaN(cond.value)
            ? `'${cond.value}'`
            : cond.value;
          const clause = `${cond.column} ${cond.operator} ${value}`;
          return index < conditions.length - 1
            ? clause + ` ${cond.condition} `
            : clause;
        })
        .join("");

    if (whereConditions.length > 0 && whereConditions[0].column) {
      query += ` WHERE ${buildClause(whereConditions)}`;
    }

    if (groupBy.length > 0 && groupBy[0]) {
      query += ` GROUP BY ${groupBy.filter(Boolean).join(", ")}`;
    }

    if (havingConditions.length > 0 && havingConditions[0].column) {
      query += ` HAVING ${buildClause(havingConditions)}`;
    }

    if (orderBy.length > 0 && orderBy[0].column) {
      const orderClause = orderBy
        .map((o) => `${o.column} ${o.direction}`)
        .join(", ");
      query += ` ORDER BY ${orderClause}`;
    }

    if (limit) {
      query += ` LIMIT ${limit}`;
    }

    setGeneratedQuery(query + ";");
  };

  const clearAll = () => {
    setSelectedSchema("");
    setSelectedTable("");
    setJoinTable("");
    setSelectedColumns([]);
    setAggregates({});
    setWhereConditions([]);
    setHavingConditions([]);
    setGroupBy([]);
    setOrderBy([]);
    setLimit("");
    setGeneratedQuery("");
    setQueryResult([]); 
  };
   const hasAggregate = Object.values(aggregates).some(val => val);
   const aggregateColumns = selectedColumns.filter(
  (col) => aggregates[col]
);

const downloadPDF = () => {
  const doc = new jsPDF("landscape"); // 👈 landscape for many columns

  if (!queryResult || queryResult.length === 0) return;

  const columns = Object.keys(queryResult[0]);

  const rows = queryResult.map(row =>
    columns.map(col => row[col])
  );

  autoTable(doc, {
    head: [columns],
    body: rows,
    styles: {
      fontSize: 8
    },
    headStyles: {
      fillColor: [25, 118, 210]
    }
  });

  doc.save("query_result.pdf");
};

const downloadExcel = () => {
  if (queryResult.length === 0) return;

  const worksheet = XLSX.utils.json_to_sheet(queryResult);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Results");

  const excelBuffer = XLSX.write(workbook, {
    bookType: "xlsx",
    type: "array"
  });

  const data = new Blob([excelBuffer], {
    type:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8"
  });

  saveAs(data, "query_result.xlsx");
};

const selectedTableData = schemaData?.tables?.find(
  (table) => table.name === selectedTable
);

const columns = selectedTableData?.columns || [];
const renderTableColumns = (tableName) => {
  const tableObj = schemaData?.tables?.find(
    (t) => t.name === tableName
  );

  if (!tableObj?.columns) return null;

  return (
    <Box mb={4}>
      {/* Table Header */}
      <Typography
        mb={3}
        fontWeight="600"
        fontSize={16}
        sx={{
          px: 2,
          py: 1,
          borderRadius: 2,
          background: "#f4f6f8",
          color: "#333",
          display: "inline-block"
        }}
      >
        {tableName} Columns
      </Typography>

      <Box
  sx={{
    display: "grid",
    gridTemplateColumns: {
      xs: "1fr",
      md: "1fr 1fr"   // Exactly 2 equal columns
    },
    gap: 3,
    maxWidth: 900,
    margin: "0 auto",
    alignItems: "stretch"
  }}
>
  {tableObj.columns
    .filter((colObj) =>
      colObj.name.toLowerCase().includes(columnSearch.toLowerCase())
    )
    .map((colObj) => {
      const fullName = `${tableName}.${colObj.name}`;
      const isSelected = selectedColumns.includes(fullName);

      return (
        <Box
          key={fullName}
          sx={{
            width: 150,
            height: "auto",              // FIXED HEIGHT (important)
            p: 1,
            borderRadius: 3,
            background: "#ffffff",
            border: isSelected
              ? "1px solid #1976d2"
              : "1px solid #e6edf5",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            transition: "all 0.25s ease",
            "&:hover": {
              boxShadow: "0 8px 20px rgba(0,0,0,0.08)",
              transform: "translateY(-3px)"
            }
          }}
        >
          {/* Top Section */}
          <Box display="flex" alignItems="flex-start" gap={1}>
            <Checkbox
              size="small"
              checked={isSelected}
              onChange={() => handleColumnCheck(fullName)}
            />

            <Box sx={{ overflow: "hidden" }}>
              <Typography
                fontWeight={600}
                fontSize={14}
                sx={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical"
                }}
              >
                {colObj.name}
              </Typography>

              <Typography fontSize={11} color="text.secondary">
                {colObj.type}
              </Typography>
            </Box>
          </Box>

          {/* Aggregate Dropdown */}
          {isSelected ? (
            <Select
              fullWidth
              size="small"
              value={aggregates[fullName] || ""}
              sx={{
                borderRadius: 2,
                background: "#f8fafc"
              }}
              onChange={(e) =>
                setAggregates({
                  ...aggregates,
                  [fullName]: e.target.value || null
                })
              }
            >
              <MenuItem value="">No Aggregate</MenuItem>
              <MenuItem value="SUM">SUM</MenuItem>
              <MenuItem value="AVG">AVG</MenuItem>
              <MenuItem value="COUNT">COUNT</MenuItem>
              <MenuItem value="MAX">MAX</MenuItem>
              <MenuItem value="MIN">MIN</MenuItem>
            </Select>
          ) : (
            <Box height={40} />  // placeholder keeps height equal
          )}
        </Box>
      );
    })}
</Box>
    </Box>
  );
};

useEffect(() => {
  if (inputMode === "manual") {
    const text = "Ask something . . .";
    let index = 0;

    const interval = setInterval(() => {
      setPlaceholderText(text.slice(0, index));
      index++;
      if (index > text.length) clearInterval(interval);
    }, 60);

    return () => clearInterval(interval);
  }
}, [inputMode]);



const handleSubmit = async () => {
  console.log("handleSubmit");
  setLoading(true); // add a loading state
  
  try {
    const response = await fetch("http://localhost:8282/get-react-code-using-ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        schemaName: selectedSchema,
        query: generatedQuery,
        textQue: formValue,
        dbJsonData: queryResult
      })
    });

    const result = await response.json();
    console.log("result:", result);          // ← check what you're getting
    console.log("reactCode:", result.reactCode); // ← confirm key name

    if (result.reactCode) {
      // 1. Set localStorage FIRST
      localStorage.setItem("generatedReactCode", result.reactCode);
      localStorage.setItem("generatedMeta", JSON.stringify({
        query: generatedQuery,
        schema: selectedSchema,
        question: formValue,
        generatedAt: new Date().toISOString()
      }));

      // 2. Confirm it was saved
      const saved = localStorage.getItem("generatedReactCode");
      console.log("saved to localStorage:", !!saved);

      // 3. THEN open new tab
      const newTab = window.open("/custom-response", "_blank");
      
      // 4. If browser blocked popup, fallback to same tab navigate
      if (!newTab) {
        console.warn("Popup blocked! Navigating in same tab...");
        window.location.href = "/custom-response";
      }

      setOpenDialog(false);
    } else {
      console.error("reactCode missing in response. Keys:", Object.keys(result));
    }

  } catch (error) {
    console.error("Error:", error);
  } finally {
    setLoading(false);
  }
};
  /* ================= UI ================= */

  return (
  <Box
  sx={{
    height: "100vh",    // 👈 full screen initially
    width: "100%",
    display: "flex",
    alignItems: "stretch",
    background: "linear-gradient(135deg, #eef2f3, #d9e4f5)",
    boxSizing: "border-box"
  }}
>

    {/* LEFT PANEL 30% */}
    <Box
      sx={{
        width: "35%",
        minHeight: "100vh",
        p: 2,
         overflowY: "auto"
      }}
    >
     <Paper
  elevation={0}
  sx={{
    p: 3,
    borderRadius: 4,
    backdropFilter: "blur(10px)",
    background: "rgba(255,255,255,0.75)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.08)",
    border: "1px solid rgba(255,255,255,0.3)"
  }}
>

        <Typography
  variant="h5"
  fontWeight="bold"
  sx={{
    mb: 2,
    background: "linear-gradient(90deg, #1976d2, #42a5f5)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent"
  }}
>
  Dynamic Data Explorer
</Typography>

        {/* Schema */}
        <FormControl fullWidth>
          <InputLabel id="schema-label">Schema</InputLabel>
          <Select
          label="Schema"
        labelId="schema-label"
          sx={{
      borderRadius: 3,
      backgroundColor: "#f9fafc",
      "& .MuiOutlinedInput-notchedOutline": {
        borderColor: "#d0d7e2"
      },
      "&:hover .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      },
      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      }
    }}
    MenuProps={{
    PaperProps: {
      sx: {
        borderRadius: 3,
        mt: 1,
        boxShadow: "0 10px 30px rgba(0,0,0,0.15)"
      }
    }
  }}

  value={selectedSchema}
  onChange={(e) => {
    const schemaName = e.target.value;
    setSelectedSchema(schemaName);
    setSelectedTable("");

    fetch(`http://localhost:8282/get-schema-by-schemaName?schemaName=${schemaName}`)
      .then((res) => res.json())
      .then((data) => {
        console.log("Schema Data:", data);
        setSchemaData(data);
      })
      .catch((err) => {
        console.error("Error fetching schema details:", err);
      });
  }}
>
            {schemas.map((s) => (
              <MenuItem key={s} value={s}
               sx={{
    borderRadius: 2,
    mx: 1,
    my: 0.5,
    "&:hover": {
      backgroundColor: "#e3f2fd"
    },
    "&.Mui-selected": {
      backgroundColor: "#bbdefb !important",
      fontWeight: 600
    }
  }}
              >{s}</MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* INPUT MODE SELECTION */}
<Box mb={2}>
  <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
    
  </Typography>

  <RadioGroup
    row
    value={inputMode}
    onChange={(e) => setInputMode(e.target.value)}
  >
    <FormControlLabel
      value="query"
      control={<Radio />}
      label="Build Query"
    />

    <FormControlLabel
      value="manual"
      control={<Radio />}
      label="Ask AI"
    />
  </RadioGroup>
</Box>

<Collapse in={inputMode === "manual"}>
  <Box mt={1}
  sx={{
      p: 3,
      borderRadius: 3,
      background: "linear-gradient(145deg, #f9fafc, #eef2f7)",
      boxShadow: "0 8px 25px rgba(0,0,0,0.08)",
      position: "relative",
      overflow: "hidden"
    }}>
    <TextField
      label="Enter Your Question"
      fullWidth
      multiline
      minRows={3}
      placeholder={placeholderText}
      value={manualQuestion}
      onChange={(e) => setManualQuestion(e.target.value)}
      sx={{
    "& .MuiOutlinedInput-root": {
      borderRadius: 3,
      transition: "all 0.4s ease",
      "& fieldset": {
        borderColor: "#1976d2",
      },
      "&:hover fieldset": {
        borderColor: "#1565c0",
      },
      "&.Mui-focused fieldset": {
        borderWidth: "2px",
        borderColor: "#1976d2",
        boxShadow: "0 0 12px rgba(25,118,210,0.4)"
      }
    }
  }}
    />
    {errorMsg && (
  <Typography color="error" sx={{ mt: 1 }}>
    {errorMsg}
  </Typography>
)}
    <Box mt={2} textAlign="right">
      <Button
         variant="contained"
           sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600,
    boxShadow: "0 4px 14px rgba(0,0,0,0.15)"
  }}
      onClick={async () => {
  if (!selectedSchema) {
  setErrorMsg("Please select schema.");
  return;
}

if (!manualQuestion.trim()) {
  setErrorMsg("Please enter your question.");
  return;
}

setErrorMsg(""); // clear if valid
setQueryResult([]); 
  try {
    setAiLoading(true);
    const res = await fetch("http://localhost:8282/get-db-level-data-by-textQue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        schemaName: selectedSchema,
        query: "",
        textQue: manualQuestion,
        dbJsonData: schemaData || {}
      })
    });

    const data = await res.json();

    console.log("Manual Question Response:", data);

    const rows = data?.data?.rows || [];
    const cleanSql = (data?.sql || "")
      .replace(/```sql|```/g, "")
      .trim();

    setGeneratedQuery(cleanSql);
    setQueryResult(rows);

  } catch (err) {
    console.error("Error:", err);
  }
  finally {
    setAiLoading(false); // ✅ stop loading
  }
}}
      >
        View
      </Button>
    </Box>
  </Box>
  </Collapse>
  
<Collapse in={inputMode === "query"}>
        {/* Table */}
        {selectedSchema && schemaData?.tables && (
  <FormControl fullWidth margin="normal">
    <InputLabel id="table-select">Table</InputLabel>
    <Select
    label="Table"
    id="table-select"
     sx={{
      borderRadius: 3,
      backgroundColor: "#f9fafc",
      "& .MuiOutlinedInput-notchedOutline": {
        borderColor: "#d0d7e2"
      },
      "&:hover .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      },
      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      }
    }}
     MenuProps={{
    PaperProps: {
      sx: {
        borderRadius: 3,
        mt: 1,
        boxShadow: "0 10px 30px rgba(0,0,0,0.15)"
      }
    }
  }}
      value={selectedTable}
      onChange={(e) => setSelectedTable(e.target.value)}
    >
      {schemaData.tables.map((table) => (
        <MenuItem key={table.name} value={table.name}
        sx={{
    borderRadius: 2,
    mx: 1,
    my: 0.5,
    "&:hover": {
      backgroundColor: "#e3f2fd"
    },
    "&.Mui-selected": {
      backgroundColor: "#bbdefb !important",
      fontWeight: 600
    }
  }}
        >
          {table.name}
        </MenuItem>
      ))}
    </Select>
  </FormControl>
)}

{/* Columns Section */}
{selectedTable && (
  <>
    {/* <Typography
      mt={3}
      fontWeight="bold"
      fontSize={18}
      sx={{ color: "#2c3e50" }}
    >
    Select Columns
    </Typography> */}

    <Box
      sx={{
        maxHeight: 400,
        overflowY: "auto",
        borderRadius: 3,
        p: 3,
        mt: 2,
        background: "linear-gradient(145deg, #ffffff, #f4f6f8)",
        boxShadow: "0 6px 20px rgba(0,0,0,0.08)"
      }}
    >
 {/* ONE Global Search Box */}
    <Box mt={2} mb={3}>
      <TextField
        fullWidth
        size="small"
        placeholder="Search columns..."
        value={columnSearch}
        onChange={(e) => setColumnSearch(e.target.value)}
        sx={{
          "& .MuiOutlinedInput-root": {
      borderRadius: 3,
      backgroundColor: "#f9fafc"
    }
        }}
      />
    </Box>

      {renderTableColumns(selectedTable)}
      {joinTable && renderTableColumns(joinTable)}
    </Box>
  </>
)}


       <Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
  <AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      JOIN
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={3} sx={{p:2}}>
       
      {/* Your existing JOIN fields go here */}

      {/* Join Table */}
      {columns.length > 0 && (
        <>
      <TextField
        select
        label="Join Table"
        value={joinTable}
        onChange={(e) => setJoinTable(e.target.value)}
        fullWidth
        size="small"
        sx={{
          "& .MuiOutlinedInput-root": {
            borderRadius: 3,
            backgroundColor: "#f9fafc"
          }
        }}
      >
        {schemaData?.tables
          ?.filter((t) => t.name !== selectedTable)
          .map((t) => (
            <MenuItem key={t.name} value={t.name}
            sx={menuItemStyle}>
              {t.name}
            </MenuItem>
          ))}
      </TextField>

      {/* Join Type */}
      <TextField
        select
        label="Join Type"
        value={joinType}
        onChange={(e) => setJoinType(e.target.value)}
        fullWidth
        size="small"
        sx={{
          "& .MuiOutlinedInput-root": {
            borderRadius: 3,
            backgroundColor: "#f9fafc"
          }
        }}
      >
        <MenuItem value="INNER JOIN" sx={menuItemStyle}>INNER JOIN</MenuItem>
        <MenuItem value="LEFT JOIN" sx={menuItemStyle}>LEFT JOIN</MenuItem>
        <MenuItem value="RIGHT JOIN" sx={menuItemStyle}>RIGHT JOIN</MenuItem>
        <MenuItem value="FULL JOIN" sx={menuItemStyle}>FULL JOIN</MenuItem>
      </TextField>

      {/* Join Condition */}
      {joinTable && (
        <TextField
          select
          label="Join Condition"
          value={useCustomJoin ? "OTHER" : joinCondition}
          onChange={(e) => {
            if (e.target.value === "OTHER") {
              setUseCustomJoin(true);
              setJoinCondition("");
            } else {
              setUseCustomJoin(false);
              setJoinCondition(e.target.value);
            }
          }}
          fullWidth
          size="small"
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 3,
              backgroundColor: "#f9fafc"
            }
          }}
        >
          {autoJoinConditions.map((cond, index) => (
            <MenuItem key={index} value={cond}
            sx={menuItemStyle}>
              {cond}
            </MenuItem>
          ))}

          <MenuItem value="OTHER">Other (Custom)</MenuItem>
        </TextField>
      )}

      {/* Custom Join Field */}
      {useCustomJoin && (
        <TextField
          label="Custom Join Condition"
          placeholder="table1.id = table2.user_id"
          value={joinCondition}
          onChange={(e) => setJoinCondition(e.target.value)}
          fullWidth
          size="small"
          sx={{
            "& .MuiOutlinedInput-root": {
              borderRadius: 3,
              backgroundColor: "#f9fafc"
            }
          }}
        />
      )}
      </>
)}
    </Box>
  </AccordionDetails>
</Accordion>

{/* WHERE */}
 <Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
<AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      WHERE
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={2}>
        {/* WHERE */}
        {columns.length > 0 && (
          <>
            {whereConditions.map((cond, i) => (
              <Grid container spacing={1} alignItems="center" mt={1}>
  {/* Column */}
  <Grid item xs={4}>
    <Select
      fullWidth
      size="small"
      value={cond.column}
      onChange={(e) => {
        const updated = [...whereConditions];
        updated[i].column = e.target.value;
        setWhereConditions(updated);
      }}
      sx={modernSelectStyle}
      MenuProps={selectMenuProps}
    >
      {availableColumns.map((col) => (
  <MenuItem key={col.value} value={col.value}
  sx={menuItemStyle}>
    {col.label}
  </MenuItem>
))}
    </Select>
  </Grid>

  {/* Operator */}
  <Grid item xs={3}>
    <Select
      fullWidth
      size="small"
      value={cond.operator}
      onChange={(e) => {
        const updated = [...whereConditions];
        updated[i].operator = e.target.value;
        setWhereConditions(updated);
      }}
      sx={modernSelectStyle}
      MenuProps={selectMenuProps}
    >
      <MenuItem value="=" sx={menuItemStyle}>=</MenuItem>
      <MenuItem value="!=" sx={menuItemStyle}>!=</MenuItem>
      <MenuItem value=">" sx={menuItemStyle}>{">"}</MenuItem>
      <MenuItem value="<" sx={menuItemStyle}>{"<"}</MenuItem>
    </Select>
  </Grid>

  {/* Value - fixed width */}
  <Grid item>
    <TextField
      size="small"
      value={cond.value}
      onChange={(e) => {
        const updated = [...whereConditions];
        updated[i].value = e.target.value;
        setWhereConditions(updated);
      }}
      sx={{ "& .MuiOutlinedInput-root": {
      borderRadius: 3,   // 🔥 Rounded corners
      backgroundColor: "#f9fafc"
    },
    width: 80 }} // ✅ fixed width so icon doesn't shift
    />
  </Grid>

  {/* Delete button */}
  <Grid item>
    <IconButton
      onClick={() =>
        removeCondition(setWhereConditions, whereConditions, i)
      }
      size="small"
    >
      <DeleteIcon fontSize="small" color="error" />
    </IconButton>
  </Grid>
</Grid>

            ))}
<Box display="flex" justifyContent="flex-start" mt={1}>
            <Button
              size="small"
              onClick={() =>
                addCondition(setWhereConditions, whereConditions)
              }
            >
              Add WHERE
            </Button>
            </Box>
          </>
        )}
        </Box>
</AccordionDetails>
</Accordion>

        {/* GROUP BY */}
        <Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
<AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      GROUP BY
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={2}>
{columns.length > 0 && (
  <>
    {groupBy.map((col, i) => (
      <Grid container spacing={1} key={i} mt={1}>
        <Grid item xs={10}>
          <Select
            fullWidth
            size="small"
            value={col}
            onChange={(e) => {
              const updated = [...groupBy];
              updated[i] = e.target.value;
              setGroupBy(updated);
            }}
            sx={modernSelectStyle}
            MenuProps={selectMenuProps}
          >
            {availableColumns.map((col) => (
  <MenuItem key={col.value} value={col.value}
  sx={menuItemStyle}>
    {col.label}
  </MenuItem>
))}
          </Select>
        </Grid>

        <Grid item>
          <IconButton
            onClick={() => {
              const updated = [...groupBy];
              updated.splice(i, 1);
              setGroupBy(updated);
            }}
             size="small"
          >
            <DeleteIcon fontSize="small" color="error" />
          </IconButton>
        </Grid>
      </Grid>
    ))}
<Box display="flex" justifyContent="flex-start" mt={1}>
    <Button size="small" onClick={addGroupBy}>
      Add GROUP BY
    </Button>
    </Box>
  </>
)}
</Box>
</AccordionDetails>
</Accordion>

<Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
<AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      HAVING
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={2}>
{/* HAVING */}
{columns.length > 0 && groupBy.length > 0 && hasAggregate && groupBy.some(col => col) && (
  <>
    {havingConditions.map((cond, i) => (
      <Grid container spacing={1} key={i} mt={1}>
        <Grid item xs={4}>
          <Select
            fullWidth
            size="small"
            value={cond.column}
            onChange={(e) => {
              const updated = [...havingConditions];
              updated[i].column = e.target.value;
              setHavingConditions(updated);
            }}
            sx={modernSelectStyle}
            MenuProps={selectMenuProps}
          >
            {aggregateColumns.map((c) => (
  <MenuItem key={c} value={c}
  sx={menuItemStyle}>
    {aggregates[c]}({c})
  </MenuItem>
))}
          </Select>
        </Grid>

        <Grid item xs={3}>
          <Select
            fullWidth
            size="small"
            value={cond.operator}
            onChange={(e) => {
              const updated = [...havingConditions];
              updated[i].operator = e.target.value;
              setHavingConditions(updated);
            }}
            sx={modernSelectStyle}
            MenuProps={selectMenuProps}
          >
            <MenuItem value="=" sx={menuItemStyle}>=</MenuItem>
            <MenuItem value="!=" sx={menuItemStyle}>!=</MenuItem>
            <MenuItem value=">" sx={menuItemStyle}>{">"}</MenuItem>
            <MenuItem value="<" sx={menuItemStyle}>{"<"}</MenuItem>
          </Select>
        </Grid>

        <Grid item>
          <TextField
            size="small"
            fullWidth
            value={cond.value}
            onChange={(e) => {
              const updated = [...havingConditions];
              updated[i].value = e.target.value;
              setHavingConditions(updated);
            }}
             sx={{ 
              "& .MuiOutlinedInput-root": {
      borderRadius: 3,
      backgroundColor: "#f9fafc"
    },
              width: 80 }} 
          />
        </Grid>

        <Grid item>
          <IconButton
            onClick={() =>
              removeCondition(setHavingConditions, havingConditions, i)
            }
              size="small"
          >
            <DeleteIcon fontSize="small" color="error" />
          </IconButton>
        </Grid>
      </Grid>
    ))}

    <Box display="flex" justifyContent="flex-start" mt={1}>
  <Button
    size="small"
    onClick={() =>
      addCondition(setHavingConditions, havingConditions)
    }
  >
    Add HAVING
  </Button>
</Box>
  </>
)}
</Box>
</AccordionDetails>
</Accordion>

{/* ORDER BY */}
<Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
<AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      ORDER BY
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={2}>
{columns.length > 0 && (
  <>
    {orderBy.map((o, i) => (
      <Grid container spacing={1} key={i} mt={1}>
        <Grid item xs={6}>
          <Select
            fullWidth
            size="small"
            value={o.column}
            onChange={(e) => {
              const updated = [...orderBy];
              updated[i].column = e.target.value;
              setOrderBy(updated);
            }}
            sx={modernSelectStyle}
      MenuProps={selectMenuProps}
          >
            {availableColumns.map((col) => (
  <MenuItem key={col.value} value={col.value}
  sx={menuItemStyle}>
    {col.label}
  </MenuItem>
))}
          </Select>
        </Grid>

        <Grid item xs={4}>
          <Select
            fullWidth
            size="small"
            value={o.direction}
            onChange={(e) => {
              const updated = [...orderBy];
              updated[i].direction = e.target.value;
              setOrderBy(updated);
            }}
            sx={modernSelectStyle}
      MenuProps={selectMenuProps}
          >
            <MenuItem value="ASC" sx={menuItemStyle}>ASC</MenuItem>
            <MenuItem value="DESC" sx={menuItemStyle}>DESC</MenuItem>
          </Select>
        </Grid>

        <Grid item>
          <IconButton
            onClick={() => {
              const updated = [...orderBy];
              updated.splice(i, 1);
              setOrderBy(updated);
            }}
             size="small"
          >
            <DeleteIcon fontSize="small" color="error" />
          </IconButton>
        </Grid>
      </Grid>
    ))}

    <Box display="flex" justifyContent="flex-start" mt={1}>
  <Button size="small" onClick={addOrderBy}>
    Add ORDER BY
  </Button>
</Box>
  </>
)}
</Box>
</AccordionDetails>
</Accordion>

        {/* LIMIT */}
       <Accordion
  defaultExpanded={false}   // 🔥 collapsed by default
  sx={{
    mt: 4,
    borderRadius: 3,
    boxShadow: "0 6px 20px rgba(0,0,0,0.05)",
    "&:before": { display: "none" } // removes top line
  }}
>
<AccordionSummary
    expandIcon={<ExpandMoreIcon />}
    sx={{
      borderRadius: 3,
      background: "#f4f6f8",
      fontWeight: 600
    }}
  >
    <Typography fontWeight="bold">
      LIMIT
    </Typography>
  </AccordionSummary>

  <AccordionDetails>
    <Box display="flex" flexDirection="column" gap={2}>
        <TextField
  label="Limit"
  type="number"
  value={limit}
  onChange={(e) => {
    const value = Math.max(0, Number(e.target.value));
    setLimit(value);
  }}
  onKeyDown={(e) => {
    if (e.key === "-" || e.key === "e") {
      e.preventDefault();
    }
  }}
  inputProps={{ min: 0 }}
  fullWidth
 sx={{ "& .MuiOutlinedInput-root": {
      borderRadius: 3, 
      backgroundColor: "#f9fafc"
    }
  }}
/>
</Box>
</AccordionDetails>
</Accordion>

        {/* ACTION BUTTONS */}
        <Box mt={2} display="flex" gap={2}>
          <Button
            variant="contained"
           sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600,
    boxShadow: "0 4px 14px rgba(0,0,0,0.15)"
  }}
            onClick={generateQuery}
          >
            Generate Query
          </Button>

          <Button
            variant="outlined"
            color="error"
            sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600
  }}
            onClick={clearAll}
          >
            Clear All
          </Button>
        </Box>
</Collapse>
      </Paper>
    </Box>

    {/* RIGHT PANEL 70% */}
    <Box
      sx={{
        width: "66%",
        p: 2,
        minHeight: "100vh"
      }}
    >
      <Paper
       elevation={0}
  sx={{
    p: 3,
    display: "flex",
    flexDirection: "column",
    borderRadius: 4,
    backdropFilter: "blur(10px)",
    background: "rgba(255,255,255,0.75)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.08)",
    border: "1px solid rgba(255,255,255,0.3)"
  }}
>
        <Typography variant="h6"
  fontWeight="bold"
  sx={{
    mb: 2,
    background: "linear-gradient(90deg, #1976d2, #42a5f5)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent"
  }}>Generated Query</Typography>

      <Box
  sx={{
    borderRadius: 2,
    overflow: "hidden",
    border: "1px solid #2d2d2d",
    background: "#1e1e1e",
    position: "relative"
  }}
>

  {/* Copy Button */}
  {generatedQuery && (
    <IconButton
      onClick={() => {
        navigator.clipboard.writeText(generatedQuery);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      sx={{
        position: "absolute",
        top: 8,
        right: 8,
        color: copied ? "#4caf50" : "#ffffff",
        background: "rgba(255,255,255,0.05)",
        "&:hover": {
          background: "rgba(255,255,255,0.15)"
        }
      }}
    >
      {copied ? <CheckIcon /> : <ContentCopyIcon />}
    </IconButton>
  )}

  <SyntaxHighlighter
    language="sql"
    style={okaidia}
    wrapLongLines={true}
    customStyle={{
      margin: 0,
      padding: "28px",
      paddingBottom: "70px",   // 👈 important (space for button)
      minHeight: "200px",
      maxHeight: "450px",
      overflowY: "auto",
      overflowX: "hidden",
      fontSize: "20px",
      fontFamily: "Fira Code, monospace",
      lineHeight: "1.6",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word"
    }}
    codeTagProps={{
    style: {
      whiteSpace: "pre-wrap",
      wordBreak: "break-word"
    }
  }}
  >
    {generatedQuery || "-- Your query will appear here"}
  </SyntaxHighlighter>

  {/* RUN BUTTON INSIDE BOX */}
  <Button
  variant="contained"
  disabled={!generatedQuery} 
  onClick={handleRunQuery}
  startIcon={
    loading ? (
      <CircularProgress size={18} sx={{ color: "#ffffff" }} />
    ) : null
  }
  sx={{
    position: "absolute",
    bottom: 16,
    right: 16,
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600,
    backgroundColor: "#2e7d32",  // success green
    color: "#ffffff",            // white text
    "&:hover": {
      backgroundColor: "#1b5e20"
    },
    "&.Mui-disabled": {
      backgroundColor: "#2e7d32", // keep same color
      color: "#ffffff",
      opacity: 1                 // remove faded effect
    }
  }}
>
  {loading ? "Running..." : "Run"}
</Button>

</Box>

{aiLoading && (
  <Box
    sx={{
      position: "fixed",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      backdropFilter: "blur(4px)",
      backgroundColor: "rgba(255,255,255,0.6)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 2000
    }}
  >
    <Box textAlign="center">
      <CircularProgress size={60} />
      <Typography sx={{ mt: 2 }}>
        AI analysing your request...
      </Typography>
    </Box>
  </Box>
)}

  {/* RESULT TABLE */}
{queryResult && queryResult.length > 0 && (
  <Box mt={3}>

<Box mt={2} display="flex" gap={2}  justifyContent="flex-end">
  {/* <Button
    variant="contained"
    sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600,
    boxShadow: "0 4px 14px rgba(0,0,0,0.15)"
  }}
    color="primary"
    onClick={downloadPDF}
  >
    Download PDF
  </Button> */}

  <Tooltip title="Click to analyse data">
  <IconButton
    onClick={() => setOpenDialog(true)}
    sx={{
      backgroundColor: "#ffffff",
      border: "1.5px solid #000",
      color: "#000",
      borderRadius: 2,
      boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
      "&:hover": {
        backgroundColor: "#f5f5f5",
        border: "1.5px solid #000"
      }
    }}
  >
    <QuestionAnswerIcon />
  </IconButton>
</Tooltip>

<Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
  <DialogTitle>Enter Details</DialogTitle>

  <DialogContent>
    <TextField
      fullWidth
      label="Enter Value"
      value={formValue}
      onChange={(e) => setFormValue(e.target.value)}
      sx={{ mt: 1 }}
    />
  </DialogContent>

  <DialogActions>
    <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
    <Button variant="contained" onClick={handleSubmit}>
      Submit
    </Button>
  </DialogActions>
</Dialog>

  <Button
  variant="contained"
  color="success"
  onClick={downloadExcel}
  sx={{
    borderRadius: 3,
    minWidth: 38,          // small square button
    width: 38,
    height: 38,
    backgroundColor: "#1f4c1f",
    boxShadow: "0 4px 14px rgba(0,0,0,0.15)"
  }}
>
  <DownloadIcon />
</Button>
</Box>

   <Paper
  elevation={0}
  sx={{
    mt: 3,
    borderRadius: 4,
    boxShadow: "0 8px 24px rgba(0,0,0,0.08)"
  }}
>
   <Box sx={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead style={{
  background: "linear-gradient(90deg,#1976d2,#42a5f5)",
  color: "white"
}}>

          <tr>
            {Object.keys(queryResult[0]).map((key) => (
              <th
                key={key}
                style={{
                  padding: "10px",
                  border: "1px solid #ddd",
                  textAlign: "left"
                }}
              >
                {key}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {queryResult
            .slice(
              (currentPage - 1) * rowsPerPage,
              currentPage * rowsPerPage
            )
            .map((row, index) => (
              <tr key={index}>
                {Object.values(row).map((value, i) => (
                  <td
                    key={i}
                    style={{
                      padding: "10px",
                      border: "1px solid #ddd"
                    }}
                  >
                    {value}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
      </Box>
    </Paper>

    {/* Pagination Controls */}
    <Box  mt={3}
  display="flex"
  justifyContent="space-between"
  alignItems="center"
  sx={{
    background: "#ffffff",
    p: 2,
    borderRadius: 3,
    boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
  }}>
      <Button
        variant="outlined"
         sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600
  }}
        disabled={currentPage === 1}
        onClick={() => setCurrentPage(currentPage - 1)}
      >
        Previous
      </Button>

      <Typography>
        Page {currentPage} of{" "}
        {Math.ceil(queryResult.length / rowsPerPage)}
      </Typography>

      <Button
        variant="outlined"
         sx={{
    borderRadius: 3,
    textTransform: "none",
    fontWeight: 600
  }}
        disabled={
          currentPage ===
          Math.ceil(queryResult.length / rowsPerPage)
        }
        onClick={() => setCurrentPage(currentPage + 1)}
      >
        Next
      </Button>
    </Box>
  </Box>
)}


      </Paper>
    </Box>
<Box
  sx={{
    position: "fixed",
    bottom: 0,
    left: 0,
    width: "100%",
    height: 40,
    overflow: "hidden",
    zIndex: 1500,
    display: "flex",
    alignItems: "center"
  }}
>
  <Box
    sx={{
      display: "flex",
      gap: 20,
      animation: "moveIcons 20s linear infinite"
    }}
  >
    <PeopleIcon sx={{ fontSize: 40, color: "#0d47a1" }} />
    <WorkIcon sx={{ fontSize: 40, color: "#1565c0" }} />
    <AssessmentIcon sx={{ fontSize: 40, color: "#1976d2" }} />
    <PaymentsIcon sx={{ fontSize: 40, color: "#1e88e5" }} />
    <BusinessIcon sx={{ fontSize: 40, color: "#42a5f5" }} />
    <PeopleIcon sx={{ fontSize: 40, color: "#0d47a1" }} />
    <WorkIcon sx={{ fontSize: 40, color: "#1565c0" }} />
  </Box>

  <style>
    {`
      @keyframes moveIcons {
        from { transform: translateX(100%); }
        to { transform: translateX(-100%); }
      }
    `}
  </style>
</Box>

  </Box>

);
}
