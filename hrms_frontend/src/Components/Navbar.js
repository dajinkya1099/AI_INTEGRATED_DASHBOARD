import React from "react";
import NotificationsIcon from "@mui/icons-material/Notifications";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import LogoutIcon from "@mui/icons-material/Logout";

function Navbar() {
  return (
    <div style={styles.navbar}>
      <h2 style={styles.title}>
        HRMS (Human Resource Management System)
      </h2>

      <div style={styles.iconContainer}>
        <NotificationsIcon style={styles.icon} />
        <AccountCircleIcon style={styles.icon} />
        <LogoutIcon style={styles.icon} />
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
    gap: "20px",
    cursor: "pointer"
  },
  icon: {
    fontSize: "26px",
    transition: "0.3s",
  }
};

export default Navbar;