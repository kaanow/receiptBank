import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import UploadReceipt from "./pages/UploadReceipt";
import Reports from "./pages/Reports";
import AccountDetail from "./pages/AccountDetail";
import AccountNew from "./pages/AccountNew";

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/upload" element={<PrivateRoute><UploadReceipt /></PrivateRoute>} />
      <Route path="/reports" element={<PrivateRoute><Reports /></PrivateRoute>} />
      <Route path="/accounts/new" element={<PrivateRoute><AccountNew /></PrivateRoute>} />
      <Route path="/accounts/:id" element={<PrivateRoute><AccountDetail /></PrivateRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="app">
          <AppRoutes />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
