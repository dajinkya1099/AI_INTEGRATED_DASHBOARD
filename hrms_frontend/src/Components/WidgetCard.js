// import { useEffect, useState } from "react";
// import RefreshIcon from "@mui/icons-material/Refresh";

// function WidgetCard({ metric, refreshKey }) {
//   const [value, setValue] = useState(null);
//   const [loading, setLoading] = useState(false);

//   const fetchData = async () => {
//     try {
//       setLoading(true);

//       const res = await fetch(`http://localhost:8282${metric.url}`);
//       const data = await res.json();

//       // ✅ handle different backend formats
//       if (typeof data === "number") {
//         setValue(data);
//       } else if (data.value !== undefined) {
//         setValue(data.value);
//       } else {
//         setValue(0);
//       }

//     } catch (err) {
//       console.error("Widget fetch error:", err);
//       setValue(0);
//     } finally {
//       setLoading(false);
//     }
//   };

//   // ✅ Initial load + refresh trigger
//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]); // 🔥 THIS FIXES YOUR REFRESH BUTTON

//   return (
//     <div style={styles.card}>

//       {/* <div style={styles.header}>
//         <h4 style={styles.title}>{metric.key}</h4>
//       </div> */}

//       <div style={styles.content}>
//         {loading ? (
//           <p style={styles.loading}>Loading...</p>
//         ) : (
//           <>
//             {metric.type === "count" && (
//               <h1 style={styles.value}>{value}</h1>
//             )}

//             {metric.type === "percentage" && (
//               <h2 style={styles.value}>{value}%</h2>
//             )}

//             {metric.type === "speedometer" && (
//               <h2 style={styles.value}>{value}% 🚀</h2>
//             )}
//           </>
//         )}
//       </div>

//     </div>
//   );
// }

// const styles = {
//   card: {
//     background: "#ffffff",
//     padding: "16px",
//     borderRadius: "14px",
//     boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
//     transition: "0.3s",
//     display: "flex",
//     flexDirection: "column",
//     justifyContent: "space-between"
//   },
//   header: {
//     display: "flex",
//     justifyContent: "space-between",
//     alignItems: "center"
//   },
//   title: {
//     margin: 0,
//     fontSize: "14px",
//     color: "#64748b"
//   },
//   icon: {
//     fontSize: "18px",
//     cursor: "pointer",
//     color: "#6366f1"
//   },
//   content: {
//     marginTop: "10px"
//   },
//   value: {
//     margin: 0,
//     fontSize: "28px",
//     fontWeight: "bold",
//     color: "#0f172a"
//   },
//   loading: {
//     fontSize: "14px",
//     color: "#94a3b8"
//   }
// };

// export default WidgetCard;

// import { useEffect, useState } from "react";
// import "../Styles/widgetCard.css";

// function WidgetCard({ metric, refreshKey }) {
//   const [value, setValue] = useState(null);
//   const [loading, setLoading] = useState(true);

//   const fetchData = async () => {
//     try {
//       setLoading(true);

//       const res = await fetch(`http://localhost:8282${metric.url}`);
//       const data = await res.json();

//       let finalValue = 0;

//       if (typeof data === "number") {
//         finalValue = data;
//       } else if (data.value !== undefined) {
//         finalValue = data.value;
//       }

//       setValue(finalValue);

//     } catch (err) {
//       console.error("Widget fetch error:", err);
//       setValue(0);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]);

//   return (
//     <div className="widget-card">

//       {/* Title */}
//       {/* <div className="widget-title">{metric.key}</div> */}

//       {/* Value */}
//       {loading ? (
//         <div className="widget-loading"></div>
//       ) : (
//         <>
//           {metric.type === "count" && (
//             <div className="widget-value">{value}</div>
//           )}

//           {metric.type === "percentage" && (
//             <div className="widget-value">{value}%</div>
//           )}

//           {metric.type === "speedometer" && (
//             <div className="widget-value">{value}% 🚀</div>
//           )}
//         </>
//       )}

//     </div>
//   );
// }

// export default WidgetCard;

// import { useEffect, useState } from "react";
// import "../Styles/widgetCard.css";

// function WidgetCard({ metric, refreshKey }) {
//   const [value, setValue] = useState(0);
//   const [displayValue, setDisplayValue] = useState(0);

//   const fetchData = async () => {
//     try {
//       const res = await fetch(`http://localhost:8282${metric.url}`);
//       const data = await res.json();
//       console.log("Fetched widget data:", data);
//       let finalValue = 0;

//       if (typeof data === "number") {
//         finalValue = data;
//       } else if (data.value !== undefined) {
//         finalValue = data.value;
//       }
//       console.log("Parsed widget value:", finalValue);
//       setValue(finalValue); // ✅ store actual value
//     } catch (err) {
//       console.error(err);
//       setValue(0);
//     }
//   };

//   // 🔥 API CALL
//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]);

//   // 🔥 ANIMATION (IMPORTANT FIX)
//   useEffect(() => {
//     let start = 0;
//     const duration = 800;
//     const increment = value / (duration / 16);

//     const counter = setInterval(() => {
//       start += increment;

//       if (start >= value) {
//         setDisplayValue(value); // ✅ FINAL VALUE FIX
//         clearInterval(counter);
//       } else {
//         setDisplayValue(Math.floor(start));
//       }
//     }, 16);

//     return () => clearInterval(counter);
//   }, [value]);

//   return (
//     <div className="widget-card">
//       {/* <div className="widget-title">{metric.key}</div> */}

//       <div className="widget-value">
//         {metric.type === "percentage"
//           ? `${displayValue}%`
//           : displayValue}
//       </div>
//     </div>
//   );
// }

// export default WidgetCard;

import { useEffect, useState } from "react";
import "../Styles/widgetCard.css";

function WidgetCard({ metric, refreshKey }) {
  const [value, setValue] = useState(0);
  const [displayValue, setDisplayValue] = useState(0);

  const fetchData = async () => {
    try {
      const res = await fetch(`http://localhost:8282${metric.url}`);
      const data = await res.json();

      let finalValue = 0;

      if (typeof data === "number") {
        finalValue = data;
      } else if (data.value !== undefined) {
        finalValue = data.value;
      }

      setValue(finalValue);
    } catch (err) {
      console.error(err);
      setValue(0);
    }
  };

  // 🔥 API CALL (runs on refresh click)
  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // 🔥 FORCE ANIMATION EVERY TIME refreshKey OR value changes
  useEffect(() => {
    let start = 0;
    setDisplayValue(0); // ✅ RESET TO ZERO ALWAYS

    const duration = 800;
    const increment = value / (duration / 16);

    const counter = setInterval(() => {
      start += increment;

      if (start >= value) {
        setDisplayValue(value);
        clearInterval(counter);
      } else {
        setDisplayValue(Math.floor(start));
      }
    }, 16);

    return () => clearInterval(counter);

  }, [value, refreshKey]); // ✅ IMPORTANT FIX

  return (
    <div className="widget-card">
      {/* <div className="widget-title">{metric.key}</div> */}

      <div className="widget-value">
        {metric.type === "percentage"
          ? `${displayValue}%`
          : displayValue}
      </div>
    </div>
  );
}

export default WidgetCard;