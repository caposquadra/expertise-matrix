import { useState, Fragment } from "react";
import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Text, Group, Badge, Table, Loader, Center, Button, Avatar, Box } from "@mantine/core";
import { IconArrowLeft, IconStar } from "@tabler/icons-react";
import client from "../api/client";
import { useAuth } from "../store/auth";
import { translateRole, translateGrade } from "../constants";

import { EmployeeProfileBlock } from "../components/EmployeeProfileBlock";
import { SkillLevelEditor } from "../components/SkillLevelEditor";
import type { Skill, Assessment, Employee } from "../types";

const gradeLevel: Record<string, number> = { junior: 1, middle: 2, senior: 3 };

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

const catBgColors = ["#f0f4f8", "#f0f0f8", "#f4f8f0", "#f8f4f0", "#f0f8f8", "#f8f0f4", "#f4f4f0", "#f0f4f4"];

export function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "manager";
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      client.get(`/employees/${id}`).then((r) => setEmployee(r.data)),
      client.get("/skills").then((r) => setSkills(r.data)),
      client.get(`/assessments?employee_id=${id}`).then((r) => setAssessments(r.data)),
    ]).catch((err) => {
      console.error("Failed to load employee detail", err);
    }).finally(() => setLoading(false));
  }, [id]);

  const getAssess = (skillId: string) => assessments.find((a) => a.skill_id === skillId);

  const handleAssessmentSave = (updated: Assessment) => {
    setAssessments((prev) => {
      const idx = prev.findIndex((a) => a.skill_id === updated.skill_id);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = updated;
        return next;
      }
      return [...prev, updated];
    });
  };

  if (loading) return <Center h={300}><Loader /></Center>;
  if (!employee) return <Center h={300}><Text c="dimmed">Сотрудник не найден</Text></Center>;

  const categories = [...new Set(skills.map((s) => s.category))];

  const gradeOrder = ["junior", "middle", "senior"];
  const currentGrade = employee?.grade ?? "";
  const currentGradeIdx = gradeOrder.indexOf(currentGrade);
  const nextGrade = currentGradeIdx >= 0 && currentGradeIdx < gradeOrder.length - 1 ? gradeOrder[currentGradeIdx + 1] : null;
  const nextGradeTarget = nextGrade ? gradeLevel[nextGrade] : 3;

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

      {isManager && id && <EmployeeProfileBlock employeeId={id} />}

      <Card padding="0" radius="lg" mb="md" style={{ overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <Table striped={false}>
            <Table.Thead>
              <Table.Tr style={{ background: "var(--mantine-color-gray-0)" }}>
                <Table.Th>Раздел / Навык</Table.Th>
                <Table.Th w={160} />
                <Table.Th w={70} ta="center">Текущий</Table.Th>
                <Table.Th w={60} ta="center">Цель</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {categories.map((cat, ci) => (
                <Fragment key={cat}>
                  <Table.Tr>
                    <Table.Td colSpan={4} style={{ background: catBgColors[ci % catBgColors.length], fontWeight: 700, fontSize: 13, color: "var(--mantine-color-indigo-7)", padding: "10px 16px", borderBottom: "2px solid var(--mantine-color-indigo-2)" }}>
                      {cat}
                    </Table.Td>
                  </Table.Tr>
                  {skills.filter((s) => s.category === cat).map((s) => {
                    const a = getAssess(s.id);
                    const effective = a?.manager_level ?? a?.self_level ?? null;
                    const col = currentBadgeColor(effective, a?.target_level ?? null);
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
                              if (i < (effective ?? 0)) {
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
                        <Table.Td ta="center">
                          <SkillLevelEditor skillId={s.id} employeeId={id} currentValue={effective} mode="manager" onSave={handleAssessmentSave} />
                        </Table.Td>
                        <Table.Td ta="center">{a?.target_level ?? nextGradeTarget}</Table.Td>
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
