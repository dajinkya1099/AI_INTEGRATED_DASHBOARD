// src/styles/formStyles.js

export const modernSelectStyle = {

 borderRadius: 3,
      backgroundColor: "#f9fafc",
      "& .MuiOutlinedInput-notchedOutline": {
        borderColor: "#d0d7e2"
      },
      "&:hover .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      },
      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
        borderColor: "#1976d2"
      }
};


export const menuItemStyle = {
  borderRadius: 2,
    mx: 1,
    my: 0.5,
    "&:hover": {
      backgroundColor: "#e3f2fd"
    },
    "&.Mui-selected": {
      backgroundColor: "#bbdefb !important",
      fontWeight: 600
    }
};

export const selectMenuProps = {
  PaperProps: {
    sx: {
      borderRadius: 3,
      mt: 1,
      boxShadow: "0 10px 30px rgba(0,0,0,0.15)"
    }
  }
};
