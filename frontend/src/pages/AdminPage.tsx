import { useEffect, useState } from "react";
import { Title, Tabs, Table, Badge, Button, Group, Modal, TextInput, Loader, Center, ActionIcon, ThemeIcon, Card, Text, Select, NumberInput } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { IconEdit, IconTrash, IconPlus, IconDownload, IconSettings, IconKey } from "@tabler/icons-react";
import client, { getAccessToken } from "../api/client";
import { translateRole, translateGrade } from "../constants";

interface Skill { id: string; name: string; category: string; description: string | null; weight: number; sort_order: number; is_active: boolean; }
interface Employee { id: string; email: string; full_name: string; role: string; grade: string | null; is_active: boolean; }

export function AdminPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [skillModal, setSkillModal] = useState(false);
  const [editSkill, setEditSkill] = useState<Skill | null>(null);
  const [skillForm, setSkillForm] = useState({ name: "", category: "", description: "", weight: 1, sort_order: 0 });
  const [userModal, setUserModal] = useState(false);
  const [userForm, setUserForm] = useState({ full_name: "", email: "", password: "", role: "employee", grade: "" });
  const [passwordModal, setPasswordModal] = useState(false);
  const [passwordTarget, setPasswordTarget] = useState<Employee | null>(null);
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    Promise.all([
      client.get("/skills").then((r) => setSkills(r.data)),
      client.get("/employees").then((r) => setEmployees(r.data)),
    ]).catch((err) => {
      console.error("Failed to load admin data", err);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Center h={300}><Loader /></Center>;

  const openSkillCreate = () => { setEditSkill(null); setSkillForm({ name: "", category: "", description: "", weight: 1, sort_order: 0 }); setSkillModal(true); };

  const openSkillEdit = (s: Skill) => { setEditSkill(s); setSkillForm({ name: s.name, category: s.category, description: s.description || "", weight: s.weight, sort_order: s.sort_order }); setSkillModal(true); };

  const saveSkill = async () => {
    try {
      if (editSkill) {
        await client.patch(`/skills/${editSkill.id}`, skillForm);
        notifications.show({ title: "Обновлено", message: "Навык обновлён", color: "green" });
      } else {
        await client.post("/skills", skillForm);
        notifications.show({ title: "Создано", message: "Навык создан", color: "green" });
      }
      setSkillModal(false);
      const { data } = await client.get("/skills");
      setSkills(data);
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось сохранить навык", color: "red" }); }
  };

  const deleteSkill = async (id: string) => {
    try {
      await client.delete(`/skills/${id}`);
      setSkills((prev) => prev.filter((s) => s.id !== id));
      notifications.show({ title: "Удалено", message: "Навык деактивирован", color: "orange" });
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось удалить навык", color: "red" }); }
  };

  const toggleActive = async (s: Skill) => {
    try {
      const { data } = await client.patch(`/skills/${s.id}`, { is_active: !s.is_active });
      setSkills((prev) => prev.map((sk) => (sk.id === s.id ? data : sk)));
      notifications.show({ title: "Обновлено", message: `Навык ${data.is_active ? "активирован" : "деактивирован"}`, color: "green" });
    } catch { notifications.show({ title: "Ошибка", message: "Не удалось изменить статус", color: "red" }); }
  };

  const downloadExport = (format: "csv" | "excel") => {
    const url = `/api/v1/export/${format}`;
    const token = getAccessToken();
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.blob())
      .then((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `expertise_matrix.${format === "csv" ? "csv" : "xlsx"}`;
        a.click();
        notifications.show({ title: "Экспорт", message: `Файл .${format} скачан`, color: "green" });
      })
      .catch(() => notifications.show({ title: "Ошибка", message: "Не удалось скачать", color: "red" }));
  };

  const categories = [...new Set(skills.map((s) => s.category))];

  return (
    <>
      <Group mb="lg">
        <ThemeIcon size="lg" radius="md" color="indigo" variant="light"><IconSettings size={20} /></ThemeIcon>
        <Title order={2} fw={700}>Администрирование</Title>
      </Group>

      <Group mb="md">
        <Button leftSection={<IconDownload size={16} />} variant="light" color="green" onClick={() => downloadExport("csv")}>CSV</Button>
        <Button leftSection={<IconDownload size={16} />} variant="light" color="blue" onClick={() => downloadExport("excel")}>Excel</Button>
      </Group>

      <Tabs defaultValue="skills" variant="pills" radius="md">
        <Tabs.List mb="md">
          <Tabs.Tab value="skills">Навыки</Tabs.Tab>
          <Tabs.Tab value="users">Пользователи</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="skills">
          <Group mb="md">
            <Button leftSection={<IconPlus size={16} />} variant="light" color="indigo" onClick={openSkillCreate}>Добавить навык</Button>
          </Group>

          {categories.map((cat) => (
            <Card key={cat} padding="md" radius="lg" mb="lg">
              <Badge size="lg" variant="filled" color="indigo" mb="sm">{cat}</Badge>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Название</Table.Th>
                    <Table.Th>Описание</Table.Th>
                    <Table.Th>Вес</Table.Th>
                    <Table.Th>Порядок</Table.Th>
                    <Table.Th>Активен</Table.Th>
                    <Table.Th>Действия</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {skills.filter((s) => s.category === cat).map((s) => (
                    <Table.Tr key={s.id}>
                      <Table.Td fw={500}>{s.name}</Table.Td>
                      <Table.Td><Text size="sm" c="dimmed">{s.description || "—"}</Text></Table.Td>
                      <Table.Td><Badge color="gray" variant="light">{s.weight}</Badge></Table.Td>
                      <Table.Td>{s.sort_order}</Table.Td>
                      <Table.Td><Badge color={s.is_active ? "green" : "red"} variant="dot" style={{ cursor: "pointer" }} onClick={() => toggleActive(s)}>{s.is_active ? "да" : "нет"}</Badge></Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <ActionIcon variant="light" color="indigo" onClick={() => openSkillEdit(s)}><IconEdit size={16} /></ActionIcon>
                          <ActionIcon variant="light" color="red" onClick={() => deleteSkill(s.id)}><IconTrash size={16} /></ActionIcon>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Card>
          ))}
        </Tabs.Panel>

        <Tabs.Panel value="users">
          <Group mb="md">
            <Button leftSection={<IconPlus size={16} />} variant="light" color="indigo" onClick={() => { setUserForm({ full_name: "", email: "", password: "", role: "employee", grade: "" }); setUserModal(true); }}>Добавить пользователя</Button>
          </Group>
          <Card padding="md" radius="lg">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Имя</Table.Th>
                  <Table.Th>Email</Table.Th>
                  <Table.Th>Роль</Table.Th>
                  <Table.Th>Грейд</Table.Th>
                  <Table.Th>Статус</Table.Th>
                  <Table.Th>Действия</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {employees.map((e) => (
                  <Table.Tr key={e.id}>
                    <Table.Td fw={500}>{e.full_name}</Table.Td>
                    <Table.Td>{e.email}</Table.Td>
                    <Table.Td><Badge color={e.role === "admin" ? "red" : e.role === "manager" ? "blue" : "gray"}>{translateRole(e.role)}</Badge></Table.Td>
                    <Table.Td>{translateGrade(e.grade)}</Table.Td>
                    <Table.Td><Badge color={e.is_active ? "green" : "red"} variant="dot">{e.is_active ? "активен" : "неактивен"}</Badge></Table.Td>
                    <Table.Td>
                      <ActionIcon variant="light" color="indigo" onClick={() => { setPasswordTarget(e); setNewPassword(""); setPasswordModal(true); }}>
                        <IconKey size={16} />
                      </ActionIcon>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Card>
        </Tabs.Panel>
      </Tabs>

      <Modal opened={userModal} onClose={() => setUserModal(false)} title="Добавить пользователя" radius="lg" shadow="lg">
        <TextInput label="Имя" value={userForm.full_name} onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })} mb="sm" required />
        <TextInput label="Email" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} mb="sm" required />
        <TextInput label="Пароль" type="password" value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} mb="sm" required />
        <Select label="Роль" data={[{ value: "employee", label: "Сотрудник" }, { value: "manager", label: "Руководитель" }]} value={userForm.role} onChange={(v) => setUserForm({ ...userForm, role: v ?? "employee" })} mb="sm" />
        <TextInput label="Грейд" value={userForm.grade} onChange={(e) => setUserForm({ ...userForm, grade: e.target.value })} mb="lg" placeholder="Junior / Middle / Senior" />
        <Button fullWidth color="indigo" onClick={async () => {
          try {
            await client.post("/employees", userForm);
            notifications.show({ title: "Создано", message: "Пользователь создан", color: "green" });
            setUserModal(false);
            const { data } = await client.get("/employees");
            setEmployees(data);
          } catch { notifications.show({ title: "Ошибка", message: "Не удалось создать пользователя", color: "red" }); }
        }}>Создать</Button>
      </Modal>

      <Modal opened={passwordModal} onClose={() => setPasswordModal(false)} title={`Смена пароля — ${passwordTarget?.full_name}`} radius="lg" shadow="lg">
        <TextInput label="Новый пароль" type="password" value={newPassword} onChange={(e) => setNewPassword(e.currentTarget.value)} mb="lg" required />
        <Button fullWidth color="indigo" onClick={async () => {
          if (!passwordTarget || !newPassword) return;
          try {
            await client.patch(`/employees/${passwordTarget.id}`, { password: newPassword });
            notifications.show({ title: "Сохранено", message: "Пароль обновлён", color: "green" });
            setPasswordModal(false);
          } catch { notifications.show({ title: "Ошибка", message: "Не удалось обновить пароль", color: "red" }); }
        }}>Сохранить</Button>
      </Modal>

      <Modal opened={skillModal} onClose={() => setSkillModal(false)} title={editSkill ? "Редактировать навык" : "Добавить навык"} radius="lg" shadow="lg">
        <TextInput label="Название" value={skillForm.name} onChange={(e) => setSkillForm({ ...skillForm, name: e.target.value })} mb="sm" />
        <TextInput label="Категория" value={skillForm.category} onChange={(e) => setSkillForm({ ...skillForm, category: e.target.value })} mb="sm" />
        <TextInput label="Описание" value={skillForm.description} onChange={(e) => setSkillForm({ ...skillForm, description: e.target.value })} mb="sm" />
        <NumberInput label="Вес (1–5)" min={1} max={5} value={skillForm.weight} onChange={(v) => setSkillForm({ ...skillForm, weight: typeof v === "string" ? parseInt(v) : v ?? 1 })} mb="sm" />
        <TextInput label="Порядок сортировки" type="number" value={skillForm.sort_order.toString()} onChange={(e) => setSkillForm({ ...skillForm, sort_order: parseInt(e.target.value) || 0 })} mb="lg" />
        <Button fullWidth onClick={saveSkill} color="indigo">{editSkill ? "Сохранить" : "Создать"}</Button>
      </Modal>
    </>
  );
}
