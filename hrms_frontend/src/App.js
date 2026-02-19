import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./Components/Layout";
import Home from "./Pages/Home";
import Dashboard from "./Pages/Dashboard";
import Settings from "./Pages/Settings";
import QueryBuilder from "./Pages/QueryBuilder";
import CustomResponse from "./Pages/CustomResponse";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/dynamic-data-explorer" element={<QueryBuilder />} />
          <Route path="/custom-response" element={<CustomResponse />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
