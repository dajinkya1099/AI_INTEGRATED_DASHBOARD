import { useEffect, useState } from "react";
import RefreshIcon from "@mui/icons-material/Refresh";

function WidgetCard({ metric, refreshKey }) {
  const [value, setValue] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);

      const res = await fetch(`http://localhost:8282${metric.url}`);
      const data = await res.json();

      // ✅ handle different backend formats
      if (typeof data === "number") {
        setValue(data);
      } else if (data.value !== undefined) {
        setValue(data.value);
      } else {
        setValue(0);
      }

    } catch (err) {
      console.error("Widget fetch error:", err);
      setValue(0);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Initial load + refresh trigger
  useEffect(() => {
    fetchData();
  }, [refreshKey]); // 🔥 THIS FIXES YOUR REFRESH BUTTON

  return (
    <div style={styles.card}>

      <div style={styles.header}>
        <h4 style={styles.title}>{metric.key}</h4>
      </div>

      <div style={styles.content}>
        {loading ? (
          <p style={styles.loading}>Loading...</p>
        ) : (
          <>
            {metric.type === "count" && (
              <h1 style={styles.value}>{value}</h1>
            )}

            {metric.type === "percentage" && (
              <h2 style={styles.value}>{value}%</h2>
            )}

            {metric.type === "speedometer" && (
              <h2 style={styles.value}>{value}% 🚀</h2>
            )}
          </>
        )}
      </div>

    </div>
  );
}

const styles = {
  card: {
    background: "#ffffff",
    padding: "16px",
    borderRadius: "14px",
    boxShadow: "0 6px 18px rgba(0,0,0,0.08)",
    transition: "0.3s",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between"
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  },
  title: {
    margin: 0,
    fontSize: "14px",
    color: "#64748b"
  },
  icon: {
    fontSize: "18px",
    cursor: "pointer",
    color: "#6366f1"
  },
  content: {
    marginTop: "10px"
  },
  value: {
    margin: 0,
    fontSize: "28px",
    fontWeight: "bold",
    color: "#0f172a"
  },
  loading: {
    fontSize: "14px",
    color: "#94a3b8"
  }
};

export default WidgetCard;