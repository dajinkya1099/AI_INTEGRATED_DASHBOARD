import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

function GraphCard({ metric, refreshKey }) {
  const [chartData, setChartData] = useState(null);

  const fetchData = async () => {
  try {
    const res = await fetch(`http://localhost:8282${metric.url}`);
    const data = await res.json();

    console.log("Graph API Response:", data);

    let labels = [];
    let values = [];

    // ✅ CASE 1: backend sends array
    if (Array.isArray(data)) {
      labels = data.map((item) => item.label);
      values = data.map((item) => item.value);
    }

    // ✅ CASE 2: backend sends {labels, values}
    else if (data.labels && data.values) {
      labels = data.labels;
      values = data.values;
    }

    else {
      console.error("Invalid graph format:", data);
      setChartData(null);
      return;
    }

    setChartData({
      labels,
      datasets: [
        {
          label: metric.key,
          data: values,
          backgroundColor: "rgba(99,102,241,0.6)"
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

  return (
    <div className="card-body">

      {chartData ? (
        <div className="graph-container">
  {chartData ? <Bar data={chartData} /> : <p className="no-data">No data</p>}
</div>
      ) : (
        <p className="no-data">No graph data available</p>
      )}
    </div>
  );
}

export default GraphCard;