import { useState, Fragment } from "react";
import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Text, Group, Badge, Table, Loader, Center, Button, Avatar, Progress } from "@mantine/core";
import { IconArrowLeft, IconStar } from "@tabler/icons-react";
import client from "../api/client";
import { translateRole, translateGrade } from "../constants";

import { EmployeeProfileBlock } from "../components/EmployeeProfileBlock";
import type { Skill, Assessment, Employee, Score } from "../types";

const gradeLevel: Record<string, number> = { junior: 2, middle: 3, senior: 4 };

const currentBadgeColor = (v: number | null, grade: string | null) => {
  if (v == null) return "gray";
  const expected = grade ? gradeLevel[grade] : null;
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

const catBgColors = ["#f0f4f8", "#f0f0f8", "#f4f8f0", "#f8f4f0", "#f0f8f8", "#f8f0f4", "#f4f4f0", "#f0f4f4"];

export function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [score, setScore] = useState<Score | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      client.get(`/employees/${id}`).then((r) => setEmployee(r.data)),
      client.get("/skills").then((r) => setSkills(r.data)),
      client.get(`/assessments?employee_id=${id}`).then((r) => setAssessments(r.data)),
      client.get(`/employees/${id}/score`).then((r) => setScore(r.data)),
    ]).catch((err) => {
      console.error("Failed to load employee detail", err);
    }).finally(() => setLoading(false));
  }, [id]);

  const getAssess = (skillId: string) => assessments.find((a) => a.skill_id === skillId);

  if (loading) return <Center h={300}><Loader /></Center>;
  if (!employee) return <Center h={300}><Text c="dimmed">Сотрудник не найден</Text></Center>;

  const categories = [...new Set(skills.map((s) => s.category))];

  return (
    <>
      <Button variant="subtle" leftSection={<IconArrowLeft size={16} />} onClick={() => navigate("/matrix")} mb="md" c="gray">
        Назад к матрице
      </Button>

      <Card padding="lg" radius="lg" mb="xl" style={{ background: "var(--mantine-color-indigo-0)" }}>
        <Group>
          <Avatar size={56} radius="xl" color="indigo" variant="filled">{employee.full_name.charAt(0)}</Avatar>
          <div>
            <Text fw={700} size="xl">{employee.full_name}</Text>
            <Group gap={8} mt={4}>
              <Badge color="indigo" variant="light">{translateRole(employee.role)}</Badge>
              {employee.grade && <Badge color="blue" variant="light">{translateGrade(employee.grade)}</Badge>}
              <Text size="sm" c="dimmed">{employee.email}</Text>
            </Group>
          </div>
        </Group>
      </Card>

      {id && <EmployeeProfileBlock employeeId={id} />}

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

      <Card padding="0" radius="lg" mb="md" style={{ overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <Table striped={false}>
            <Table.Thead>
              <Table.Tr style={{ background: "var(--mantine-color-gray-0)" }}>
                <Table.Th w={220}>Раздел / Навык</Table.Th>
                <Table.Th w={60} ta="center">Вес</Table.Th>
                <Table.Th w={220} ta="center">Текущий → Цель</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {categories.map((cat, ci) => (
                <Fragment key={cat}>
                  <Table.Tr>
                    <Table.Td colSpan={3} style={{ background: catBgColors[ci % catBgColors.length], fontWeight: 700, fontSize: 13, color: "var(--mantine-color-indigo-7)", padding: "10px 16px", borderBottom: "2px solid var(--mantine-color-indigo-2)" }}>
                      {cat}
                    </Table.Td>
                  </Table.Tr>
                  {skills.filter((s) => s.category === cat).map((s) => {
                    const a = getAssess(s.id);
                    const effective = a?.manager_level ?? a?.self_level ?? null;
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
                                value={((effective ?? 0) / 4) * 100}
                                color={currentBadgeColor(effective, employee.grade)}
                              />
                              {a?.target_level != null && (effective ?? 0) < a.target_level && (
                                <Progress.Section
                                  value={((a.target_level - (effective ?? 0)) / 4) * 100}
                                  color="gray"
                                  striped
                                />
                              )}
                            </Progress.Root>
                            <Text size="sm" fw={600}>
                              {effective ?? "—"} → {a?.target_level ?? "—"}
                            </Text>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    );
                  })}
                </Fragment>
              ))}
            </Table.Tbody>
          </Table>
        </div>
      </Card>
    </>
  );
}
