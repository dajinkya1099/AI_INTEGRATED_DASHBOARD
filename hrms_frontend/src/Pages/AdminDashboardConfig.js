// import { useState } from "react";
// import "../Styles/adminConfig.css";

// function AdminDashboardConfig() {

//   const [modules, setModules] = useState([]);

//   const [moduleName, setModuleName] = useState("");
//   const [metrics, setMetrics] = useState([
//     { key: "", url: "", type: "count" }
//   ]);

//   const [username, setUsername] = useState("");
//   const [moduleIdForAccess, setModuleIdForAccess] = useState(null);

//   // ➕ Add Metric
//   const addMetric = () => {
//     setMetrics([...metrics, { key: "", url: "", type: "count" }]);
//   };

//   // 🔄 Update metric
//   const handleMetricChange = (i, field, value) => {
//     const updated = [...metrics];
//     updated[i][field] = value;
//     setMetrics(updated);
//   };

//   // 💾 SAVE MODULE
//   const handleSubmit = async () => {
//     const payload = {
//       moduleName,
//       metrics
//     };

//     try {
//       const res = await fetch("http://localhost:8282/api/dashboard/modules", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload)
//       });

//       const savedModule = await res.json();

//       // ✅ update UI locally (NO FETCH)
//       setModules([...modules, savedModule]);

//       // reset form
//       setModuleName("");
//       setMetrics([{ key: "", url: "", type: "count" }]);

//     } catch (err) {
//       console.error(err);
//     }
//   };

//   // ❌ SOFT DELETE
//   const handleDelete = async (id) => {
//     await fetch(`http://localhost:8282/api/dashboard/modules/${id}`, {
//       method: "DELETE"
//     });

//     // remove locally
//     setModules(modules.filter(m => m.id !== id));
//   };

//   // 🔐 ASSIGN MODULE
//   const assignModule = async () => {
//     if (!username || !moduleIdForAccess) return;

//     await fetch("http://localhost:8282/api/dashboard/assign", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({
//         username,
//         moduleId: moduleIdForAccess
//       })
//     });

//     alert("Assigned successfully");
//   };

//   return (
//     <div className="admin-container">

//       <h2>Admin Dashboard Config</h2>

//       {/* 🔥 CREATE MODULE */}
//       <div className="card">

//         <input
//           className="input"
//           placeholder="Module Name"
//           value={moduleName}
//           onChange={(e) => setModuleName(e.target.value)}
//         />

//         <h4>Metrics</h4>

//         {metrics.map((m, i) => (
//           <div key={i} className="metric-row">

//             <input
//               placeholder="Key (e.g. Total Employees)"
//               value={m.key}
//               onChange={(e) =>
//                 handleMetricChange(i, "key", e.target.value)
//               }
//             />

//             <input
//               placeholder="API URL (/employees/count)"
//               value={m.url}
//               onChange={(e) =>
//                 handleMetricChange(i, "url", e.target.value)
//               }
//             />

//             <select
//               value={m.type}
//               onChange={(e) =>
//                 handleMetricChange(i, "type", e.target.value)
//               }
//             >
//               <option value="count">Count</option>
//               <option value="graph">Graph</option>
//               <option value="list">Table</option>
//               <option value="percentage">Percentage</option>
//             </select>

//           </div>
//         ))}

//         <button onClick={addMetric}>+ Add Metric</button>
//         <button className="primary-btn" onClick={handleSubmit}>
//           Save Module
//         </button>
//       </div>

//       {/* 🔐 ASSIGN ACCESS */}
//       <div className="card">
//         <h3>Assign Module to User</h3>

//         <input
//           placeholder="Enter Username"
//           onChange={(e) => setUsername(e.target.value)}
//         />

//         <select
//           onChange={(e) => setModuleIdForAccess(e.target.value)}
//         >
//           <option>Select Module</option>
//           {modules.map((m) => (
//             <option key={m.id} value={m.id}>
//               {m.moduleName}
//             </option>
//           ))}
//         </select>

//         <button onClick={assignModule}>
//           Assign Access
//         </button>
//       </div>

//       {/* 📋 LOCAL LIST */}
//       <div className="card">
//         <h3>Modules (Session)</h3>

//         {modules.length === 0 && <p>No modules added yet</p>}

//         {modules.map((mod) => (
//           <div key={mod.id} className="module-box">

//             <div>
//               <strong>{mod.moduleName}</strong>

//               <ul>
//                 {mod.metrics.map((m, i) => (
//                   <li key={i}>
//                     {m.key} ({m.type})
//                   </li>
//                 ))}
//               </ul>
//             </div>

//             <button onClick={() => handleDelete(mod.id)}>
//               Delete
//             </button>

//           </div>
//         ))}
//       </div>

//     </div>
//   );
// }

// export default AdminDashboardConfig;


// import { useState, useEffect } from "react";
// import "../Styles/adminConfig.css";

// function AdminDashboardConfig() {

//   const [modules, setModules] = useState([]);
//   const [moduleName, setModuleName] = useState("");
//   const [metrics, setMetrics] = useState([
//     { key: "", url: "", type: "count" }
//   ]);

//   const [username, setUsername] = useState("");
//   const [moduleIdForAccess, setModuleIdForAccess] = useState("");

//   // 📥 LOAD MODULES
//   useEffect(() => {
//     loadModules();
//   }, []);

//   const loadModules = async () => {
//     const res = await fetch("http://localhost:8282/api/dashboard/modules");
//     const data = await res.json();
//     console.log("Loaded modules:", data);
//     setModules(data);
//   };

//   // ➕ Add Metric
//   const addMetric = () => {
//     setMetrics([...metrics, { key: "", url: "", type: "count" }]);
//   };

//   // 🔄 Update Metric
//   const handleMetricChange = (i, field, value) => {
//     const updated = [...metrics];
//     updated[i][field] = value;
//     setMetrics(updated);
//   };

//   // 💾 SAVE MODULE
//   const handleSubmit = async () => {
//     const payload = { moduleName, metrics };

//     await fetch("http://localhost:8282/api/dashboard/modules", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify(payload)
//     });

//     await loadModules(); // ✅ reload full list

//     setModuleName("");
//     setMetrics([{ key: "", url: "", type: "count" }]);
//   };

//   // ❌ DELETE
//   const handleDelete = async (id) => {
//     await fetch(`http://localhost:8282/api/dashboard/modules/${id}`, {
//       method: "DELETE"
//     });

//     await loadModules(); // reload
//   };

//   // 🔐 ASSIGN
//   const assignModule = async () => {
//     await fetch("http://localhost:8282/api/dashboard/assign", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json"
//       },
//       body: JSON.stringify({
//         username,
//         moduleId: Number(moduleIdForAccess)
//       })
//     });

//     alert("Assigned successfully");
//   };

//   return (
//     <div className="admin-container">

//       <h2>Admin Dashboard Config</h2>

//       {/* CREATE MODULE */}
//       <div className="card">

//         <input
//           placeholder="Module Name"
//           value={moduleName}
//           onChange={(e) => setModuleName(e.target.value)}
//         />

//         <h4>Metrics</h4>

//         {metrics.map((m, i) => (
//           <div key={i}>

//             <input
//               placeholder="Key"
//               value={m.key}
//               onChange={(e) =>
//                 handleMetricChange(i, "key", e.target.value)
//               }
//             />

//             <input
//               placeholder="URL"
//               value={m.url}
//               onChange={(e) =>
//                 handleMetricChange(i, "url", e.target.value)
//               }
//             />

//             <select
//               value={m.type}
//               onChange={(e) =>
//                 handleMetricChange(i, "type", e.target.value)
//               }
//             >
//               <option value="count">Count</option>
//               <option value="graph">Graph</option>
//               <option value="list">Table</option>
//               <option value="percentage">Percentage</option>
//             </select>

//           </div>
//         ))}

//         <button onClick={addMetric}>+ Add Metric</button>
//         <button onClick={handleSubmit}>Save Module</button>

//       </div>

//       {/* ASSIGN */}
//       <div className="card">

//         <h3>Assign Module</h3>

//         <input
//           placeholder="Username"
//           onChange={(e) => setUsername(e.target.value)}
//         />

//         <select
//           onChange={(e) => setModuleIdForAccess(e.target.value)}
//         >
//           <option>Select Module</option>
//           {modules.map((m) => (
//             <option key={m.id} value={m.id}>
//               {m.moduleName}
//             </option>
//           ))}
//         </select>

//         <button onClick={assignModule}>
//           Assign
//         </button>

//       </div>

//       {/* MODULE LIST */}
//       <div className="card">

//         <h3>Modules</h3>

//         {modules.length === 0 && <p>No modules</p>}

//         {modules.map((mod) => (
//           <div key={mod.id}>

//             <strong>{mod.moduleName}</strong>

//             <ul>
//               {mod.metrics.map((m, i) => (
//                 <li key={i}>
//                   {m.key} ({m.type})
//                 </li>
//               ))}
//             </ul>

//             <button onClick={() => handleDelete(mod.id)}>
//               Delete
//             </button>

//           </div>
//         ))}

//       </div>

//     </div>
//   );
// }

// export default AdminDashboardConfig;


import { useState, useEffect } from "react";
import "../Styles/adminConfig.css";
import DeleteIcon from "@mui/icons-material/Delete";

function AdminDashboardConfig() {

  // 🔥 IMPORTANT: now modules is OBJECT, not array
  const [modules, setModules] = useState({});

  const [moduleName, setModuleName] = useState("");
  const [metrics, setMetrics] = useState([
    { key: "", url: "", type: "count" }
  ]);

  const [username, setUsername] = useState("");
  const [moduleNameForAccess, setModuleNameForAccess] = useState("");

  // 📥 LOAD MODULES
  useEffect(() => {
    loadModules();
  }, []);

  const loadModules = async () => {
    const res = await fetch("http://localhost:8282/api/dashboard/modules");
    const data = await res.json();
    console.log("Loaded modules:", data);

    setModules(data); // ✅ object
  };

  // ➕ Add Metric
  const addMetric = () => {
    setMetrics([...metrics, { key: "", url: "", type: "count" }]);
  };

  // 🔄 Update Metric
  const handleMetricChange = (i, field, value) => {
    const updated = [...metrics];
    updated[i][field] = value;
    setMetrics(updated);
  };

  // 💾 SAVE MODULE
  const handleSubmit = async () => {
    const payload = { moduleName, metrics };

    await fetch("http://localhost:8282/api/dashboard/modules", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    await loadModules(); // ✅ reload full list

    setModuleName("");
    setMetrics([{ key: "", url: "", type: "count" }]);
  };

  // ❌ DELETE (by module name)
  const handleDelete = async (moduleName) => {
    await fetch(`http://localhost:8282/api/dashboard/modules/${moduleName}`, {
      method: "DELETE"
    });

    await loadModules();
  };

  // 🔐 ASSIGN (using module name)
  const assignModule = async () => {
    await fetch("http://localhost:8282/api/dashboard/assign", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
  username,
  moduleId: Number(moduleNameForAccess)
})
    });

    alert("Assigned successfully");
  };

  return (
    <div className="admin-container">

      <h2>Admin Dashboard Config</h2>

      {/* CREATE MODULE */}
      <div className="card">

        <input
          placeholder="Module Name"
          value={moduleName}
          onChange={(e) => setModuleName(e.target.value)}
        />

        <h4>Metrics</h4>

        {metrics.map((m, i) => (
          <div key={i} className="metric-row">

            <input
              placeholder="Key"
              value={m.key}
              onChange={(e) =>
                handleMetricChange(i, "key", e.target.value)
              }
            />

            <input
              placeholder="URL"
              value={m.url}
              onChange={(e) =>
                handleMetricChange(i, "url", e.target.value)
              }
            />

            <select
              value={m.type}
              onChange={(e) =>
                handleMetricChange(i, "type", e.target.value)
              }
            >
              <option value="count">Count</option>
              <option value="graph">Graph</option>
              <option value="list">Table</option>
              <option value="percentage">Percentage</option>
            </select>

          </div>
        ))}

        <button onClick={addMetric}>+ Add Metric</button>
        <button className="primary-btn" onClick={handleSubmit}>
          Save Module
        </button>

      </div>

      {/* ASSIGN */}
      <div className="card">

        <h3>Assign Module</h3>

        <input
          placeholder="Username"
          onChange={(e) => setUsername(e.target.value)}
        />

        <select
          onChange={(e) => setModuleNameForAccess(e.target.value)}
        >
          <option>Select Module</option>

          {/* ✅ FIXED */}
          {Object.entries(modules).map(([name, data]) => (
  <option key={data.id} value={data.id}>
    {name}
  </option>
))}

        </select>

        <button onClick={assignModule}>
          Assign
        </button>

      </div>

      {/* MODULE LIST */}
      <div className="card">

        <h3>Modules</h3>

        {Object.keys(modules).length === 0 && <p>No modules</p>}

        {/* ✅ FIXED */}
        {Object.entries(modules).map(([moduleName, data]) => (
  <div key={moduleName} className="module-box-admin-config">

    <strong>{moduleName}</strong>

    <ul>
      {data.metrics.map((m, i) => (
        <li key={i}>
          {m.key} ({m.type})
        </li>
      ))}
    </ul>

    <button onClick={() => handleDelete(moduleName)}>
      <DeleteIcon fontSize="small" />
    </button>

  </div>
))}

      </div>

    </div>
  );
}

export default AdminDashboardConfig;