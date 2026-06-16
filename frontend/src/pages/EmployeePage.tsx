import { useEffect, useState } from "react";
import { Title, Card, Text, Group, Badge, Table, Loader, Center, Tabs, Avatar, Button, Box } from "@mantine/core";
import { IconStar, IconHistory } from "@tabler/icons-react";
import client from "../api/client";
import { useAuth } from "../store/auth";
import { translateRole, translateGrade } from "../constants";

import { EmployeeProfileBlock } from "../components/EmployeeProfileBlock";
import type { Skill, Assessment, HistoryEntry } from "../types";

const fieldLabels: Record<string, string> = {
  self_level: "Самооценка", manager_level: "Оценка руководителя", target_level: "Целевой уровень",
};

const gradeTargetMap: Record<string, number> = {
  junior: 1, middle: 2, senior: 3,
};

const currentBadgeColor = (v: number | null, targetLevel: number | null) => {
  if (v == null) return "gray";
  if (targetLevel != null) {
    if (v >= targetLevel) return "green";
    if (v >= targetLevel - 1) return "yellow";
    return "red";
  }
  if (v < 2) return "red";
  if (v < 3) return "yellow";
  return "green";
};

export function EmployeePage() {
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "manager";
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<Record<string, HistoryEntry[]>>({});
  const [historyLoading, setHistoryLoading] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      client.get("/skills").then((r) => setSkills(r.data)),
      client.get(`/assessments?employee_id=${user.id}`).then((r) => setAssessments(r.data)),
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

  const gradeOrder = ["junior", "middle", "senior"];
  const currentGrade = user?.grade ?? "";
  const currentGradeIdx = gradeOrder.indexOf(currentGrade);
  const nextGrade = currentGradeIdx >= 0 && currentGradeIdx < gradeOrder.length - 1 ? gradeOrder[currentGradeIdx + 1] : null;
  const nextGradeTarget = nextGrade ? gradeTargetMap[nextGrade] : 3;

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

      {isManager && user && <EmployeeProfileBlock employeeId={user.id} />}



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
                    <Table.Th>Навык</Table.Th>
                    <Table.Th w={160} />
                    <Table.Th w={70} ta="center">Текущий</Table.Th>
                    <Table.Th w={60} ta="center">Цель</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {skills.filter((s) => s.category === cat).map((s) => {
                    const a = getAssess(s.id);
                    const cl = currentLevel(a);
                    const col = currentBadgeColor(cl, a?.target_level ?? null);
                    return (
                      <Table.Tr key={s.id}>
                        <Table.Td fw={500}>
                          <Group gap={4} wrap="nowrap">
                            {s.weight >= 3 && <IconStar size={12} style={{ color: "var(--mantine-color-yellow-6)", flexShrink: 0 }} />}
                            {s.name}
                          </Group>
                        </Table.Td>
                        <Table.Td>
                          <Group gap={2} w={120} style={{ height: 14 }}>
                            {Array.from({ length: 3 }, (_, i) => {
                              let bg: string;
                              if (i < (cl ?? 0)) {
                                bg = `var(--mantine-color-${col}-6)`;
                              } else if (i < (a?.target_level ?? nextGradeTarget)) {
                                bg = "var(--mantine-color-gray-4)";
                              } else {
                                bg = "var(--mantine-color-gray-2)";
                              }
                              return <Box key={i} style={{ flex: 1, height: 14, borderRadius: 2, backgroundColor: bg }} />;
                            })}
                          </Group>
                        </Table.Td>
                        <Table.Td ta="center">{cl ?? "—"}</Table.Td>
                        <Table.Td ta="center">{a?.target_level ?? nextGradeTarget}</Table.Td>
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
