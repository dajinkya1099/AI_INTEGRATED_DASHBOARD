import { useEffect, useState } from "react";
import "../Styles/tableCard.css";   

function TableCard({ metric, refreshKey }) {
  const [data, setData] = useState([]);

  const fetchData = () => {
    fetch(`http://localhost:8282${metric.url}`)
      .then(res => res.json())
      .then(res => {
        if (Array.isArray(res)) {
          setData(res);
        } else {
          setData([]);
        }
      });
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]); // ✅ refresh support

  return (
    <div className="table-container">

      <div className="table-scroll">
        <table className="custom-table">
          <thead>
            <tr>
              {data[0] &&
                Object.keys(data[0]).map((key) => (
                  <th key={key}>{key}</th>
                ))}
            </tr>
          </thead>

          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {Object.values(row).map((val, j) => (
                  <td key={j}>
                    {typeof val === "object"
                      ? JSON.stringify(val)
                      : val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
}

export default TableCard;