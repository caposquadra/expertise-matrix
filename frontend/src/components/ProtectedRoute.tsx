import { useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Loader, Center } from "@mantine/core";
import { useAuth } from "../store/auth";
import client from "../api/client";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const location = useLocation();
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    if (token && !user) {
      client.get("/auth/me").then(({ data }) => setUser(data)).catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      });
    }
  }, [token, user, setUser]);

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!user) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  return <>{children}</>;
}
