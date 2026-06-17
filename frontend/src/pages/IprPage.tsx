import { useEffect, useState } from "react";
import { Title, Card, Text, Group, Badge, Table, Loader, Center, Progress, Button, Modal, TextInput, Textarea, Select, Stack, ThemeIcon, RingProgress } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconPlus, IconTarget } from "@tabler/icons-react";
import { useAuth } from "../store/auth";
import client from "../api/client";

interface Goal { id: string; skill_id: string; current_level: number; target_level: number; status: string; due_date: string | null; notes: string | null; }
interface IprPlan { id: string; employee_id: string; title: string; description: string | null; status: string; goals: Goal[]; }
interface Employee { id: string; full_name: string; }
interface Skill { id: string; name: string; }

const statusColor: Record<string, string> = { draft: "gray", active: "blue", completed: "green", cancelled: "red" };
const goalStatusColor: Record<string, string> = { pending: "gray", in_progress: "yellow", achieved: "green", overdue: "red" };
const goalStatusOptions = [
  { value: "pending", label: "Ожидает" }, { value: "in_progress", label: "В работе" },
  { value: "achieved", label: "Достигнута" }, { value: "overdue", label: "Просрочена" },
];

export function IprPage() {
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "manager";
  const [plans, setPlans] = useState<IprPlan[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [addGoalModal, setAddGoalModal] = useState<string | null>(null);
  const [form, setForm] = useState({
    employee_id: "", title: "", description: "",
    skill_id: "", current_level: "1", target_level: "3", due_date: "", notes: "",
  });

  const loadPlans = () => {
    if (!user) return;
    const endpoint = isManager ? "/ipr-plans" : `/ipr-plans?employee_id=${user.id}`;
    return client.get(endpoint).then((r) => setPlans(r.data));
  };

  useEffect(() => {
    if (!user) return;
    Promise.all([
      loadPlans(),
      isManager ? client.get("/employees").then((r) => setEmployees(r.data)) : Promise.resolve(),
      client.get("/skills").then((r) => setSkills(r.data)),
    ]).catch((err) => {
      console.error("Failed to load IPR data", err);
    }).finally(() => setLoading(false));
  }, [user]);

  const goalOptions = skills.map((s) => ({ value: s.id, label: s.name }));

  const createPlan = async () => {
    try {
      await client.post("/ipr-plans", { employee_id: form.employee_id, title: form.title, description: form.description || null });
      notifications.show({ title: "Создано", message: "План развития создан", color: "green" });
      setCreateModal(false);
      setForm({ employee_id: "", title: "", description: "", skill_id: "", current_level: "1", target_level: "3", due_date: "", notes: "" });
      loadPlans();
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось создать план", color: "red" }); }
  };

  const addGoal = async () => {
    if (!addGoalModal) return;
    try {
      await client.post(`/ipr-plans/${addGoalModal}/goals`, {
        skill_id: form.skill_id, current_level: parseInt(form.current_level),
        target_level: parseInt(form.target_level), due_date: form.due_date || null, notes: form.notes || null,
      });
      notifications.show({ title: "Добавлено", message: "Цель добавлена", color: "green" });
      setAddGoalModal(null);
      setForm({ employee_id: "", title: "", description: "", skill_id: "", current_level: "1", target_level: "3", due_date: "", notes: "" });
      loadPlans();
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось добавить цель", color: "red" }); }
  };

  const updateGoalStatus = async (goalId: string, status: string) => {
    try {
      await client.patch(`/ipr-plans/goals/${goalId}`, { status });
      notifications.show({ title: "Обновлено", message: "Статус цели обновлён", color: "green" });
      loadPlans();
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось обновить статус", color: "red" }); }
  };

  if (loading) return <Center h={300}><Loader /></Center>;

  const employeeOptions = employees.map((e) => ({ value: e.id, label: e.full_name }));

  return (
    <>
      <Group justify="space-between" mb="lg">
        <Group>
          <ThemeIcon size="lg" radius="md" color="indigo" variant="light"><IconTarget size={20} /></ThemeIcon>
          <Title order={2} fw={700}>Индивидуальный план развития (ИПР)</Title>
        </Group>
        {isManager && (
          <Button leftSection={<IconPlus size={16} />} color="indigo" onClick={() => setCreateModal(true)}>
            Создать план
          </Button>
        )}
      </Group>

      {plans.length === 0 && (
        <Card padding="xl" radius="lg" ta="center">
          <Text c="dimmed">Нет планов развития</Text>
        </Card>
      )}

      {plans.map((plan) => {
        const achieved = plan.goals.filter((g) => g.status === "achieved").length;
        const total = plan.goals.length;
        const progress = total ? Math.round((achieved / total) * 100) : 0;
        const empName = employees.find((e) => e.id === plan.employee_id)?.full_name || "—";

        return (
          <Card key={plan.id} padding="xl" radius="lg" mb="md">
            <Group justify="space-between" mb="md">
              <div>
                <Title order={4}>{plan.title}</Title>
                {isManager && <Text size="sm" c="dimmed">Сотрудник: <b>{empName}</b></Text>}
                {plan.description && <Text size="sm" c="dimmed" mt={4}>{plan.description}</Text>}
              </div>
              <Group>
                {total > 0 && (
                  <RingProgress size={60} thickness={6} sections={[{ value: progress, color: progress === 100 ? "green" : "indigo" }]} label={<Text ta="center" size="xs" fw={700}>{progress}%</Text>} />
                )}
                <Badge color={statusColor[plan.status]} variant="light" size="lg">{plan.status}</Badge>
              </Group>
            </Group>

            {total > 0 && <Progress value={progress} mb="md" color={progress === 100 ? "green" : "indigo"} size="sm" radius="md" />}

            {plan.goals.length > 0 && (
              <Table mb="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Навык</Table.Th>
                    <Table.Th>Текущий</Table.Th>
                    <Table.Th>Целевой</Table.Th>
                    <Table.Th>Статус</Table.Th>
                    <Table.Th>Дедлайн</Table.Th>
                    {isManager && <Table.Th></Table.Th>}
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {plan.goals.map((g) => {
                    const skill = skills.find((s) => s.id === g.skill_id);
                    return (
                      <Table.Tr key={g.id}>
                        <Table.Td><Text size="sm" fw={500}>{skill?.name || g.skill_id.slice(0, 8) + "…"}</Text></Table.Td>
                        <Table.Td><Badge color="gray" variant="light">{g.current_level}</Badge></Table.Td>
                        <Table.Td><Badge color="indigo" variant="light">{g.target_level}</Badge></Table.Td>
                        <Table.Td>
                          {isManager ? (
                            <Select data={goalStatusOptions} value={g.status} onChange={(v) => updateGoalStatus(g.id, v ?? g.status)} size="xs" w={130} />
                          ) : (
                            <Badge color={goalStatusColor[g.status]} variant="light" size="sm">{g.status}</Badge>
                          )}
                        </Table.Td>
                        <Table.Td><Text size="sm">{g.due_date || "—"}</Text></Table.Td>
                        {isManager && (
                          <Table.Td>
                            <Button size="xs" variant="light" color="indigo" onClick={() => { setAddGoalModal(plan.id); setForm({ ...form, employee_id: plan.employee_id }); }}>
                              + Цель
                            </Button>
                          </Table.Td>
                        )}
                      </Table.Tr>
                    );
                  })}
                </Table.Tbody>
              </Table>
            )}

            {plan.goals.length === 0 && isManager && (
              <Button size="xs" variant="light" color="indigo" onClick={() => { setAddGoalModal(plan.id); setForm({ ...form, employee_id: plan.employee_id }); }}>
                Добавить цель
              </Button>
            )}
          </Card>
        );
      })}

      <Modal opened={createModal} onClose={() => setCreateModal(false)} title="Создать план развития" radius="lg" shadow="lg">
        <Stack>
          <Select label="Сотрудник" data={employeeOptions} value={form.employee_id} onChange={(v) => setForm({ ...form, employee_id: v ?? "" })} searchable required />
          <TextInput label="Название" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <Textarea label="Описание" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Button onClick={createPlan} color="indigo">Создать</Button>
        </Stack>
      </Modal>

      <Modal opened={!!addGoalModal} onClose={() => setAddGoalModal(null)} title="Добавить цель" radius="lg" shadow="lg">
        <Stack>
          <Select label="Навык" data={goalOptions} value={form.skill_id} onChange={(v) => setForm({ ...form, skill_id: v ?? "" })} searchable required />
          <TextInput label="Текущий уровень" type="number" min={1} max={3} value={form.current_level} onChange={(e) => setForm({ ...form, current_level: e.target.value })} />
          <TextInput label="Целевой уровень" type="number" min={1} max={3} value={form.target_level} onChange={(e) => setForm({ ...form, target_level: e.target.value })} />
          <TextInput label="Дедлайн (YYYY-MM-DD)" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          <Textarea label="Заметки" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <Button onClick={addGoal} color="indigo">Добавить</Button>
        </Stack>
      </Modal>
    </>
  );
}
