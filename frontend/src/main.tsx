import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { MantineProvider, createTheme } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import { App } from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

const theme = createTheme({
  primaryColor: "indigo",
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  defaultRadius: "md",
  shadows: {
    md: "0 4px 12px rgba(0,0,0,0.06)",
    lg: "0 8px 24px rgba(0,0,0,0.08)",
  },
  components: {
    Card: {
      defaultProps: { shadow: "sm", withBorder: true, padding: "lg", radius: "lg" },
    },
    Table: {
      defaultProps: { highlightOnHover: true, withTableBorder: false, withColumnBorders: false },
    },
    Badge: {
      defaultProps: { variant: "light" },
    },
    Button: {
      defaultProps: { radius: "md" },
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <MantineProvider theme={theme} defaultColorScheme="light">
        <Notifications position="top-right" />
        <ErrorBoundary><App /></ErrorBoundary>
      </MantineProvider>
    </BrowserRouter>
  </StrictMode>,
);
