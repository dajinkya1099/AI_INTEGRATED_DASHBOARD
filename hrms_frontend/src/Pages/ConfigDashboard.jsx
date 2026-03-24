import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../Styles/configDashboard.css";
import DeleteIcon from "@mui/icons-material/Delete";

function ConfigDashboard() {

  const navigate = useNavigate();

  const [selectedModule, setSelectedModule] = useState("");
  const [config, setConfig] = useState([]);

  const user = JSON.parse(localStorage.getItem("user"));

  // ✅ LOAD SAVED CONFIG
  useEffect(() => {
    fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
      .then(res => res.json())
      .then(data => {
        if (data?.selections) {
          setConfig(data.selections);
        }
      })
      .catch(err => console.error(err));
  }, []);

  // ================= MASTER DATA =================
  // const modules = {
  //   "Human Resource Department": [
  //     { key: "Total Employees", url: "/emp/count/all", type: "count" },
  //     { key: "Employees by Department", url: "/employees/by-department", type: "graph" },
  //     { key: "Employee Marital Status", url: "/employees/by-employment-marital-status", type: "graph" },
  //     { key: "Employee VS Salary", url: "/employees/by-employment-salary", type: "graph" },
  //     { key: "Employee Directory", url: "/get/employee-list", type: "list" }
  //   ],
  //   "Payroll": [
  //     { key: "Payroll Processed", url: "/payroll/processed-rate", type: "percentage" }
  //   ],
  //   "Attendance": [
  //     { key: "Attendance Rate", url: "/attendance/rate-today", type: "percentage" }
  //   ]
  // };

  const [modules, setModules] = useState({});

  useEffect(() => {
    // 🔹 Load user saved config
    fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
      .then(res => res.json())
      .then(data => {
        if (data?.selections) {
          setConfig(data.selections);
        }
      })
      .catch(err => console.error(err));

    // 🔹 Load modules from backend
    fetch(`http://localhost:8282/api/dashboard/modules/${user.username}`)
      .then(res => res.json())
      .then(data => {
        console.log("Modules from backend:", data);
        setModules(data); // ✅ same format as before
      })
      .catch(err => console.error(err));

  }, []);

  // ================= ADD =================
  const addMetric = (metric) => {
    if (!selectedModule) return;

    setConfig(prev => {
      const existing = prev.find(m => m.module === selectedModule);

      if (existing) {
        const exists = existing.metrics.some(m => m.key === metric.key);
        if (exists) return prev;

        return prev.map(m =>
          m.module === selectedModule
            ? { ...m, metrics: [...m.metrics, metric] }
            : m
        );
      }

      return [...prev, { module: selectedModule, metrics: [metric] }];
    });
  };

  // ================= REMOVE =================
  const removeMetric = (moduleName, key) => {
    setConfig(prev =>
      prev
        .map(m =>
          m.module === moduleName
            ? { ...m, metrics: m.metrics.filter(x => x.key !== key) }
            : m
        )
        .filter(m => m.metrics.length > 0)
    );
  };

  // ================= SAVE =================
  const handleSave = async () => {

    const payload = {
      userId: user.username,
      selections: config
    };

    const res = await fetch("http://localhost:8282/save-dashboard-config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (data.success) {
      alert("Saved successfully");
      navigate("/dashboard");
    }
  };

  // ================= CHECK ALREADY ADDED =================
  const isAdded = (metric) => {
    const module = config.find(m => m.module === selectedModule);
    return module?.metrics.some(m => m.key === metric.key);
  };

  return (
    <div className="config-container">

      <h2>Configure Dashboard</h2>

      {/* SELECT MODULE */}
      <select
        className="config-dropdown"
        value={selectedModule}
        onChange={(e) => setSelectedModule(e.target.value)}
      >
        <option value="">Select Module</option>
        {Object.keys(modules).map(mod => (
          <option key={mod}>{mod}</option>
        ))}
      </select>

      {/* AVAILABLE METRICS */}
      {selectedModule && (
        <div className="metrics-box">
          <h3>Available Metrics</h3>

          {modules[selectedModule].map(metric => (
            <div key={metric.key} className="metric-item">
              <span>{metric.key}</span>

              <button
                disabled={isAdded(metric)}
                onClick={() => addMetric(metric)}
              >
                {isAdded(metric) ? "Added" : "Add"}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* SELECTED METRICS */}
      <div className="selected-box">
        {/* <h3>Selected Widgets</h3> */}

        {config.length === 0 && <p>No widgets selected</p>}

        {config.map(mod => (
          <div key={mod.module} className="module-box">

            <h4>{mod.module}</h4>

            {mod.metrics.map(m => (
              <div key={m.key} className="metric-item">
                <span>{m.key}</span>

                <button
                  className="icon-btn delete"
                  onClick={() => removeMetric(mod.module, m.key)}
                >
                  <DeleteIcon fontSize="small" />
                </button>
              </div>
            ))}

          </div>
        ))}
      </div>

      <button className="save-btn" onClick={handleSave}>
        Save Configuration
      </button>

    </div>
  );
}

export default ConfigDashboard;