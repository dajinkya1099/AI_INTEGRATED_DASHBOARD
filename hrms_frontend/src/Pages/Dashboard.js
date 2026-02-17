import { useEffect, useState } from "react";

function Dashboard() {
  const [data, setData] = useState({});

  useEffect(() => {
    fetch("http://localhost:5000/api/data")
      .then((res) => res.json())
      .then((data) => setData(data));
  }, []);

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Users: {data.users}</p>
      <p>Revenue: {data.revenue}</p>
      <p>Orders: {data.orders}</p>
    </div>
  );
}

export default Dashboard;
