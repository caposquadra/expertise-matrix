import { Component, type ErrorInfo, type ReactNode } from "react";
import { Container, Title, Text, Button, Paper } from "@mantine/core";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Container size="sm" py="xl">
          <Paper p="xl" withBorder radius="lg" ta="center">
            <Title order={3} mb="md">Что-то пошло не так</Title>
            <Text c="dimmed" mb="lg">
              {this.state.error?.message || "Произошла непредвиденная ошибка"}
            </Text>
            <Button onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = "/"; }}>
              На главную
            </Button>
          </Paper>
        </Container>
      );
    }
    return this.props.children;
  }
}
