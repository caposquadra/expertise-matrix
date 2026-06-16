import { useEffect, useState, Fragment } from "react";
import {
  Box, Button, Card, Group, Text, Title, Badge, Select, Textarea,
  Stack, LoadingOverlay, Tabs, Modal, Alert, Table,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { IconCheck, IconX, IconPlayerPlay, IconSend, IconArrowRight, IconTrash, IconArrowBackUp, IconDeviceFloppy } from "@tabler/icons-react";
import { useAuth } from "../store/auth";
import client from "../api/client";
import { translateGrade } from "../constants";

interface ApiError {
  response?: { data?: { detail?: string } };
}

const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  manager_review: "На проверке у руководителя",
  interview: "Интервью с экспертом",
  decision: "Ожидает решения",
  completed: "Завершено (повышение)",
  rejected: "Завершено (отказ)",
};

const STATUS_COLORS: Record<string, string> = {
  draft: "gray",
  manager_review: "yellow",
  interview: "blue",
  decision: "orange",
  completed: "green",
  rejected: "red",
};

interface Skill {
  id: string;
  name: string;
  category: string;
}

interface EmployeeInfo {
  id: string;
  full_name: string;
  email: string;
}

interface ReviewAssessment {
  id: string;
  review_cycle_id: string;
  skill_id: string;
  self_level: number | null;
  self_comment: string | null;
  manager_level: number | null;
  expert_level: number | null;
}

interface ReviewCycle {
  id: string;
  employee_id: string;
  status: string;
  current_grade: string | null;
  target_grade: string | null;
  manager_comment: string | null;
  expert_comment: string | null;
  final_decision: string | null;
  final_comment: string | null;
  manager_id: string | null;
  expert_id: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
  assessments: ReviewAssessment[];
}

export function ReviewsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [employees, setEmployees] = useState<EmployeeInfo[]>([]);
  const [activeCycle, setActiveCycle] = useState<ReviewCycle | null>(null);
  const [newTarget, setNewTarget] = useState("middle");
  const [opened, { open, close }] = useDisclosure(false);
  const [editValues, setEditValues] = useState<Record<string, number | null>>({});

  const role = user?.role || "employee";
  const isManager = role === "admin" || role === "manager";
  const isExpert = role === "admin" || role === "expert";
  const canDecide = role === "admin" || role === "manager";

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [cyclesRes, skillsRes, employeesRes] = await Promise.all([
        client.get("/reviews"),
        client.get("/skills"),
        client.get("/employees"),
      ]);
      setCycles(cyclesRes.data);
      setSkills(skillsRes.data);
      setEmployees(employeesRes.data);
    } catch {
      notifications.show({ color: "red", title: "Ошибка", message: "Не удалось загрузить данные" });
    } finally {
      setLoading(false);
    }
  }

  async function createCycle() {
    try {
      const res = await client.post("/reviews", { target_grade: newTarget });
      setCycles((prev) => [res.data, ...prev]);
      notifications.show({ color: "green", title: "Создано", message: "Цикл оценки создан" });
      close();
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось создать" });
    }
  }

  async function updateAssessment(skillId: string, data: Record<string, unknown>) {
    if (!activeCycle) return;
    try {
      const res = await client.put(`/reviews/${activeCycle.id}/assessments/${skillId}`, data);
      setActiveCycle((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          assessments: prev.assessments.map((a) =>
            a.skill_id === skillId ? res.data : a
          ),
        };
      });
      setCycles((prev) =>
        prev.map((c) =>
          c.id === activeCycle.id ? { ...c, assessments: c.assessments.map((a) => a.skill_id === skillId ? res.data : a) } : c
        )
      );
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось обновить" });
    }
  }

  async function submitReview(cycleId: string) {
    try {
      const res = await client.post(`/reviews/${cycleId}/submit`, {});
      updateCycleState(res.data);
      notifications.show({ color: "green", title: "Отправлено", message: "Оценка отправлена руководителю" });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось отправить" });
    }
  }

  async function proceedToInterview(cycleId: string, comment: string) {
    try {
      const res = await client.post(`/reviews/${cycleId}/manager-review`, { manager_comment: comment || undefined });
      updateCycleState(res.data);
      notifications.show({ color: "green", title: "Готово", message: "Отправлено на интервью" });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось отправить" });
    }
  }

  async function proceedToDecision(cycleId: string, comment: string) {
    try {
      const res = await client.post(`/reviews/${cycleId}/expert-review`, { expert_comment: comment || undefined });
      updateCycleState(res.data);
      notifications.show({ color: "green", title: "Готово", message: "Отправлено на финальное решение" });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось отправить" });
    }
  }

  async function finalizeReview(cycleId: string, decision: string, comment: string) {
    try {
      const res = await client.post(`/reviews/${cycleId}/finalize`, { decision, comment: comment || undefined });
      updateCycleState(res.data);
      notifications.show({
        color: decision === "promoted" ? "green" : "red",
        title: "Готово",
        message: decision === "promoted" ? "Сотрудник повышен" : "Заявка отклонена",
      });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось завершить" });
    }
  }

  function updateCycleState(updated: ReviewCycle) {
    setCycles((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    setActiveCycle(updated);
  }

  async function deleteCycle(cycleId: string) {
    try {
      await client.delete(`/reviews/${cycleId}`);
      setCycles((prev) => prev.filter((c) => c.id !== cycleId));
      setActiveCycle((prev) => (prev?.id === cycleId ? null : prev));
      notifications.show({ color: "green", title: "Удалено", message: "Заявка удалена" });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось удалить" });
    }
  }

  async function returnToDraft(cycleId: string) {
    try {
      const res = await client.post(`/reviews/${cycleId}/return-to-draft`);
      updateCycleState(res.data);
      notifications.show({ color: "green", title: "Возвращено", message: "Заявка возвращена сотруднику на доработку" });
    } catch (err: unknown) {
      notifications.show({ color: "red", title: "Ошибка", message: (err as ApiError).response?.data?.detail || "Не удалось вернуть" });
    }
  }

  function openCycle(cycle: ReviewCycle) {
    setActiveCycle(cycle);
    const vals: Record<string, number | null> = {};
    cycle.assessments.forEach((a) => {
      vals[a.skill_id] = a.self_level || a.manager_level || a.expert_level || null;
    });
    setEditValues(vals);
  }

  const skillsById = Object.fromEntries(skills.map((s) => [s.id, s]));
  const employeesById = Object.fromEntries(employees.map((e) => [e.id, e]));

  const myCycles = cycles.filter((c) => role !== "employee" || c.employee_id === user?.id);
  const draftCycles = cycles.filter((c) => c.status === "draft");
  const pendingManager = cycles.filter((c) => c.status === "manager_review");
  const pendingInterview = cycles.filter((c) => c.status === "interview");
  const pendingDecision = cycles.filter((c) => c.status === "decision");

  const hasDraftCycle = cycles.some((c) => String(c.employee_id) === String(user?.id) && c.status === "draft");

  const sortedMyCycles = [...myCycles].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <Box pos="relative" maw={1200}>
      <LoadingOverlay visible={loading} />

      <Group justify="space-between" mb="lg">
        <Title order={2}>Оценка компетенций</Title>
        {role === "employee" && (
          <Button leftSection={<IconPlayerPlay size={16} />} onClick={open} disabled={hasDraftCycle}>
            Начать оценку
          </Button>
        )}
      </Group>

      <Tabs defaultValue="my">
        <Tabs.List mb="md">
          <Tabs.Tab value="my">Мои циклы</Tabs.Tab>
          {isManager && <Tabs.Tab value="drafts">Черновики ({draftCycles.length})</Tabs.Tab>}
          {isManager && <Tabs.Tab value="pending-manager">На проверке ({pendingManager.length})</Tabs.Tab>}
          {isExpert && <Tabs.Tab value="pending-interview">На интервью ({pendingInterview.length})</Tabs.Tab>}
          {canDecide && <Tabs.Tab value="pending-decision">На решение ({pendingDecision.length})</Tabs.Tab>}
        </Tabs.List>

        <Tabs.Panel value="my">
          {sortedMyCycles.length === 0 && <Text c="dimmed">Нет циклов оценки</Text>}
          <Stack gap="sm">
              {sortedMyCycles.map((cycle) => (
                <CycleCard
                  key={cycle.id}
                  cycle={cycle}
                  employeesById={employeesById}
                  onOpen={() => openCycle(cycle)}
                  onDelete={() => deleteCycle(cycle.id)}
                />
              ))}
          </Stack>
        </Tabs.Panel>

        {isManager && (
          <Tabs.Panel value="drafts">
            {draftCycles.length === 0 && <Text c="dimmed">Нет черновиков</Text>}
            <Stack gap="sm">
              {draftCycles.map((cycle) => (
                <CycleCard
                  key={cycle.id}
                  cycle={cycle}
                  employeesById={employeesById}
                  onOpen={() => openCycle(cycle)}
                />
              ))}
            </Stack>
          </Tabs.Panel>
        )}

        {isManager && (
          <Tabs.Panel value="pending-manager">
            {pendingManager.length === 0 && <Text c="dimmed">Нет ожидающих проверок</Text>}
            <Stack gap="sm">
              {pendingManager.map((cycle) => (
                <CycleCard
                  key={cycle.id}
                  cycle={cycle}
                  employeesById={employeesById}
                  onOpen={() => openCycle(cycle)}
                />
              ))}
            </Stack>
          </Tabs.Panel>
        )}

        {isExpert && (
          <Tabs.Panel value="pending-interview">
            {pendingInterview.length === 0 && <Text c="dimmed">Нет ожидающих интервью</Text>}
            <Stack gap="sm">
              {pendingInterview.map((cycle) => (
                <CycleCard
                  key={cycle.id}
                  cycle={cycle}
                  employeesById={employeesById}
                  onOpen={() => openCycle(cycle)}
                />
              ))}
            </Stack>
          </Tabs.Panel>
        )}

        {canDecide && (
          <Tabs.Panel value="pending-decision">
            {pendingDecision.length === 0 && <Text c="dimmed">Нет ожидающих решений</Text>}
            <Stack gap="sm">
              {pendingDecision.map((cycle) => (
                <CycleCard
                  key={cycle.id}
                  cycle={cycle}
                  employeesById={employeesById}
                  onOpen={() => openCycle(cycle)}
                />
              ))}
            </Stack>
          </Tabs.Panel>
        )}
      </Tabs>

      <Modal opened={opened} onClose={close} title="Новый цикл оценки" centered>
        <Stack>
          <Text size="sm">Выберите желаемый грейд:</Text>
          <Select
            data={[
              { value: "junior", label: translateGrade("junior") },
              { value: "middle", label: translateGrade("middle") },
              { value: "senior", label: translateGrade("senior") },
            ]}
            value={newTarget}
            onChange={(v) => setNewTarget(v || "middle")}
          />
          <Group justify="flex-end">
            <Button variant="default" onClick={close}>Отмена</Button>
            <Button onClick={createCycle}>Создать</Button>
          </Group>
        </Stack>
      </Modal>

      <DetailedReviewModal
        cycle={activeCycle}
        skillsById={skillsById}
        role={role}
        editValues={editValues}
        setEditValues={setEditValues}
        updateAssessment={updateAssessment}
        submitReview={submitReview}
        proceedToInterview={proceedToInterview}
        proceedToDecision={proceedToDecision}
        finalizeReview={finalizeReview}
        returnToDraft={returnToDraft}
        onClose={() => setActiveCycle(null)}
      />
    </Box>
  );
}

function CycleCard({
  cycle,
  employeesById,
  onOpen,
  onDelete,
}: {
  cycle: ReviewCycle;
  employeesById: Record<string, EmployeeInfo>;
  onOpen: () => void;
  onDelete?: () => void;
}) {
  const total = cycle.assessments.length;
  let filled: number;
  if (cycle.status === "draft") {
    filled = cycle.assessments.filter((a) => a.self_level != null).length;
  } else if (cycle.status === "manager_review") {
    filled = cycle.assessments.filter((a) => a.self_level != null).length;
  } else if (cycle.status === "interview") {
    filled = cycle.assessments.filter((a) => a.manager_level != null).length;
  } else if (cycle.status === "decision") {
    filled = cycle.assessments.filter((a) => a.expert_level != null).length;
  } else {
    filled = cycle.assessments.filter((a) =>
      a.self_level || a.manager_level || a.expert_level
    ).length;
  }

  const emp = employeesById[cycle.employee_id];

  return (
    <Card withBorder padding="md" radius="md" shadow="sm">
      <Group justify="space-between">
        <Box>
          <Group gap="xs" mb={4}>
            <Text fw={600}>{translateGrade(cycle.current_grade)} → {translateGrade(cycle.target_grade)}</Text>
            <Badge color={STATUS_COLORS[cycle.status]} variant="light">
              {STATUS_LABELS[cycle.status]}
            </Badge>
            {emp && (
              <Text size="xs" c="dimmed" ml="sm">
                {emp.full_name} ({emp.email})
              </Text>
            )}
          </Group>
          <Text size="sm" c="dimmed">
            Создан: {new Date(cycle.created_at).toLocaleDateString("ru-RU")}
            {cycle.submitted_at && ` | Отправлен: ${new Date(cycle.submitted_at).toLocaleDateString("ru-RU")}`}
          </Text>
          <Text size="sm" c="dimmed">
            Навыки: {filled}/{total} оценено
          </Text>
        </Box>
        <Group gap="xs">
          {cycle.status === "draft" && onDelete && (
            <Button variant="light" color="red" size="sm" onClick={onDelete}>
              <IconTrash size={16} />
            </Button>
          )}
          <Button variant="light" onClick={onOpen}>
            Открыть
          </Button>
        </Group>
      </Group>
    </Card>
  );
}

function DetailedReviewModal({
  cycle,
  skillsById,
  role,
  editValues,
  setEditValues,
  updateAssessment,
  submitReview,
  proceedToInterview,
  proceedToDecision,
  finalizeReview,
  returnToDraft,
  onClose,
}: {
  cycle: ReviewCycle | null;
  skillsById: Record<string, Skill>;
  role: string;
  editValues: Record<string, number | null>;
  setEditValues: (v: Record<string, number | null>) => void;
  updateAssessment: (skillId: string, data: Record<string, unknown>) => void;
  submitReview: (cycleId: string) => void;
  proceedToInterview: (cycleId: string, comment: string) => void;
  proceedToDecision: (cycleId: string, comment: string) => void;
  finalizeReview: (cycleId: string, decision: string, comment: string) => void;
  returnToDraft: (cycleId: string) => void;
  onClose: () => void;
}) {
  const [comment, setComment] = useState("");
  const [commentErrors, setCommentErrors] = useState<Set<string>>(new Set());

  if (!cycle) return null;

  const isEmployee = role === "employee";
  const isManager = role === "admin" || role === "manager";
  const isExpert = role === "admin" || role === "expert";
  const canDecide = role === "admin" || role === "manager";

  const levels = [
    { value: "1", label: "1 — Начальный" },
    { value: "2", label: "2 — Базовый" },
    { value: "3", label: "3 — Средний" },
    { value: "4", label: "4 — Продвинутый" },
  ];

  const categories = [...new Set(cycle.assessments.map((a) => skillsById[a.skill_id]?.category).filter(Boolean))];

  const allDraftFilled = isEmployee && cycle.status === "draft"
    ? cycle.assessments.some((a) => a.self_level != null && a.self_comment?.trim())
    : true;

  const levelBadgeColor = (v: number | null) => {
    if (v == null) return "gray";
    if (v < 2) return "red";
    if (v < 3) return "yellow";
    return "green";
  };

  const catBgColors = ["#f0f4f8", "#f0f0f8", "#f4f8f0", "#f8f4f0", "#f0f8f8", "#f8f0f4", "#f4f4f0", "#f0f4f4"];

  const editSelf = isEmployee && cycle.status === "draft";
  const editManager = isManager && cycle.status === "manager_review";
  const editExpert = isExpert && cycle.status === "interview";

  return (
    <>
      <Modal opened={!!cycle} onClose={onClose} title="Детали цикла оценки" size="xl" centered>
        <Box>
          <Group gap="xs" mb="md">
            <Badge size="lg">{translateGrade(cycle.current_grade)} → {translateGrade(cycle.target_grade)}</Badge>
            <Badge color={STATUS_COLORS[cycle.status]} variant="light" size="lg">
              {STATUS_LABELS[cycle.status]}
            </Badge>
          </Group>

          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Навык</Table.Th>
                <Table.Th ta="center" w={140}>Самооценка</Table.Th>
                <Table.Th ta="center" w={140}>Оценка рук-ля</Table.Th>
                <Table.Th ta="center" w={140}>Оценка эксперта</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {categories.map((cat, ci) => (
                <>
                  <Table.Tr key={`cat-${cat}`}>
                    <Table.Td
                      colSpan={4}
                      style={{
                        background: catBgColors[ci % catBgColors.length],
                        fontWeight: 700,
                        fontSize: 13,
                        color: "var(--mantine-color-indigo-7)",
                        padding: "10px 16px",
                        borderBottom: "2px solid var(--mantine-color-indigo-2)",
                      }}
                    >
                      {cat}
                    </Table.Td>
                  </Table.Tr>
                  {cycle.assessments
                    .filter((a) => skillsById[a.skill_id]?.category === cat)
                    .map((assessment) => {
                      const skill = skillsById[assessment.skill_id];
                      if (!skill) return null;
                      const showComment = editSelf
                        ? assessment.self_level != null
                        : assessment.self_comment != null;
                      return (
                        <Fragment key={assessment.id}>
                          <Table.Tr>
                            <Table.Td style={{ verticalAlign: "middle" }}>
                              <Text fw={500} size="sm">{skill.name}</Text>
                            </Table.Td>
                            <Table.Td ta="center" style={{ verticalAlign: "middle" }}>
                              {editSelf ? (
                                <Select
                                  size="xs"
                                  w={130}
                                  data={levels}
                                  value={String(assessment.self_level || "")}
                                  onChange={(v) => {
                                    const val = v ? Number(v) : null;
                                    setEditValues({ ...editValues, [assessment.skill_id]: val });
                                    updateAssessment(assessment.skill_id, { self_level: val });
                                  }}
                                  placeholder="—"
                                  clearable
                                />
                              ) : (
                                <Badge color={levelBadgeColor(assessment.self_level)} variant="light" size="lg">
                                  {assessment.self_level ?? "—"}
                                </Badge>
                              )}
                            </Table.Td>
                            <Table.Td ta="center" style={{ verticalAlign: "middle" }}>
                              {editManager ? (
                                <Select
                                  size="xs"
                                  w={130}
                                  data={levels}
                                  value={String(assessment.manager_level || "")}
                                  onChange={(v) => {
                                    const val = v ? Number(v) : null;
                                    updateAssessment(assessment.skill_id, { manager_level: val });
                                  }}
                                  placeholder="—"
                                  clearable
                                />
                              ) : (
                                <Badge color={levelBadgeColor(assessment.manager_level)} variant="light" size="lg">
                                  {assessment.manager_level ?? "—"}
                                </Badge>
                              )}
                            </Table.Td>
                            <Table.Td ta="center" style={{ verticalAlign: "middle" }}>
                              {editExpert ? (
                                <Select
                                  size="xs"
                                  w={130}
                                  data={levels}
                                  value={String(assessment.expert_level || "")}
                                  onChange={(v) => {
                                    const val = v ? Number(v) : null;
                                    updateAssessment(assessment.skill_id, { expert_level: val });
                                  }}
                                  placeholder="—"
                                  clearable
                                />
                              ) : (
                                <Badge color={levelBadgeColor(assessment.expert_level)} variant="light" size="lg">
                                  {assessment.expert_level ?? "—"}
                                </Badge>
                              )}
                            </Table.Td>
                          </Table.Tr>
                          {showComment && (
                            <Table.Tr>
                              <Table.Td colSpan={2} style={{ padding: "4px 16px 8px" }}>
                                {editSelf ? (
                                  <Textarea
                                    size="xs"
                                    w="100%"
                                    placeholder="Комментарий"
                                    value={assessment.self_comment || ""}
                                    error={commentErrors.has(assessment.skill_id)}
                                    onChange={(e) => {
                                      setCommentErrors((prev) => { const next = new Set(prev); next.delete(assessment.skill_id); return next; });
                                      updateAssessment(assessment.skill_id, { self_comment: e.currentTarget.value });
                                    }}
                                    minRows={2}
                                    maxRows={4}
                                    autosize
                                  />
                                ) : (
                                  <Text size="xs" c="dimmed" style={{ fontStyle: "italic", lineHeight: 1.4 }}>
                                    {assessment.self_comment}
                                  </Text>
                                )}
                              </Table.Td>
                              <Table.Td colSpan={2}></Table.Td>
                            </Table.Tr>
                          )}
                        </Fragment>
                      );
                    })}
                </>
              ))}
            </Table.Tbody>
          </Table>

          {isEmployee && cycle.status === "draft" && (
            <Group justify="flex-end" mt="md">
              <Button
                variant="default"
                onClick={() => {
                  const anyFilled = cycle.assessments.some((a) => a.self_level != null && a.self_comment?.trim());
                  if (!anyFilled) {
                    notifications.show({
                      color: "red",
                      title: "Ошибка",
                      message: "Заполните хотя бы один навык с самооценкой и комментарием",
                    });
                    return;
                  }
                  setCommentErrors(new Set());
                  notifications.show({ color: "green", title: "Сохранено", message: "Изменения сохранены. Вы можете продолжить позже." });
                  onClose();
                }}
              >
                Сохранить
              </Button>
              <Button
                leftSection={<IconSend size={16} />}
                disabled={!allDraftFilled}
                onClick={async () => {
                  await submitReview(cycle.id);
                  onClose();
                }}
              >
                Отправить на проверку
              </Button>
            </Group>
          )}

          {isManager && cycle.status === "manager_review" && (
            <Stack mt="md">
              <Textarea
                label="Комментарий руководителя"
                placeholder="Общий комментарий по результатам..."
                value={comment}
                onChange={(e) => setComment(e.currentTarget.value)}
                minRows={4}
                autosize
              />
              <Group justify="flex-end">
                <Button
                  variant="default"
                  leftSection={<IconDeviceFloppy size={16} />}
                  onClick={() => {
                    notifications.show({ color: "green", title: "Сохранено", message: "Оценка сохранена. Вы можете продолжить позже." });
                    onClose();
                  }}
                >
                  Сохранить
                </Button>
                <Button
                  variant="light"
                  color="orange"
                  leftSection={<IconArrowBackUp size={16} />}
                  onClick={async () => {
                    await returnToDraft(cycle.id);
                    onClose();
                  }}
                >
                  Вернуть сотруднику
                </Button>
                <Button
                  leftSection={<IconArrowRight size={16} />}
                  onClick={async () => {
                    await proceedToInterview(cycle.id, comment);
                    onClose();
                  }}
                >
                  Отправить на интервью
                </Button>
              </Group>
            </Stack>
          )}

          {isExpert && cycle.status === "interview" && (
            <Stack mt="md">
              {cycle.manager_comment && (
                <Alert title="Комментарий руководителя" color="yellow">
                  {cycle.manager_comment}
                </Alert>
              )}
              <Textarea
                label="Заключение эксперта"
                placeholder="Результаты интервью..."
                value={comment}
                onChange={(e) => setComment(e.currentTarget.value)}
                minRows={4}
                autosize
              />
              <Group justify="flex-end">
                <Button
                  variant="default"
                  leftSection={<IconDeviceFloppy size={16} />}
                  onClick={() => {
                    notifications.show({ color: "green", title: "Сохранено", message: "Оценка сохранена. Вы можете продолжить позже." });
                    onClose();
                  }}
                >
                  Сохранить
                </Button>
                <Button
                  leftSection={<IconArrowRight size={16} />}
                  onClick={async () => {
                    await proceedToDecision(cycle.id, comment);
                    onClose();
                  }}
                >
                  Завершить интервью
                </Button>
              </Group>
            </Stack>
          )}

          {canDecide && cycle.status === "decision" && (
            <Stack mt="md">
              {cycle.manager_comment && (
                <Alert title="Комментарий руководителя" color="yellow">{cycle.manager_comment}</Alert>
              )}
              {cycle.expert_comment && (
                <Alert title="Заключение эксперта" color="blue">{cycle.expert_comment}</Alert>
              )}
              <Textarea
                label="Финальный комментарий"
                placeholder="Обоснование решения..."
                value={comment}
                onChange={(e) => setComment(e.currentTarget.value)}
                minRows={4}
                autosize
              />
              <Group justify="flex-end">
                <Button
                  color="green"
                  leftSection={<IconCheck size={16} />}
                  onClick={async () => {
                    await finalizeReview(cycle.id, "promoted", comment);
                    onClose();
                  }}
                >
                  Повысить
                </Button>
                <Button
                  color="red"
                  leftSection={<IconX size={16} />}
                  onClick={async () => {
                    await finalizeReview(cycle.id, "rejected", comment);
                    onClose();
                  }}
                >
                  Отклонить
                </Button>
              </Group>
            </Stack>
          )}

          {cycle.final_decision && (
            <Alert
              mt="md"
              title={cycle.final_decision === "promoted" ? "Повышение" : "Отказ"}
              color={cycle.final_decision === "promoted" ? "green" : "red"}
            >
              {cycle.final_comment || "Решение принято."}
            </Alert>
          )}
        </Box>
      </Modal>
    </>
  );
}
