import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { Loader, Center } from "@mantine/core";
import { useAuth } from "../store/auth";
import client, { getAccessToken } from "../api/client";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, setUser } = useAuth();
  const location = useLocation();
  const [checking, setChecking] = useState(!getAccessToken() && !user);

  useEffect(() => {
    if (getAccessToken() && !user) {
      client.get("/auth/me").then(({ data }) => setUser(data)).catch(() => {
        // refresh will be attempted by interceptor; if that fails, redirect
      });
      return;
    }
    if (!getAccessToken() && !user) {
      // try to restore session via refresh cookie
      client.get("/auth/me").then(({ data }) => setUser(data)).catch(() => {
        // no cookie or refresh failed — redirect to login
      }).finally(() => setChecking(false));
    }
  }, [user, setUser]);

  if (!getAccessToken() && !user && !checking) {
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
