import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Title, Table, Loader, Center, Group, Text, Badge, Card, ThemeIcon, Select, TextInput } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconTable, IconSearch, IconStar } from "@tabler/icons-react";
import client from "../api/client";
import { translateGrade } from "../constants";
import type { Cell, Employee, Score, Skill } from "../types";

const levelText = (v: number | null) => (v != null ? String(v) : "—");

const categoryColors: Record<string, string> = {
  "Тестирование": "#f0f4f8",
  "Инструменты": "#f4f0f8",
  "Процессы": "#f8f4f0",
};

export function MatrixPage() {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [cells, setCells] = useState<Cell[]>([]);
  const [scores, setScores] = useState<Record<string, Score>>({});
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState<string>("");
  const [employeeSearch, setEmployeeSearch] = useState("");

  const loadData = () => Promise.all([
    client.get("/employees").then((r) => setEmployees(r.data.filter((e: Employee) => e.role === "employee"))),
    client.get("/skills").then((r) => setSkills(r.data)),
    client.get("/assessments/matrix").then((r) => setCells(r.data)),
  ]).catch(() => {
    notifications.show({ title: "Ошибка", message: "Не удалось загрузить матрицу", color: "red" });
  });

  const loadScores = async (emps: Employee[]) => {
    if (emps.length === 0) return;
    try {
      const { data } = await client.post("/employees/scores", { employee_ids: emps.map((e) => e.id) });
      setScores(data);
    } catch {
      notifications.show({ title: "Ошибка", message: "Не удалось загрузить баллы", color: "red" });
    }
  };

  useEffect(() => {
    loadData().finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (employees.length > 0) loadScores(employees);
  }, [employees]);

  const categories = [...new Set(skills.map((s) => s.category))];
  const filteredSkills = category ? skills.filter((s) => s.category === category) : skills;
  const query = employeeSearch.toLowerCase().trim();
  const filteredEmployees = query
    ? employees.filter((e) => e.full_name.toLowerCase().includes(query))
    : employees;

  const getCell = (empId: string, skillId: string) => cells.find((c) => c.employee_id === empId && c.skill_id === skillId);

  if (loading) return <Center h={300}><Loader /></Center>;

  const skillGroups: [string, Skill[]][] = category
    ? [["", filteredSkills]]
    : categories.map((cat) => [cat, filteredSkills.filter((s) => s.category === cat)]);

  return (
    <>
      <Group mb="lg">
        <ThemeIcon size="lg" radius="md" color="indigo" variant="light"><IconTable size={20} /></ThemeIcon>
        <Title order={2} fw={700}>Матрица компетенций</Title>
      </Group>

      <Group mb="md">
        <Select
          label="Категория"
          placeholder="Все категории"
          data={categories.map((c) => ({ value: c, label: c }))}
          value={category}
          onChange={(v) => setCategory(v ?? "")}
          clearable
          size="xs"
          w={200}
        />
        <TextInput
          label="Сотрудник"
          placeholder="Поиск по имени"
          leftSection={<IconSearch size={14} />}
          value={employeeSearch}
          onChange={(e) => setEmployeeSearch(e.currentTarget.value)}
          size="xs"
          w={200}
        />
        {category && <Text size="xs" c="dimmed" mt={20}>{filteredSkills.length} навыков</Text>}
        {query && <Text size="xs" c="dimmed" mt={20}>{filteredEmployees.length} сотрудников</Text>}
      </Group>

      {filteredSkills.length === 0 ? (
        <Card padding="xl" radius="lg" ta="center"><Text c="dimmed">Выберите категорию навыков</Text></Card>
      ) : (
        <Card padding="0" radius="lg" mb="md" style={{ overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <Table striped={false} highlightOnHover={false}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th style={{ position: "sticky", left: 0, background: "var(--mantine-color-indigo-0)", zIndex: 2, whiteSpace: "nowrap", width: 1 }}>
                    <Text fw={600} size="xs">Навык</Text>
                  </Table.Th>
                  {filteredEmployees.map((emp) => (
                    <Table.Th key={emp.id} ta="center" style={{ background: "var(--mantine-color-gray-0)", padding: "10px 4px" }}>
                        <Text
                          size="xs"
                          fw={600}
                          style={{ cursor: "pointer", color: "var(--mantine-color-indigo-7)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "block" }}
                          onClick={() => navigate(`/employees/${emp.id}`)}
                        >
                          {emp.full_name}
                        </Text>
                        {emp.grade && <Badge size="xs" color="gray" variant="dot" mt={2}>{translateGrade(emp.grade)}</Badge>}
                      </Table.Th>
                    ))}
                </Table.Tr>
                <Table.Tr>
                  <Table.Th style={{ position: "sticky", left: 0, background: "white", zIndex: 2, whiteSpace: "nowrap", borderRight: "1px solid var(--mantine-color-gray-2)" }}>
                    <Text fw={600} size="xs">Итоговый балл по навыкам</Text>
                  </Table.Th>
                  {filteredEmployees.map((emp) => {
                    const s = scores[emp.id];
                    return (
                      <Table.Td key={emp.id} ta="center" style={{ padding: "4px 8px" }}>
                        {s ? (
                          <Text size="xs" fw={700}>
                            {s.current_score}
                            {s.target_score != null && <Text component="span" size="xs" c="dimmed" fw={400}> / {s.target_score}</Text>}
                          </Text>
                        ) : (
                          <Text size="xs" c="#bbb">—</Text>
                        )}
                      </Table.Td>
                    );
                  })}
                </Table.Tr>
                <Table.Tr>
                  <Table.Th style={{ position: "sticky", left: 0, background: "white", zIndex: 2, whiteSpace: "nowrap", borderRight: "1px solid var(--mantine-color-gray-2)" }}>
                    <Text fw={600} size="xs">Грейд</Text>
                  </Table.Th>
                  {filteredEmployees.map((emp) => {
                    const s = scores[emp.id];
                    return (
                      <Table.Td key={emp.id} ta="center" style={{ padding: "4px 8px" }}>
                        {s?.profile_grade != null ? <Text size="xs" fw={700}>{s.profile_grade}</Text> : <Text size="xs" c="#bbb">—</Text>}
                      </Table.Td>
                    );
                  })}
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {skillGroups.map(([cat, group]) => (
                  <>
                    {cat && (
                      <Table.Tr key={`cat-${cat}`}>
                        <Table.Td colSpan={filteredEmployees.length + 1} style={{ background: categoryColors[cat] || "#f0f0f0", padding: "3px 10px" }}>
                          <Text fw={600} size="xs">{cat}</Text>
                        </Table.Td>
                      </Table.Tr>
                    )}
                    {group.map((s) => (
                      <Table.Tr key={s.id}>
                        <Table.Td style={{ position: "sticky", left: 0, background: "white", zIndex: 1, borderRight: "1px solid var(--mantine-color-gray-2)", whiteSpace: "nowrap" }}>
                          <Group gap={4} wrap="nowrap">
                            {s.weight >= 3 && <IconStar size={12} style={{ color: "var(--mantine-color-yellow-6)", flexShrink: 0 }} />}
                            <Text
                              size="xs"
                              fw={500}
                              style={{ cursor: "pointer", color: "var(--mantine-color-indigo-7)" }}
                              onClick={() => navigate(`/skills/${s.id}`)}
                            >
                              {s.name}
                            </Text>
                          </Group>
                        </Table.Td>
                        {filteredEmployees.map((emp) => {
                          const c = getCell(emp.id, s.id);
                          const level = c?.manager_level ?? c?.self_level ?? null;
                          return (
                            <Table.Td
                              key={emp.id}
                              ta="center"
                              style={{ padding: "6px 8px" }}
                            >
                              <Text size="sm" c={level != null ? "#444" : "#bbb"}>{levelText(level)}</Text>
                            </Table.Td>
                          );
                        })}
                      </Table.Tr>
                    ))}
                  </>
                ))}
              </Table.Tbody>
            </Table>
          </div>
        </Card>
      )}

      <Group mt="md" gap="xs">
        <Text size="xs" c="dimmed">уровни: 1 · 2 · 3 · 4</Text>
        <Text size="xs" c="dimmed" ml="md">имя → страница сотрудника · название → описание навыка</Text>
      </Group>
    </>
  );
}
