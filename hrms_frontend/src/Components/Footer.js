import React from "react";
import { Box, Typography } from "@mui/material";

function Footer() {
  return (
    <Box sx={styles.footer}>
      
      {/* Left */}
      <Typography variant="body2">
        © 2026 AI Integrated Dashboard
      </Typography>

      {/* Center */}
      <Typography variant="body2">
        Built with ❤️ using React & FastAPI
      </Typography>

      {/* Right */}
      <Typography variant="body2">
        Version 1.0
      </Typography>

    </Box>
  );
}

const styles = {
  footer: {
    height: "50px",
    background: "linear-gradient(90deg, #1e293b, #0f172a)",
    color: "#e2e8f0",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    borderTop: "1px solid #334155",
    fontSize: "13px"
  }
};

export default Footer;