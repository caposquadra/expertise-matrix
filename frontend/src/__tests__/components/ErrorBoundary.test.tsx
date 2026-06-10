import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorBoundary } from "../../components/ErrorBoundary";
import { MantineProvider } from "@mantine/core";

const ThrowError = () => {
  throw new Error("Test error message");
};

const renderWithProvider = (ui: React.ReactElement) =>
  render(<MantineProvider>{ui}</MantineProvider>);

describe("ErrorBoundary", () => {
  it("renders children when no error", () => {
    renderWithProvider(
      <ErrorBoundary>
        <div>Hello World</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Hello World")).toBeDefined();
  });

  it("catches error and shows fallback UI", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    renderWithProvider(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Что-то пошло не так")).toBeDefined();
    expect(screen.getByText("Test error message")).toBeDefined();
    expect(screen.getByText("На главную")).toBeDefined();

    vi.restoreAllMocks();
  });
});
