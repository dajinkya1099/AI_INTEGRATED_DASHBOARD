import { useEffect, useState } from "react";

function Dashboard() {
  const [schemas, setSchemas] = useState([]);

  useEffect(() => {
   fetch("http://localhost:8282/schemas")
      .then((res) => res.json())
      .then((data) => {
        setSchemas(data.schemas);
      })
      .catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h3>Schemas</h3>
      <ul>
        {schemas.map((schema) => (
          <li key={schema}>{schema}</li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;
