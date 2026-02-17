import React from "react";

function Navbar() {
  return (
    <div style={styles.navbar}>
      <h2>My React App</h2>
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
    paddingLeft: "20px"
  }
};

export default Navbar;
