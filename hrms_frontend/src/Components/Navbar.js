import React from "react";
import { useNavigate } from "react-router-dom";

import NotificationsIcon from "@mui/icons-material/Notifications";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/Logout";

function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    setUser(null);   // ✅ works now

    navigate("/login");
  };

  return (
    <div style={styles.navbar}>
      <h2 style={styles.title}>AI Integrated Dashboard</h2>

      <div style={styles.iconContainer}>
        <NotificationsIcon style={styles.icon} />

        <div style={styles.userBox}>
          <AccountCircleIcon style={styles.icon} />
          <span style={styles.username}>
            {user?.username || "Guest"}
          </span>
        </div>

        <div onClick={handleLogout}>
          <LogoutIcon style={{ ...styles.icon, color: "#f87171" }} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  navbar: {
    height: "60px",
    background: "#1e293b",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.3)"
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "500"
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    gap: "20px"
  },
  icon: {
    fontSize: "26px",
    cursor: "pointer",
    transition: "0.3s"
  },
  userBox: {
    display: "flex",
    alignItems: "center",
    gap: "6px"
  },
  username: {
    fontSize: "14px"
  }
};

export default Navbar;