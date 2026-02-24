import {
  People,
  Work,
  Assessment,
  Payments,
  Business,
  TrendingUp,
  Psychology
} from "@mui/icons-material";
import { Box, Typography } from "@mui/material";

function BottomBar() {
  const items = [
    { icon: <People />, label: "Employees" },
    { icon: <Work />, label: "Departments" },
    { icon: <Assessment />, label: "Analytics" },
    { icon: <Payments />, label: "Payroll" },
    { icon: <Business />, label: "Operations" },
    { icon: <TrendingUp />, label: "Growth" },
    { icon: <Psychology />, label: "AI Insights" }
  ];

  return (
    <Box
      sx={{
        position: "fixed",
        bottom: 0,
        left: 0,
        width: "100%",
        height: 40,
        overflow: "hidden",
        zIndex: 1500,
        backdropFilter: "blur(12px)",
        background:
          "linear-gradient(90deg, rgba(47, 118, 188, 0.15), rgba(66,165,245,0.15))",
        borderTop: "1px solid rgba(255,255,255,0.2)",
        display: "flex",
        alignItems: "center"
      }}
    >
      <Box
        sx={{
          display: "flex",
          gap: 8,
          px: 2,
          animation: "marquee 25s linear infinite"
        }}
      >
        {[...items, ...items].map((item, index) => (
          <Box
            key={index}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              px: 3,
              py: 1,
              borderRadius: 3,
              background: "rgba(255,255,255,0.15)",
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
              transition: "all 0.3s ease",
              cursor: "pointer",
              "&:hover": {
                transform: "scale(1.08)",
                background: "rgba(25,118,210,0.3)"
              }
            }}
          >
            {item.icon}
            <Typography variant="body2" fontWeight={400}>
              {item.label}
            </Typography>
          </Box>
        ))}
      </Box>

      <style>
        {`
          @keyframes marquee {
            from { transform: translateX(0%); }
            to { transform: translateX(-50%); }
          }
        `}
      </style>
    </Box>
  );
}

export default BottomBar;