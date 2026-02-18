import React from "react";
import { Link } from "react-router-dom";

const menuItems = [
  { name: "Home", path: "/" },
  { name: "Dashboard", path: "/dashboard" },
  { name: "Settings", path: "/settings" },
 { name: "Dynamic Data Explorer", path: "/dynamic-data-explorer" }
];

function Sidebar() {
  return (
    <div style={styles.sidebar}>
      {menuItems.map((item, index) => (
        <Link key={index} to={item.path} style={styles.link}>
          {item.name}
        </Link>
      ))}
    </div>
  );
}

const styles = {
  sidebar: {
    width: "200px",
    height: "100vh",
    background: "#334155",
    color: "white",
    display: "flex",
    flexDirection: "column",
    padding: "20px"
  },
  link: {
    color: "white",
    textDecoration: "none",
    marginBottom: "15px"
  }
};

export default Sidebar;
