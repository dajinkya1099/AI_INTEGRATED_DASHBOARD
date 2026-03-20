import { Navigate } from "react-router-dom";

function ProtectedRoute({ user, children }) {
  if (!user) return <Navigate to="/login" />;

  return children;   // ✅ ONLY return children
}

export default ProtectedRoute;