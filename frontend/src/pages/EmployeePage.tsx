import { useEffect, useState } from "react";
import { Title, Card, Text, Group, Badge, Table, Loader, Center, Tabs, Avatar, Button, Progress } from "@mantine/core";
import { IconStar, IconHistory } from "@tabler/icons-react";
import client from "../api/client";
import { useAuth } from "../store/auth";
import { translateRole, translateGrade } from "../constants";

import { EmployeeProfileBlock } from "../components/EmployeeProfileBlock";
import type { Skill, Assessment, HistoryEntry, Score } from "../types";

const fieldLabels: Record<string, string> = {
  self_level: "Самооценка", manager_level: "Оценка руководителя", target_level: "Целевой уровень",
};

const gradeTargetMap: Record<string, number> = {
  junior: 2, middle: 3, senior: 4,
};

const currentBadgeColor = (v: number | null, grade: string | null) => {
  if (v == null) return "gray";
  const expected = grade ? gradeTargetMap[grade] : null;
  if (expected == null) {
    if (v <= 1) return "red";
    if (v <= 2) return "orange";
    if (v <= 3) return "yellow";
    return "green";
  }
  if (v >= expected) return "green";
  if (v === expected - 1) return "yellow";
  return "red";
};

export function EmployeePage() {
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "manager";
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [score, setScore] = useState<Score | null>(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<Record<string, HistoryEntry[]>>({});
  const [historyLoading, setHistoryLoading] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      client.get("/skills").then((r) => setSkills(r.data)),
      client.get(`/assessments?employee_id=${user.id}`).then((r) => setAssessments(r.data)),
      client.get(`/employees/${user.id}/score`).then((r) => setScore(r.data)),
    ]).catch((err) => {
      console.error("Failed to load profile", err);
    }).finally(() => setLoading(false));
  }, [user]);

  const getAssess = (skillId: string) => assessments.find((a) => a.skill_id === skillId);
  const currentLevel = (a: Assessment | undefined) => a?.manager_level ?? a?.self_level ?? null;

  const loadHistory = async (assessmentId: string) => {
    if (history[assessmentId]) return;
    setHistoryLoading(assessmentId);
    try {
      const { data } = await client.get(`/assessments/${assessmentId}/history`);
      setHistory((prev) => ({ ...prev, [assessmentId]: data }));
    } finally { setHistoryLoading(null); }
  };

  if (loading) return <Center h={300}><Loader /></Center>;

  const categories = [...new Set(skills.map((s) => s.category))];

  return (
    <>
      <Title order={2} mb="lg" fw={700}>Профиль</Title>

      <Card padding="xl" radius="lg" mb="xl" style={{ background: "var(--mantine-color-indigo-0)" }}>
        <Group>
          <Avatar size={64} radius="xl" color="indigo" variant="filled">{user?.full_name?.charAt(0)}</Avatar>
          <div>
            <Text fw={800} size="xl">{user?.full_name}</Text>
            <Group gap={8} mt={4}>
              <Badge color="indigo" variant="light">{translateRole(user?.role)}</Badge>
              {user?.grade && <Badge color="blue" variant="light">{translateGrade(user.grade)}</Badge>}
              <Text size="sm" c="dimmed">{user?.email}</Text>
            </Group>
          </div>
        </Group>
      </Card>

      {score && (
        <Group mb="md" gap="md">
          <Card padding="md" radius="lg" withBorder style={{ flex: 1 }}>
            <Text size="xs" c="dimmed" mb={4}>Общий балл (текущий)</Text>
            <Group gap={6}>
              <Text fw={700} size="xl" c={score.current_score >= (score.target_score ?? 0) ? "green" : "orange"}>
                {score.current_score}
              </Text>
              <Text size="sm" c="dimmed" fw={500}>баллов</Text>
            </Group>
          </Card>
          <Card padding="md" radius="lg" withBorder style={{ flex: 1 }}>
            <Text size="xs" c="dimmed" mb={4}>Цель по грейду</Text>
            <Text fw={700} size="xl" c="indigo">
              {score.target_score != null ? `${score.target_score} баллов` : "—"}
            </Text>
          </Card>
          <Card padding="md" radius="lg" withBorder style={{ flex: 1 }}>
            <Text size="xs" c="dimmed" mb={4}>Отставание</Text>
            <Text fw={700} size="xl" c={score.target_score != null && score.current_score < score.target_score ? "red" : "green"}>
              {score.target_score != null
                ? `${score.target_score - score.current_score} баллов`
                : "—"}
            </Text>
          </Card>
        </Group>
      )}

      {isManager && user && <EmployeeProfileBlock employeeId={user.id} />}

      <Card padding="sm" radius="md" mb="md" withBorder>
        <Group gap="lg">
          <Group gap={6}>
            <Badge color="green" variant="filled" size="sm">●</Badge>
            <Text size="xs" c="dimmed">уровень соответствует грейду</Text>
          </Group>
          <Group gap={6}>
            <Badge color="yellow" variant="filled" size="sm">●</Badge>
            <Text size="xs" c="dimmed">на 1 шаг ниже грейда</Text>
          </Group>
          <Group gap={6}>
            <Badge color="red" variant="filled" size="sm">●</Badge>
            <Text size="xs" c="dimmed">на 2+ шага ниже грейда</Text>
          </Group>
        </Group>
      </Card>

      <Tabs defaultValue="skills" variant="pills" radius="md">
        <Tabs.List mb="md">
          <Tabs.Tab value="skills" leftSection={<IconStar size={16} />}>Навыки и оценки</Tabs.Tab>
          {isManager && <Tabs.Tab value="history" leftSection={<IconHistory size={16} />}>История изменений</Tabs.Tab>}
        </Tabs.List>

        <Tabs.Panel value="skills">
          {categories.map((cat) => (
            <Card key={cat} padding="lg" radius="lg" mb="md">
              <Title order={5} mb="sm" c="indigo">{cat}</Title>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                  <Table.Th w={220}>Навык</Table.Th>
                    <Table.Th w={60} ta="center">Вес</Table.Th>
                    <Table.Th w={220} ta="center">Текущий → Цель</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {skills.filter((s) => s.category === cat).map((s) => {
                    const a = getAssess(s.id);
                    const cl = currentLevel(a);
                    return (
                      <Table.Tr key={s.id}>
                        <Table.Td fw={500}>
                          <Group gap={4} wrap="nowrap">
                            {s.weight >= 3 && <IconStar size={12} style={{ color: "var(--mantine-color-yellow-6)", flexShrink: 0 }} />}
                            {s.name}
                          </Group>
                        </Table.Td>
                        <Table.Td ta="center">
                          <Badge color="gray" variant="light" size="sm">{s.weight}</Badge>
                        </Table.Td>
                        <Table.Td ta="center">
                          <Group gap={8} justify="center" wrap="nowrap">
                            <Progress.Root w={130} size={20}>
                              <Progress.Section
                                value={((cl ?? 0) / 4) * 100}
                                color={currentBadgeColor(cl, user?.grade ?? null)}
                              />
                              {a?.target_level != null && (cl ?? 0) < a.target_level && (
                                <Progress.Section
                                  value={((a.target_level - (cl ?? 0)) / 4) * 100}
                                  color="gray"
                                  striped
                                />
                              )}
                            </Progress.Root>
                            <Text size="sm" fw={600}>
                              {cl ?? "—"} → {a?.target_level ?? "—"}
                            </Text>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    );
                  })}
                </Table.Tbody>
              </Table>
            </Card>
          ))}
        </Tabs.Panel>

        {isManager && (
        <Tabs.Panel value="history">
          {assessments.length === 0 && <Text c="dimmed">Нет оценок</Text>}
          {assessments.map((a) => {
            const skill = skills.find((s) => s.id === a.skill_id);
            return (
              <Card key={a.id} padding="md" radius="lg" mb="sm">
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>{skill?.name || a.skill_id}</Text>
                  <Button size="xs" variant="light" color="indigo" onClick={() => loadHistory(a.id)} loading={historyLoading === a.id}>
                    Загрузить историю
                  </Button>
                </Group>
                {history[a.id] && (
                  <Table>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th>Поле</Table.Th>
                        <Table.Th>Было</Table.Th>
                        <Table.Th>Стало</Table.Th>
                        <Table.Th>Когда</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {history[a.id].map((h) => (
                        <Table.Tr key={h.id}>
                          <Table.Td><Badge size="sm" color="gray">{fieldLabels[h.field_name] || h.field_name}</Badge></Table.Td>
                          <Table.Td>{h.old_value ?? "—"}</Table.Td>
                          <Table.Td><Badge color="indigo" variant="light">{h.new_value ?? "—"}</Badge></Table.Td>
                          <Table.Td><Text size="xs" c="dimmed">{new Date(h.changed_at).toLocaleString()}</Text></Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                )}
              </Card>
            );
          })}
        </Tabs.Panel>
        )}
      </Tabs>
    </>
  );
}
