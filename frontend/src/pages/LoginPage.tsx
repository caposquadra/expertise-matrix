import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Paper, TextInput, PasswordInput, Button, Alert, Text, Center, Stack, Divider, Group } from "@mantine/core";
import { IconAlertCircle, IconLayoutGrid, IconUsers, IconChartBar, IconStar } from "@tabler/icons-react";
import client from "../api/client";
import { useAuth } from "../store/auth";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await client.post("/auth/login", { email, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      setUser(data.user);
      if (data.user.role === "employee") {
        navigate("/profile");
      } else {
        navigate("/");
      }
    } catch (err) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response: { data: { detail?: string } } }).response?.data?.detail
        : undefined;
      setError(msg || "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", background: "linear-gradient(135deg, #eef1f6 0%, #e2e8f0 100%)" }}>
      <div style={{ flex: 1, display: "flex", alignItems: "flex-start", justifyContent: "center", paddingTop: 8 }}>
        <Container size={420}>
          <Center mb={0}>
            <IconLayoutGrid size={40} color="var(--mantine-color-indigo-7)" />
            <Text ml="sm" fw={800} style={{ fontSize: 28, lineHeight: 1.1 }} c="var(--mantine-color-indigo-7)">Expertise Matrix</Text>
          </Center>
          <Text ta="center" c="dimmed" size="sm" mb={8}>
            Внутренний портал управления компетенциями команды тестирования
          </Text>
          <Paper shadow="lg" p="md" radius="lg" style={{ background: "rgba(255,255,255,0.95)" }}>
            <form onSubmit={handleSubmit}>
              <TextInput label="Email" placeholder="email@domain.com" value={email} onChange={(e) => setEmail(e.target.value)} required mb="sm" size="md" />
              <PasswordInput label="Пароль" placeholder="Ваш пароль" value={password} onChange={(e) => setPassword(e.target.value)} required mb="lg" size="md" />
              {error && <Alert icon={<IconAlertCircle size={16} />} color="red" mb="sm" variant="light">{error}</Alert>}
              <Button type="submit" fullWidth loading={loading} size="md" color="indigo">
                Войти
              </Button>
            </form>
          </Paper>
          <Text ta="center" c="dimmed" size="xs" mt="sm">
            Демо: admin@example.com / admin123
          </Text>
        </Container>
      </div>
      <div style={{ flex: 1, display: "none", alignItems: "center", justifyContent: "center", padding: 40, background: "linear-gradient(135deg, var(--mantine-color-indigo-6) 0%, var(--mantine-color-indigo-8) 100%)" }} className="mantine-visible-from-md">
        <Stack align="center" gap="lg" c="white">
          <IconLayoutGrid size={64} stroke={1.5} />
          <Text fw={700} size="28" ta="center">Matrice de Compétences</Text>
          <Text size="sm" ta="center" opacity={0.8} maw={320}>
            Оценивайте навыки, отслеживайте прогресс, планируйте развитие команды
          </Text>
          <Divider w={200} color="rgba(255,255,255,0.3)" />
          <Stack gap="md" mt="md">
            <Group gap="md">
              <div style={{ width: 48, height: 48, borderRadius: 12, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <IconUsers size={24} />
              </div>
              <div>
                <Text fw={600} size="sm">14 сотрудников</Text>
                <Text size="xs" opacity={0.7}>в двух командах</Text>
              </div>
            </Group>
            <Group gap="md">
              <div style={{ width: 48, height: 48, borderRadius: 12, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <IconChartBar size={24} />
              </div>
              <div>
                <Text fw={600} size="sm">29 навыков</Text>
                <Text size="xs" opacity={0.7}>в 8 категориях</Text>
              </div>
            </Group>
            <Group gap="md">
              <div style={{ width: 48, height: 48, borderRadius: 12, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <IconStar size={24} />
              </div>
              <div>
                <Text fw={600} size="sm">4 уровня</Text>
                <Text size="xs" opacity={0.7}>оценки компетенций</Text>
              </div>
            </Group>
          </Stack>
        </Stack>
      </div>
    </div>
  );
}
