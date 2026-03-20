import { useEffect, useState } from "react";

function ProgressCard({ metric, refreshKey }) {

  const [value, setValue] = useState(0);

  const fetchData = () => {
    fetch(`http://localhost:8282${metric.url}`)
      .then(res => res.json())
      .then(res => setValue(res.value));
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  return (
    <div style={styles.card}>
      <h4>{metric.key}</h4>

      <div>
  <div className="progress-bar">
    <div
      className="progress-fill"
      style={{ width: `${value || 0}%` }}
    ></div>
  </div>
  <p>{value || 0}%</p>
</div>
    </div>
  );
}

const styles = {
  card: {
    background: "white",
    padding: "20px",
    borderRadius: "10px"
  }
};

export default ProgressCard;