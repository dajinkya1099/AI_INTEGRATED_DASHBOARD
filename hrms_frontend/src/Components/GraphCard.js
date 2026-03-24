// import { useEffect, useState } from "react";
// import { Bar } from "react-chartjs-2";
// import {
//   Chart as ChartJS,
//   BarElement,
//   CategoryScale,
//   LinearScale,
//   Tooltip,
//   Legend
// } from "chart.js";

// ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

// function GraphCard({ metric, refreshKey }) {
//   const [chartData, setChartData] = useState(null);

//   const fetchData = async () => {
//   try {
//     const res = await fetch(`http://localhost:8282${metric.url}`);
//     const data = await res.json();

//     console.log("Graph API Response:", data);

//     let labels = [];
//     let values = [];

//     //  CASE 1: backend sends array
//     if (Array.isArray(data)) {
//       labels = data.map((item) => item.label);
//       values = data.map((item) => item.value);
//     }

//     //  CASE 2: backend sends {labels, values}
//     else if (data.labels && data.values) {
//       labels = data.labels;
//       values = data.values;
//     }

//     else {
//       console.error("Invalid graph format:", data);
//       setChartData(null);
//       return;
//     }

//     setChartData({
//       labels,
//       datasets: [
//         {
//           label: metric.key,
//           data: values,
//           backgroundColor: "rgba(99,102,241,0.6)"
//         }
//       ]
//     });

//   } catch (err) {
//     console.error(err);
//     setChartData(null);
//   }
// };

//   useEffect(() => {
//     fetchData();
//   }, [refreshKey]);

//   return (
//     <div className="card-body">

//       {chartData ? (
//         <div className="graph-container">
//   {chartData ? <Bar data={chartData} /> : <p className="no-data">No data</p>}
// </div>
//       ) : (
//         <p className="no-data">No graph data available</p>
//       )}
//     </div>
//   );
// }

// export default GraphCard;


import { useEffect, useState, useRef } from "react";
import { Bar, Line, Pie } from "react-chartjs-2";
import { saveAs } from "file-saver";
import "../Styles/graphCard.css";

import {
  Chart as ChartJS,
  BarElement,
  LineElement,
  ArcElement,
  PointElement, 
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from "chart.js";

import zoomPlugin from "chartjs-plugin-zoom";

ChartJS.register(
  BarElement,
  LineElement,
  ArcElement,
  PointElement, 
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  zoomPlugin
);


function GraphCard({ metric, refreshKey }) {
  const [chartData, setChartData] = useState(null);
  const [chartType, setChartType] = useState("bar");

  const chartRef = useRef();

  const fetchData = async () => {
    try {
      const res = await fetch(`http://localhost:8282${metric.url}`);
      const data = await res.json();

      let labels = [];
      let values = [];

      if (Array.isArray(data)) {
        labels = data.map((item) => item.label);
        values = data.map((item) => item.value);
      } else if (data.labels && data.values) {
        labels = data.labels;
        values = data.values;
      } else {
        setChartData(null);
        return;
      }

      setChartData({
        labels,
        datasets: [
  {
    label: metric.key,
    data: values,
    backgroundColor: [
      "#6366f1",
      "#22c55e",
      "#f59e0b",
      "#ef4444",
      "#0ea5e9"
    ],

    
    borderRadius: 6,
    tension: 0.4, 
    fills: false, 

    animation: {
      duration: 1500,
      easing: "easeInOutCubic"
    }
  }
]
      });

    } catch (err) {
      console.error(err);
      setChartData(null);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  
  const resetZoom = () => {
    if (chartRef.current) {
      chartRef.current.resetZoom();
    }
  };

 
  const downloadCSV = () => {
    if (!chartData) return;

    let csv = "Label,Value\n";

    chartData.labels.forEach((label, i) => {
      csv += `${label},${chartData.datasets[0].data[i]}\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    saveAs(blob, `${metric.key}.csv`);
  };

  const options = {
  responsive: true,
  maintainAspectRatio: false,

  animation: {
    duration: 1200, 
    easing: "easeInOutQuart" 
  },

  transitions: {
    active: {
      animation: {
        duration: 800
      }
    }
  },

  plugins: {
    legend: { position: "top" },

    zoom: {
      pan: {
        enabled: true,
        mode: "x"
      },
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: "x"
      }
    }
  }
};

  const renderChart = () => {
    if (!chartData) return <p>No data</p>;

    if (chartType === "bar") {
      return <Bar key="bar" ref={chartRef} data={chartData} options={options} />;
    }

    if (chartType === "line") {
      return <Line key="line" ref={chartRef} data={chartData} options={options} />;
    }

    if (chartType === "pie") {
      return (
      <div className="pie-wrapper">
        <Pie key="pie" data={chartData} />
      </div>
    );
    }
  };

  return (
    <div className="graph-card">

      
      <div className="graph-controls">

        <select
          value={chartType}
          onChange={(e) => setChartType(e.target.value)}
        >
          <option value="bar">Bar</option>
          <option value="line">Line</option>
          <option value="pie">Pie</option>
        </select>

        <button onClick={resetZoom}>Reset</button>
        <button onClick={downloadCSV}>Download CSV</button>

      </div>

      
      <div className="graph-container">
        {renderChart()}
      </div>

    </div>
  );
}

export default GraphCard;