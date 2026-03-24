// import { useEffect, useState } from "react";
// import "../Styles/tableCard.css";   

// function TableCard({ metric, refreshKey }) {
//   const [data, setData] = useState([]);

//   const fetchData = () => {
//     fetch(`http://localhost:8282${metric.url}`)
//       .then(res => res.json())
//       .then(res => {
//         if (Array.isArray(res)) {
//           setData(res);
//         } else {
//           setData([]);
//         }
//       });
//   };

//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]); // ✅ refresh support

//   return (
//     <div className="table-container">

//       <div className="table-scroll">
//         <table className="custom-table">
//           <thead>
//             <tr>
//               {data[0] &&
//                 Object.keys(data[0]).map((key) => (
//                   <th key={key}>{key}</th>
//                 ))}
//             </tr>
//           </thead>

//           <tbody>
//             {data.map((row, i) => (
//               <tr key={i}>
//                 {Object.values(row).map((val, j) => (
//                   <td key={j}>
//                     {typeof val === "object"
//                       ? JSON.stringify(val)
//                       : val}
//                   </td>
//                 ))}
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>

//     </div>
//   );
// }

// export default TableCard;

import { useEffect, useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender
} from "@tanstack/react-table";

import SearchIcon from "@mui/icons-material/Search";
import DownloadIcon from "@mui/icons-material/Download";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import CloseFullscreenIcon from "@mui/icons-material/CloseFullscreen";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";

import Papa from "papaparse";
import { saveAs } from "file-saver";

import "../Styles/tableCard.css";

function TableCard({ metric, refreshKey }) {
  const [data, setData] = useState([]);
  const [globalFilter, setGlobalFilter] = useState("");
  const [isMaximized, setIsMaximized] = useState(false);

  // 🔥 Fetch Data
  const fetchData = () => {
    fetch(`http://localhost:8282${metric.url}`)
      .then(res => res.json())
      .then(res => {
        if (Array.isArray(res)) {
          setData(res);
        } else {
          setData([]);
        }
      });
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  useEffect(() => {
  if (isMaximized) {
    document.body.style.overflow = "hidden";
  } else {
    document.body.style.overflow = "auto";
  }

  return () => {
    document.body.style.overflow = "auto";
  };
}, [isMaximized]);

  // 🔥 Columns
  const columns = useMemo(() => {
    if (!data.length) return [];
    return Object.keys(data[0]).map((key) => ({
      accessorKey: key,
      header: key.toUpperCase(),
      cell: (info) => {
        const val = info.getValue();
        return typeof val === "object"
          ? JSON.stringify(val)
          : val;
      }
    }));
  }, [data]);

  useEffect(() => {
  setPagination(prev => ({
    ...prev,
    pageIndex: 0
  }));
}, [data]);

  // 🔥 Table Instance
  const [pagination, setPagination] = useState({
  pageIndex: 0,
  pageSize: 5
});

const table = useReactTable({
  data,
  columns,
  state: {
    globalFilter,
    pagination
  },
  onPaginationChange: setPagination,   // ✅ IMPORTANT
  onGlobalFilterChange: setGlobalFilter,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getPaginationRowModel: getPaginationRowModel()
});

  // 🔥 CSV Download
  const downloadCSV = () => {
    const csv = Papa.unparse(data);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `${metric.key}.csv`);
  };

  return (
    <div className="table-card">

      {/* 🔝 HEADER */}
      <div className="table-header">

        <div className="search-box">
          <SearchIcon />
          <input
            placeholder="Search..."
            value={globalFilter || ""}
            onChange={(e) => setGlobalFilter(e.target.value)}
          />
        </div>

        <div className="table-actions">
          <button onClick={downloadCSV}>
            <DownloadIcon />
          </button>

          {/* <button onClick={() => setIsMaximized(!isMaximized)}>
            {isMaximized ? <CloseFullscreenIcon /> : <FullscreenIcon />}
          </button> */}
        </div>
      </div>


      {/* 🔥 TABLE */}
      <div className="table-scroll">
        <table className="custom-table">

          <thead>
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
  key={header.id}
  onClick={header.column.getToggleSortingHandler()}
  style={{
    cursor: "pointer",
    userSelect: "none",
    textAlign: "center",
    verticalAlign: "middle"
  }}
>
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      gap: "6px"
    }}
  >
    {/* Header Text */}
    <span>
      {flexRender(
        header.column.columnDef.header,
        header.getContext()
      )}
    </span>

    {/* Sort Icon */}
    <span style={{ display: "flex", alignItems: "center" }}>
      {header.column.getIsSorted() === "asc" && (
        <ArrowUpwardIcon style={{ fontSize: "16px" }} />
      )}

      {header.column.getIsSorted() === "desc" && (
        <ArrowDownwardIcon style={{ fontSize: "16px" }} />
      )}

      {!header.column.getIsSorted() && (
        <UnfoldMoreIcon style={{ fontSize: "16px", opacity: 0.4 }} />
      )}
    </span>
  </div>
</th>
                ))}
              </tr>
            ))}
          </thead>

          <tbody>
            {table.getRowModel().rows.map(row => (
              <tr key={row.id}>
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id}>
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext()
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>

        </table>
      </div>

      {/* 🔥 PAGINATION */}
      <div className="pagination-container">

  {/* LEFT SIDE */}
  <div className="pagination-left">
    <span>
      Showing {table.getRowModel().rows.length} of {data.length} rows
    </span>
  </div>

  {/* CENTER */}
  <div className="pagination-center">
    <button
      className="page-btn"
      onClick={() => table.previousPage()}
      disabled={!table.getCanPreviousPage()}
    >
      ⬅ Prev
    </button>

    <span className="page-info">
      Page {pagination.pageIndex + 1}
    </span>

    <button
      className="page-btn"
      onClick={() => table.nextPage()}
      disabled={!table.getCanNextPage()}
    >
      Next ➡
    </button>
  </div>

  {/* RIGHT SIDE */}
  <div className="pagination-right">
    <span>Rows:</span>
    <select
      className="page-size"
      value={pagination.pageSize}
      onChange={(e) => table.setPageSize(Number(e.target.value))}
    >
      {[5, 10, 20, 50].map(size => (
        <option key={size} value={size}>
          {size}
        </option>
      ))}
    </select>
  </div>

</div>

    </div>
  );
}

export default TableCard;