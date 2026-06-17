import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { Loader, Center } from "@mantine/core";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { MatrixPage } from "./pages/MatrixPage";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import { EmployeePage } from "./pages/EmployeePage";
import { EmployeeDetailPage } from "./pages/EmployeeDetailPage";
import { IprPage } from "./pages/IprPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { AdminPage } from "./pages/AdminPage";
import { useAuth } from "./store/auth";

export function App() {
  const { initialized, restoreSession } = useAuth();

  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  if (!initialized) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/matrix" element={<MatrixPage />} />
        <Route path="/skills/:id" element={<SkillDetailPage />} />
        <Route path="/employees/:id" element={<EmployeeDetailPage />} />
        <Route path="/profile" element={<EmployeePage />} />
        <Route path="/ipr" element={<IprPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
