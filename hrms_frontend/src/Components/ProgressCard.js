// import { useEffect, useState } from "react";

// function ProgressCard({ metric, refreshKey }) {

//   const [value, setValue] = useState(0);

//   const fetchData = () => {
//     fetch(`http://localhost:8282${metric.url}`)
//       .then(res => res.json())
//       .then(res => setValue(res.value));
//   };

//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]);

//   return (
//     <div style={styles.card}>
//       <h4>{metric.key}</h4>

//       <div>
//   <div className="progress-bar">
//     <div
//       className="progress-fill"
//       style={{ width: `${value || 0}%` }}
//     ></div>
//   </div>
//   <p>{value || 0}%</p>
// </div>
//     </div>
//   );
// }

// const styles = {
//   card: {
//     background: "white",
//     padding: "20px",
//     borderRadius: "10px"
//   }
// };

// export default ProgressCard;

import { useEffect, useState } from "react";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

import "../Styles/progressCard.css"; // ✅ IMPORT CSS

function ProgressCard({ metric, refreshKey }) {
  const [value, setValue] = useState(0);

  const fetchData = () => {
    fetch(`http://localhost:8282${metric.url}`)
      .then(res => res.json())
      .then(res => setValue(res.value || 0));
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // 🎨 Dynamic color
  const getColor = (val) => {
    if (val < 40) return "#ef4444";
    if (val < 70) return "#f59e0b";
    return "#22c55e";
  };

  const color = getColor(value);

  return (
    <div className="progress-card">

      {/* <h4 className="progress-title">{metric.key}</h4> */}

      {/* 🔵 Circular */}
      <Box className="circular-wrapper">
        <CircularProgress
          variant="determinate"
          value={value}
          size={90}
          thickness={5}
          style={{ color }}
        />

        <Box className="circular-text">
          <Typography variant="h6" style={{ fontWeight: "bold" }}>
            {value}%
          </Typography>
        </Box>
      </Box>

      {/* 📊 Linear */}
      <div className="progress-container">
        <div
          className="progress-fill"
          style={{
            width: `${value}%`,
            background: color
          }}
        />
      </div>

    </div>
  );
}

export default ProgressCard;