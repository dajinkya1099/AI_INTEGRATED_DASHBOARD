import React from "react";
import { Link } from "react-router-dom";

// const user = JSON.parse(localStorage.getItem("user"));
// const menuItems = [
//   { name: "Home", path: "/" },
//   { name: "Dashboard", path: "/dashboard" },
//   { name: "Settings", path: "/settings" },
//  { name: "Dynamic Data Explorer", path: "/dynamic-data-explorer" },
//   { name: "Configure Dashboard", path: "/configure-dashboard"},
//   ...(user?.role === "ADMIN"
//     ? [{ name: "Admin Config", path: "/admin-dashboard-config" }]
//     : [])
// ];

// function Sidebar() {
//   return (
//     <div style={styles.sidebar}>
//       {menuItems.map((item, index) => (
//         <Link key={index} to={item.path} style={styles.link}>
//           {item.name}
//         </Link>
//       ))}
//     </div>
//   );
// }

function Sidebar({ user }) {

  const menuItems = [
    { name: "Home", path: "/" },
    { name: "Dashboard", path: "/dashboard" },
    { name: "Dynamic Data Explorer", path: "/dynamic-data-explorer" },
    { name: "Settings", path: "/settings" },

    // ✅ visible to all
    { name: "Configure Dashboard", path: "/configure-dashboard" },

    // ✅ admin only
    ...(user?.role === "ADMIN"
      ? [{ name: "Admin Config", path: "/admin-dashboard-config" }]
      : [])
  ];

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
