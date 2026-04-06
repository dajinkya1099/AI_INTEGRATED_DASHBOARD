// import { useEffect, useState } from "react";
// import WidgetCard from "../Components/WidgetCard";
// import GraphCard from "../Components/GraphCard";
// import TableCard from "../Components/TableCard";
// import ProgressCard from "../Components/ProgressCard";

// function Dashboard() {
//   const [data, setData] = useState([]);

//   const user = JSON.parse(localStorage.getItem("user"));

//   useEffect(() => {
//   fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
//     .then((res) => res.json())
//     .then((res) => {
//       console.log("Dashboard API Response:", res); // 👈 LOG HERE
//       setData(res.selections || []);
//     })
//     .catch((err) => console.error("API Error:", err));
// }, []);

//   return (
//     <div style={{ padding: "20px" }}>
//       <h2>Dashboard</h2>

//       {data.map((module) => (
//         <div key={module.module}>

//           <h3>{module.module}</h3>

//           <div style={styles.grid}>
//             {module.metrics.map((metric) => {

//               if (metric.type === "count") {
//                 return <WidgetCard key={metric.key} metric={metric} />;
//               }

//               if (metric.type === "percentage") {
//                 return <ProgressCard key={metric.key} metric={metric} />;
//               }

//               if (metric.type === "list") {
//                 return <TableCard key={metric.key} metric={metric} />;
//               }

//               if (metric.type === "graph") {
//                 return <GraphCard key={metric.key} metric={metric} />;
//               }

//               return null;
//             })}
//           </div>

//         </div>
//       ))}
//     </div>
//   );
// }

// const styles = {
//   grid: {
//     display: "grid",
//     gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
//     gap: "20px",
//   }
// };

// export default Dashboard;


// import { useEffect, useState } from "react";
// import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

// import WidgetCard from "../Components/WidgetCard";
// import GraphCard from "../Components/GraphCard";
// import TableCard from "../Components/TableCard";
// import ProgressCard from "../Components/ProgressCard";

// import RefreshIcon from "@mui/icons-material/Refresh";
// import CloseIcon from "@mui/icons-material/Close";

// import "../Styles/dashboard.css";

// function Dashboard() {
//   const [data, setData] = useState([]);
//   const [refreshMap, setRefreshMap] = useState({});

//   const user = JSON.parse(localStorage.getItem("user"));

//   // ✅ FETCH CONFIG
//   useEffect(() => {
//     fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
//       .then((res) => res.json())
//       .then((res) => {
//         console.log("Dashboard Config:", res);
//         setData(res.selections || []);
//       })
//       .catch((err) => console.error(err));
//   }, []);

//   // ✅ REFRESH SINGLE WIDGET
//   const handleRefresh = (metricKey) => {
//     setRefreshMap((prev) => ({
//       ...prev,
//       [metricKey]: Date.now()
//     }));
//   };

//   // ✅ REMOVE WIDGET
//   const removeWidget = (moduleIndex, metricIndex) => {
//     const updated = [...data];

//     updated[moduleIndex].metrics.splice(metricIndex, 1);

//     if (updated[moduleIndex].metrics.length === 0) {
//       updated.splice(moduleIndex, 1);
//     }

//     setData(updated);
//   };

//   // ✅ DRAG HANDLE (optional)
//   const handleDragEnd = (result) => {
//     if (!result.destination) return;

//     const items = Array.from(data);
//     const [moved] = items.splice(result.source.index, 1);
//     items.splice(result.destination.index, 0, moved);

//     setData(items);
//   };

//   // ✅ RENDER COMPONENT
//   const renderComponent = (metric, refreshKey) => {
//     switch (metric.type) {
//       case "count":
//         return <WidgetCard metric={metric} refreshKey={refreshKey} />;

//       case "percentage":
//         return <ProgressCard metric={metric} refreshKey={refreshKey} />;

//       case "list":
//         return <TableCard metric={metric} refreshKey={refreshKey} />;

//       case "graph":
//         return <GraphCard metric={metric} refreshKey={refreshKey} />;

//       default:
//         return <p>Unsupported widget</p>;
//     }
//   };

//   return (
//     <div className="dashboard-container">
//       <DragDropContext onDragEnd={handleDragEnd}>
//         <Droppable droppableId="modules">
//           {(provided) => (
//             <div ref={provided.innerRef} {...provided.droppableProps}>

//               {data.map((module, moduleIndex) => (
//                 <Draggable
//                   key={module.module}
//                   draggableId={module.module}
//                   index={moduleIndex}
//                 >
//                   {(provided) => (
//                     <div
//                       className="module-card"
//                       ref={provided.innerRef}
//                       {...provided.draggableProps}
//                     >

//                       {/* MODULE HEADER */}
//                       <div
//                         className="module-header"
//                         {...provided.dragHandleProps}
//                       >
//                         {module.module}
//                       </div>

//                       {/* WIDGET GRID */}
//                       <div className="widget-grid">

//                         {module.metrics.map((metric, metricIndex) => {

//                           const key = metric.key; // ✅ BEST UNIQUE KEY

//                           return (
//                             <div
//                               key={metric.key}
//                               className={`widget-wrapper ${metric.type === "list" ? "full-width" : ""
//                                 }`}
//                             >

//                               {/* TOP BAR */}
//                               <div className="widget-topbar">
//                                 <span>{metric.key}</span>

//                                 <div>
//                                   {/* 🔄 REFRESH */}
//                                   <button
//                                     className="icon-btn"
//                                     onClick={() => handleRefresh(metric.key)}
//                                   >
//                                     <RefreshIcon fontSize="small" />
//                                   </button>

//                                   {/* ❌ REMOVE */}
//                                   <button
//                                     className="icon-btn"
//                                     onClick={() =>
//                                       removeWidget(moduleIndex, metricIndex)
//                                     }
//                                   >
//                                     <CloseIcon fontSize="small" />
//                                   </button>
//                                 </div>
//                               </div>

//                               {/* BODY */}
//                               <div className="card-body">
//                                 {renderComponent(metric, refreshMap[key])}
//                               </div>

//                             </div>
//                           );
//                         })}

//                       </div>
//                     </div>
//                   )}
//                 </Draggable>
//               ))}

//               {provided.placeholder}
//             </div>
//           )}
//         </Droppable>
//       </DragDropContext>

//     </div>
//   );
// }

// export default Dashboard;















//Ajinkya Final Code


// import { useEffect, useState } from "react";
// import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

// import WidgetCard from "../Components/WidgetCard";
// import GraphCard from "../Components/GraphCard";
// import TableCard from "../Components/TableCard";
// import ProgressCard from "../Components/ProgressCard";

// import RefreshIcon from "@mui/icons-material/Refresh";
// import CloseIcon from "@mui/icons-material/Close";

// import "../Styles/dashboard.css";

// function Dashboard() {
//   const [data, setData] = useState([]);
//   const [refreshMap, setRefreshMap] = useState({});

//   const user = JSON.parse(localStorage.getItem("user"));

//   // ✅ FETCH CONFIG
//   useEffect(() => {
//     fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
//       .then((res) => res.json())
//       .then((res) => {
//         console.log("Dashboard Config:", res);
//         setData(res.selections || []);
//       })
//       .catch((err) => console.error(err));
//   }, []);

//   // ✅ REFRESH SINGLE WIDGET
//   const handleRefresh = (metricKey) => {
//     setRefreshMap((prev) => ({
//       ...prev,
//       [metricKey]: Date.now()
//     }));
//   };

//   // ✅ REMOVE WIDGET
//   const removeWidget = (moduleIndex, metricIndex) => {
//     const updated = [...data];

//     updated[moduleIndex].metrics.splice(metricIndex, 1);

//     if (updated[moduleIndex].metrics.length === 0) {
//       updated.splice(moduleIndex, 1);
//     }

//     setData(updated);
//   };

//   // ✅ DRAG LOGIC (MODULE + WIDGET)
//   const handleDragEnd = (result) => {
//     const { source, destination, type } = result;

//     if (!destination) return;

//     // 🔥 MODULE DRAG
//     if (type === "MODULE") {
//       const items = Array.from(data);
//       const [moved] = items.splice(source.index, 1);
//       items.splice(destination.index, 0, moved);
//       setData(items);
//     }

//     // 🔥 WIDGET DRAG (INSIDE MODULE)
//     if (type === "WIDGET") {
//       const moduleIndex = parseInt(source.droppableId);

//       const updated = [...data];
//       const widgets = Array.from(updated[moduleIndex].metrics);

//       const [moved] = widgets.splice(source.index, 1);
//       widgets.splice(destination.index, 0, moved);

//       updated[moduleIndex].metrics = widgets;
//       setData(updated);
//     }
//   };

//   // ✅ RENDER COMPONENT
//   const renderComponent = (metric, refreshKey) => {
//     switch (metric.type) {
//       case "count":
//         return <WidgetCard metric={metric} refreshKey={refreshKey} />;

//       case "percentage":
//         return <ProgressCard metric={metric} refreshKey={refreshKey} />;

//       case "list":
//         return <TableCard metric={metric} refreshKey={refreshKey} />;

//       case "graph":
//         return <GraphCard metric={metric} refreshKey={refreshKey} />;

//       default:
//         return <p>Unsupported widget</p>;
//     }
//   };

//   return (
//     <div className="dashboard-container">
//       <DragDropContext onDragEnd={handleDragEnd}>
        
//         {/* 🔥 MODULE DROPPABLE */}
//         <Droppable droppableId="modules" type="MODULE">
//           {(provided) => (
//             <div ref={provided.innerRef} {...provided.droppableProps}>

//               {data.map((module, moduleIndex) => (
//                 <Draggable
//                   key={module.module}
//                   draggableId={module.module}
//                   index={moduleIndex}
//                 >
//                   {(provided) => (
//                     <div
//                       className="module-card"
//                       ref={provided.innerRef}
//                       {...provided.draggableProps}
//                     >

//                       {/* MODULE HEADER */}
//                       <div
//                         className="module-header"
//                         {...provided.dragHandleProps}
//                       >
//                         {module.module}
//                       </div>

//                       {/* 🔥 WIDGET DROPPABLE */}
//                       <Droppable
//                         droppableId={`${moduleIndex}`}
//                         type="WIDGET"
//                       >
//                         {(provided) => (
//                           <div
//                             className="widget-grid"
//                             ref={provided.innerRef}
//                             {...provided.droppableProps}
//                           >

//                             {module.metrics.map((metric, metricIndex) => {
//                               const key = metric.key;

//                               return (
//                                 <Draggable
//                                   key={`${moduleIndex}-${metric.key}`}
//                                   draggableId={`${moduleIndex}-${metric.key}`}
//                                   index={metricIndex}
//                                 >
//                                   {(provided) => (
//                                     <div
//                                       ref={provided.innerRef}
//                                       {...provided.draggableProps}
//                                       {...provided.dragHandleProps}
//                                       className={`widget-wrapper 
//                                         ${metric.type === "list" ? "large" : ""}
//                                         ${metric.type === "graph" ? "medium" : ""}
//                                         ${metric.type === "count" || metric.type === "percentage" ? "small" : ""}
//                                       `}
//                                     >

//                                       {/* TOP BAR */}
//                                       <div className="widget-topbar">
//                                         <span>{metric.key}</span>

//                                         <div className="widget-actions">
//                                           <button
//                                             className="icon-btn"
//                                             onClick={() =>
//                                               handleRefresh(metric.key)
//                                             }
//                                           >
//                                             <RefreshIcon fontSize="small" />
//                                           </button>

//                                           <button
//                                             className="icon-btn"
//                                             onClick={() =>
//                                               removeWidget(
//                                                 moduleIndex,
//                                                 metricIndex
//                                               )
//                                             }
//                                           >
//                                             <CloseIcon fontSize="small" />
//                                           </button>
//                                         </div>
//                                       </div>

//                                       {/* BODY */}
//                                       <div className="card-body">
//                                         {renderComponent(
//                                           metric,
//                                           refreshMap[key]
//                                         )}
//                                       </div>

//                                     </div>
//                                   )}
//                                 </Draggable>
//                               );
//                             })}

//                             {provided.placeholder}
//                           </div>
//                         )}
//                       </Droppable>

//                     </div>
//                   )}
//                 </Draggable>
//               ))}

//               {provided.placeholder}
//             </div>
//           )}
//         </Droppable>

//       </DragDropContext>
//     </div>
//   );
// }

// export default Dashboard;





















// import { useEffect, useState, useRef } from "react";
// import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

// import WidgetCard       from "../Components/WidgetCard";
// import GraphCard        from "../Components/GraphCard";
// import TableCard        from "../Components/TableCard";
// import ProgressCard     from "../Components/ProgressCard";
// import DashboardChatbot from "../Components/DashboardChatbot";   // ← NEW

// import RefreshIcon from "@mui/icons-material/Refresh";
// import CloseIcon   from "@mui/icons-material/Close";

// import "../Styles/dashboard.css";

// function Dashboard() {
//   const [data, setData]             = useState([]);
//   const [refreshMap, setRefreshMap] = useState({});
//   const [schemaName, setSchemaName] = useState("");

//   // ── Auto-detect which module is most visible on screen ───────────────────
//   const [activeModule, setActiveModule] = useState("");
//   const moduleRefs = useRef({});   // { moduleName: DOM element }

//   const user = JSON.parse(localStorage.getItem("user"));

//   // ── Fetch dashboard config ────────────────────────────────────────────────
//   useEffect(() => {
//     fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
//       .then(res => res.json())
//       .then(res => {
//         setData(res.selections || []);
//         setSchemaName(res.schemaName || res.schema || "");
//       })
//       .catch(err => console.error(err));
//   }, []);

//   // ── IntersectionObserver — track which module is most visible ─────────────
//   useEffect(() => {
//     if (!data.length) return;

//     const observers = [];

//     data.forEach(module => {
//       const el = moduleRefs.current[module.module];
//       if (!el) return;

//       const obs = new IntersectionObserver(
//         ([entry]) => {
//           // When module is >50% visible, mark it as active
//           if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
//             setActiveModule(module.module);
//           }
//         },
//         { threshold: 0.5 }
//       );

//       obs.observe(el);
//       observers.push(obs);
//     });

//     // Set first module as default active
//     if (data[0]) setActiveModule(data[0].module);

//     return () => observers.forEach(o => o.disconnect());
//   }, [data]);

//   // ── Refresh single widget ─────────────────────────────────────────────────
//   const handleRefresh = (metricKey) => {
//     setRefreshMap(prev => ({ ...prev, [metricKey]: Date.now() }));
//   };

//   // ── Remove widget ─────────────────────────────────────────────────────────
//   const removeWidget = (moduleIndex, metricIndex) => {
//     const updated = [...data];
//     updated[moduleIndex].metrics.splice(metricIndex, 1);
//     if (updated[moduleIndex].metrics.length === 0) updated.splice(moduleIndex, 1);
//     setData(updated);
//   };

//   // ── Drag logic ────────────────────────────────────────────────────────────
//   const handleDragEnd = ({ source, destination, type }) => {
//     if (!destination) return;

//     if (type === "MODULE") {
//       const items = Array.from(data);
//       const [moved] = items.splice(source.index, 1);
//       items.splice(destination.index, 0, moved);
//       setData(items);
//     }

//     if (type === "WIDGET") {
//       const idx = parseInt(source.droppableId);
//       const updated = [...data];
//       const widgets = Array.from(updated[idx].metrics);
//       const [moved] = widgets.splice(source.index, 1);
//       widgets.splice(destination.index, 0, moved);
//       updated[idx].metrics = widgets;
//       setData(updated);
//     }
//   };

//   // ── Render widget by type ─────────────────────────────────────────────────
//   const renderComponent = (metric, refreshKey) => {
//     switch (metric.type) {
//       case "count":      return <WidgetCard   metric={metric} refreshKey={refreshKey} />;
//       case "percentage": return <ProgressCard metric={metric} refreshKey={refreshKey} />;
//       case "list":       return <TableCard    metric={metric} refreshKey={refreshKey} />;
//       case "graph":      return <GraphCard    metric={metric} refreshKey={refreshKey} />;
//       default:           return <p>Unsupported widget</p>;
//     }
//   };

//   return (
//     <div className="dashboard-container">
//       <DragDropContext onDragEnd={handleDragEnd}>

//         <Droppable droppableId="modules" type="MODULE">
//           {(provided) => (
//             <div ref={provided.innerRef} {...provided.droppableProps}>

//               {data.map((module, moduleIndex) => (
//                 <Draggable
//                   key={module.module}
//                   draggableId={module.module}
//                   index={moduleIndex}
//                 >
//                   {(provided) => (
//                     <div
//                       className="module-card"
//                       ref={el => {
//                         provided.innerRef(el);
//                         moduleRefs.current[module.module] = el; // ← track ref for IntersectionObserver
//                       }}
//                       {...provided.draggableProps}
//                     >
//                       {/* Module header */}
//                       <div className="module-header" {...provided.dragHandleProps}>
//                         {module.module}
//                       </div>

//                       <Droppable droppableId={`${moduleIndex}`} type="WIDGET">
//                         {(provided) => (
//                           <div className="widget-grid" ref={provided.innerRef} {...provided.droppableProps}>

//                             {module.metrics.map((metric, metricIndex) => (
//                               <Draggable
//                                 key={`${moduleIndex}-${metric.key}`}
//                                 draggableId={`${moduleIndex}-${metric.key}`}
//                                 index={metricIndex}
//                               >
//                                 {(provided) => (
//                                   <div
//                                     ref={provided.innerRef}
//                                     {...provided.draggableProps}
//                                     {...provided.dragHandleProps}
//                                     className={`widget-wrapper
//                                       ${metric.type === "list"       ? "large"  : ""}
//                                       ${metric.type === "graph"      ? "medium" : ""}
//                                       ${metric.type === "count" || metric.type === "percentage" ? "small" : ""}
//                                     `}
//                                   >
//                                     {/* Top bar */}
//                                     <div className="widget-topbar">
//                                       <span>{metric.key}</span>
//                                       <div className="widget-actions">
//                                         <button className="icon-btn" onClick={() => handleRefresh(metric.key)}>
//                                           <RefreshIcon fontSize="small" />
//                                         </button>
//                                         <button className="icon-btn" onClick={() => removeWidget(moduleIndex, metricIndex)}>
//                                           <CloseIcon fontSize="small" />
//                                         </button>
//                                       </div>
//                                     </div>

//                                     {/* Widget body */}
//                                     <div className="card-body">
//                                       {renderComponent(metric, refreshMap[metric.key])}
//                                     </div>
//                                   </div>
//                                 )}
//                               </Draggable>
//                             ))}

//                             {provided.placeholder}
//                           </div>
//                         )}
//                       </Droppable>
//                     </div>
//                   )}
//                 </Draggable>
//               ))}

//               {provided.placeholder}
//             </div>
//           )}
//         </Droppable>

//       </DragDropContext>

//       {/* ── CHATBOT — auto-detects current module ── */}
//       <DashboardChatbot
//         schemaName={schemaName}
//         activeModule={activeModule}
//         dashboardData={data}
//       />
//     </div>
//   );
// }

// export default Dashboard;








import { useEffect, useState } from "react";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

import WidgetCard       from "../Components/WidgetCard";
import GraphCard        from "../Components/GraphCard";
import TableCard        from "../Components/TableCard";
import ProgressCard     from "../Components/ProgressCard";
import DashboardChatbot from "../Components/DashboardChatbot";

import RefreshIcon from "@mui/icons-material/Refresh";
import CloseIcon   from "@mui/icons-material/Close";

import "../Styles/dashboard.css";

function Dashboard() {
  const [data, setData]             = useState([]);
  const [refreshMap, setRefreshMap] = useState({});

  const user = JSON.parse(localStorage.getItem("user") || "{}");

  // ── Fetch config ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!user?.username) return;

    fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
      .then(res => res.json())
      .then(res => {
        console.log("Dashboard Config:", res);
        setData(res.selections || []);
      })
      .catch(err => console.error("Dashboard config error:", err));
  }, []);

  // ── Refresh ───────────────────────────────────────────────────────────────
  const handleRefresh = (metricKey) => {
    setRefreshMap(prev => ({ ...prev, [metricKey]: Date.now() }));
  };

  // ── Remove widget ─────────────────────────────────────────────────────────
  const removeWidget = (moduleIndex, metricIndex) => {
    const updated = [...data];
    updated[moduleIndex].metrics.splice(metricIndex, 1);
    if (updated[moduleIndex].metrics.length === 0) updated.splice(moduleIndex, 1);
    setData([...updated]);
  };

  // ── Drag ──────────────────────────────────────────────────────────────────
  const handleDragEnd = ({ source, destination, type }) => {
    if (!destination) return;

    if (type === "MODULE") {
      const items = [...data];
      const [moved] = items.splice(source.index, 1);
      items.splice(destination.index, 0, moved);
      setData(items);
    }

    if (type === "WIDGET") {
      const idx = parseInt(source.droppableId);
      const updated = [...data];
      const widgets = [...updated[idx].metrics];
      const [moved] = widgets.splice(source.index, 1);
      widgets.splice(destination.index, 0, moved);
      updated[idx] = { ...updated[idx], metrics: widgets };
      setData(updated);
    }
  };

  // ── Render widget ─────────────────────────────────────────────────────────
  const renderComponent = (metric, refreshKey) => {
    switch (metric.type) {
      case "count":      return <WidgetCard   metric={metric} refreshKey={refreshKey} />;
      case "percentage": return <ProgressCard metric={metric} refreshKey={refreshKey} />;
      case "list":       return <TableCard    metric={metric} refreshKey={refreshKey} />;
      case "graph":      return <GraphCard    metric={metric} refreshKey={refreshKey} />;
      default:           return <p>Unsupported: {metric.type}</p>;
    }
  };

  return (
    <div className="dashboard-container">
      <DragDropContext onDragEnd={handleDragEnd}>

        <Droppable droppableId="modules" type="MODULE">
          {(provided) => (
            <div ref={provided.innerRef} {...provided.droppableProps}>

              {data.map((module, moduleIndex) => (
                <Draggable
                  key={module.module}
                  draggableId={module.module}
                  index={moduleIndex}
                >
                  {(provided) => (
                    <div
                      className="module-card"
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                    >
                      <div className="module-header" {...provided.dragHandleProps}>
                        {module.module}
                      </div>

                      <Droppable droppableId={`${moduleIndex}`} type="WIDGET">
                        {(provided) => (
                          <div
                            className="widget-grid"
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                          >
                            {module.metrics.map((metric, metricIndex) => (
                              <Draggable
                                key={`${moduleIndex}-${metric.key}`}
                                draggableId={`${moduleIndex}-${metric.key}`}
                                index={metricIndex}
                              >
                                {(provided) => (
                                  <div
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    {...provided.dragHandleProps}
                                    className={`widget-wrapper
                                      ${metric.type === "list"       ? "large"  : ""}
                                      ${metric.type === "graph"      ? "medium" : ""}
                                      ${metric.type === "count" || metric.type === "percentage" ? "small" : ""}
                                    `}
                                  >
                                    <div className="widget-topbar">
                                      <span>{metric.key}</span>
                                      <div className="widget-actions">
                                        <button className="icon-btn" onClick={() => handleRefresh(metric.key)}>
                                          <RefreshIcon fontSize="small" />
                                        </button>
                                        <button className="icon-btn" onClick={() => removeWidget(moduleIndex, metricIndex)}>
                                          <CloseIcon fontSize="small" />
                                        </button>
                                      </div>
                                    </div>
                                    <div className="card-body">
                                      {renderComponent(metric, refreshMap[metric.key])}
                                    </div>
                                  </div>
                                )}
                              </Draggable>
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>
                    </div>
                  )}
                </Draggable>
              ))}

              {provided.placeholder}
            </div>
          )}
        </Droppable>

      </DragDropContext>

      {/* Chatbot — no props needed, manages schema internally */}
      <DashboardChatbot />
    </div>
  );
}

export default Dashboard;