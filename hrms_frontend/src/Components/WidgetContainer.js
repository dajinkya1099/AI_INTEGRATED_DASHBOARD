import { Card, CardContent, Box, Typography, IconButton } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import CloseIcon from "@mui/icons-material/Close";

function WidgetContainer({ title, onRefresh, onRemove, children }) {
  return (
    <Card
      sx={{
        borderRadius: 3,
        boxShadow: 3,
        height: "100%",
        display: "flex",
        flexDirection: "column"
      }}
    >
      <CardContent>

        {/* HEADER */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 1
          }}
        >
          <Typography fontSize={14} fontWeight={600}>
            {title}
          </Typography>

          <Box>
            <IconButton size="small" color="primary" onClick={onRefresh}>
              <RefreshIcon />
            </IconButton>

            <IconButton size="small" color="error" onClick={onRemove}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>

        {/* CONTENT */}
        <Box sx={{ flex: 1 }}>
          {children}
        </Box>

      </CardContent>
    </Card>
  );
}

export default WidgetContainer;