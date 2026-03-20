import { Box } from "@mui/material";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

function Layout({ children, user, setUser }) {
  return (
    <Box sx={{ height: "100vh", width: "100vw", display: "flex", flexDirection: "column" }}>
      
      {/* Navbar */}
      <Navbar user={user} setUser={setUser} /> {/* ✅ FIX */}

      {/* Main Section */}
      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        
        {/* Sidebar */}
        <Sidebar />

        {/* Page Content */}
        <Box
          sx={{
            flex: 1,
            p: 2,
            overflow: "auto",
            backgroundColor: "#f4f6f8"
          }}
        >
          {children}
        </Box>

      </Box>
    </Box>
  );
}

export default Layout;