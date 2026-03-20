// import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
// import Layout from "./Components/Layout";
// import Home from "./Pages/Home";
// import Dashboard from "./Pages/Dashboard";
// import Settings from "./Pages/Settings";
// import QueryBuilder from "./Pages/QueryBuilder";
// import CustomResponse from "./Pages/CustomResponse";
// import AIResponse from "./Pages/AIResponse";

// function App() {
//   return (
//     <Router>
//       <Layout>
//         <Routes>
//           <Route path="/" element={<Home />} />
//           <Route path="/dashboard" element={<Dashboard />} />
//           <Route path="/settings" element={<Settings />} />
//           <Route path="/dynamic-data-explorer" element={<QueryBuilder />} />
//           <Route path="/custom-response" element={<CustomResponse />} />
//           <Route path="/ai-response" element={<AIResponse />} />
//         </Routes>
//       </Layout>
//     </Router>
//   );
// }

// export default App;

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";   // ✅ FIX

import ProtectedRoute from "./Components/ProtectedRoute";
import Layout from "./Components/Layout";      // ✅ FIX

import Home from "./Pages/Home";
import Dashboard from "./Pages/Dashboard";
import Settings from "./Pages/Settings";
import QueryBuilder from "./Pages/QueryBuilder";
import CustomResponse from "./Pages/CustomResponse";
import AIResponse from "./Pages/AIResponse";

import Login from "./Components/Login";
import Signup from "./Components/Signup";
import ConfigDashboard from "./Pages/ConfigDashboard";

function App() {

  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("user"))
  );

  // ✅ Load user on refresh
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  // ✅ Sync across tabs
  useEffect(() => {
    const handleStorageChange = () => {
      const updatedUser = localStorage.getItem("user");
      setUser(updatedUser ? JSON.parse(updatedUser) : null);
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  return (
    <Router>
      <Routes>

        {/* PUBLIC */}
        <Route path="/login" element={<Login setUser={setUser} />} />
        <Route path="/signup" element={<Signup />} />

        {/* PROTECTED WITH LAYOUT */}
        <Route path="/" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <Home />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/dashboard" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/settings" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <Settings />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/dynamic-data-explorer" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <QueryBuilder />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/configure-dashboard" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
            <ConfigDashboard />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/custom-response" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <CustomResponse />
            </Layout>
          </ProtectedRoute>
        } />

        <Route path="/ai-response" element={
          <ProtectedRoute user={user}>
            <Layout user={user} setUser={setUser}>
              <AIResponse />
            </Layout>
          </ProtectedRoute>
        } />

      </Routes>
    </Router>
  );
}

export default App;
