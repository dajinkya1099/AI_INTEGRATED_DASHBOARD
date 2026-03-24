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


import { useEffect, useState } from "react";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

import WidgetCard from "../Components/WidgetCard";
import GraphCard from "../Components/GraphCard";
import TableCard from "../Components/TableCard";
import ProgressCard from "../Components/ProgressCard";

import RefreshIcon from "@mui/icons-material/Refresh";
import CloseIcon from "@mui/icons-material/Close";

import "../Styles/dashboard.css";

function Dashboard() {
  const [data, setData] = useState([]);
  const [refreshMap, setRefreshMap] = useState({});

  const user = JSON.parse(localStorage.getItem("user"));

  // ✅ FETCH CONFIG
  useEffect(() => {
    fetch(`http://localhost:8282/get-dashboard-config/${user.username}`)
      .then((res) => res.json())
      .then((res) => {
        console.log("Dashboard Config:", res);
        setData(res.selections || []);
      })
      .catch((err) => console.error(err));
  }, []);

  // ✅ REFRESH SINGLE WIDGET
  const handleRefresh = (metricKey) => {
    setRefreshMap((prev) => ({
      ...prev,
      [metricKey]: Date.now()
    }));
  };

  // ✅ REMOVE WIDGET
  const removeWidget = (moduleIndex, metricIndex) => {
    const updated = [...data];

    updated[moduleIndex].metrics.splice(metricIndex, 1);

    if (updated[moduleIndex].metrics.length === 0) {
      updated.splice(moduleIndex, 1);
    }

    setData(updated);
  };

  // ✅ DRAG LOGIC (MODULE + WIDGET)
  const handleDragEnd = (result) => {
    const { source, destination, type } = result;

    if (!destination) return;

    // 🔥 MODULE DRAG
    if (type === "MODULE") {
      const items = Array.from(data);
      const [moved] = items.splice(source.index, 1);
      items.splice(destination.index, 0, moved);
      setData(items);
    }

    // 🔥 WIDGET DRAG (INSIDE MODULE)
    if (type === "WIDGET") {
      const moduleIndex = parseInt(source.droppableId);

      const updated = [...data];
      const widgets = Array.from(updated[moduleIndex].metrics);

      const [moved] = widgets.splice(source.index, 1);
      widgets.splice(destination.index, 0, moved);

      updated[moduleIndex].metrics = widgets;
      setData(updated);
    }
  };

  // ✅ RENDER COMPONENT
  const renderComponent = (metric, refreshKey) => {
    switch (metric.type) {
      case "count":
        return <WidgetCard metric={metric} refreshKey={refreshKey} />;

      case "percentage":
        return <ProgressCard metric={metric} refreshKey={refreshKey} />;

      case "list":
        return <TableCard metric={metric} refreshKey={refreshKey} />;

      case "graph":
        return <GraphCard metric={metric} refreshKey={refreshKey} />;

      default:
        return <p>Unsupported widget</p>;
    }
  };

  return (
    <div className="dashboard-container">
      <DragDropContext onDragEnd={handleDragEnd}>
        
        {/* 🔥 MODULE DROPPABLE */}
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

                      {/* MODULE HEADER */}
                      <div
                        className="module-header"
                        {...provided.dragHandleProps}
                      >
                        {module.module}
                      </div>

                      {/* 🔥 WIDGET DROPPABLE */}
                      <Droppable
                        droppableId={`${moduleIndex}`}
                        type="WIDGET"
                      >
                        {(provided) => (
                          <div
                            className="widget-grid"
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                          >

                            {module.metrics.map((metric, metricIndex) => {
                              const key = metric.key;

                              return (
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
                                        ${metric.type === "list" ? "large" : ""}
                                        ${metric.type === "graph" ? "medium" : ""}
                                        ${metric.type === "count" || metric.type === "percentage" ? "small" : ""}
                                      `}
                                    >

                                      {/* TOP BAR */}
                                      <div className="widget-topbar">
                                        <span>{metric.key}</span>

                                        <div className="widget-actions">
                                          <button
                                            className="icon-btn"
                                            onClick={() =>
                                              handleRefresh(metric.key)
                                            }
                                          >
                                            <RefreshIcon fontSize="small" />
                                          </button>

                                          <button
                                            className="icon-btn"
                                            onClick={() =>
                                              removeWidget(
                                                moduleIndex,
                                                metricIndex
                                              )
                                            }
                                          >
                                            <CloseIcon fontSize="small" />
                                          </button>
                                        </div>
                                      </div>

                                      {/* BODY */}
                                      <div className="card-body">
                                        {renderComponent(
                                          metric,
                                          refreshMap[key]
                                        )}
                                      </div>

                                    </div>
                                  )}
                                </Draggable>
                              );
                            })}

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
    </div>
  );
}

export default Dashboard;