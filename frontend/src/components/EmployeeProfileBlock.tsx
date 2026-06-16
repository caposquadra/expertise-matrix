import { useEffect, useState } from "react";
import { Card, Text, Group, Badge, Button, Modal, TextInput, NumberInput, Textarea, Stack, SimpleGrid, Loader, Center, Progress } from "@mantine/core";
import client from "../api/client";
import { useAuth } from "../store/auth";
import type { EmployeeProfile } from "../types";

const FIELDS: { key: keyof EmployeeProfile; label: string }[] = [
  { key: "organization", label: "Организация" },
  { key: "city", label: "Город" },
  { key: "department", label: "Департамент" },
  { key: "subdivision", label: "Подразделение" },
  { key: "position", label: "Должность" },
  { key: "specialization", label: "Специализация" },
];

const NUMERIC_LABELS: { key: keyof EmployeeProfile; label: string }[] = [
  { key: "experience", label: "Опыт" },
  { key: "education", label: "Образование" },
  { key: "task_complexity", label: "Сложность задач" },
  { key: "autonomy", label: "Автономность" },
  { key: "communication", label: "Коммуникации" },
  { key: "control", label: "Контроль" },
  { key: "mentoring", label: "Наставничество" },
  { key: "responsibility", label: "Ответственность" },
  { key: "technical_competencies", label: "Технические компетенции" },
];

interface Props {
  employeeId: string;
}

export function EmployeeProfileBlock({ employeeId }: Props) {
  const { user } = useAuth();
  const isManager = user?.role === "admin" || user?.role === "manager";
  const [profile, setProfile] = useState<EmployeeProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModal, setEditModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string | number | null>>({});

  useEffect(() => {
    setLoading(true);
    client.get(`/employees/${employeeId}/profile`)
      .then((r) => {
        setProfile(r.data);
        if (r.data) {
          setForm({
            organization: r.data.organization,
            city: r.data.city,
            department: r.data.department,
            subdivision: r.data.subdivision,
            position: r.data.position,
            specialization: r.data.specialization,
            experience: r.data.experience,
            education: r.data.education,
            task_complexity: r.data.task_complexity,
            autonomy: r.data.autonomy,
            communication: r.data.communication,
            control: r.data.control,
            mentoring: r.data.mentoring,
            responsibility: r.data.responsibility,
            technical_competencies: r.data.technical_competencies,
            notes: r.data.notes ?? "",
          });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [employeeId]);

  const openEdit = () => {
    if (!profile) {
      setForm({
        organization: "РЕД СОФТ",
        city: "Санкт-Петербург",
        department: "",
        subdivision: "Отдел тестирования ВРМ",
        position: "",
        specialization: "",
        experience: 8,
        education: 8,
        task_complexity: 8,
        autonomy: 8,
        communication: 8,
        control: 8,
        mentoring: 8,
        responsibility: 8,
        technical_competencies: 8,
        notes: "",
      });
    }
    setEditModal(true);
  };

  const save = async () => {
    setSaving(true);
    try {
      const body: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(form)) {
        if (val !== null && val !== "") {
          body[key] = val;
        }
      }
      const { data } = await client.put(`/employees/${employeeId}/profile`, body);
      setProfile(data);
      setEditModal(false);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Center h={100}><Loader size="sm" /></Center>;

  return (
    <>
      <Card padding="lg" radius="lg" mb="xl" withBorder>
        <Group justify="space-between" mb="md">
          <Group gap="xs">
            <Text fw={700}>Профиль сотрудника</Text>
            {profile && (
              <Badge size="lg" variant="filled" color="indigo" style={{ paddingLeft: 10, paddingRight: 10 }}>
                Грейд {profile.grade}
              </Badge>
            )}
          </Group>
          {isManager && (
            <Button size="xs" variant="light" color="indigo" onClick={openEdit}>
              {profile ? "Редактировать" : "Заполнить"}
            </Button>
          )}
        </Group>

        {!profile && !isManager && (
          <Text c="dimmed" size="sm">Профиль не заполнен</Text>
        )}
        {!profile && isManager && (
          <Text c="dimmed" size="sm">Нажмите «Заполнить», чтобы добавить данные</Text>
        )}

        {profile && (
          <>
            {FIELDS.map(({ key, label }) => (
              <Group key={key} mb={2}>
                <Text size="sm" c="dimmed" w={140}>{label}</Text>
                <Text size="sm">{String(profile[key] ?? "—")}</Text>
              </Group>
            ))}

            <Text fw={600} size="sm" mt="md" mb="sm">Оценки (1–12)</Text>
            <SimpleGrid cols={{ base: 1, md: 2 }}>
              {NUMERIC_LABELS.map(({ key, label }) => {
                const val = profile[key] as number;
                return (
                  <Group key={key} gap="xs" wrap="nowrap">
                    <Text size="sm" w={140}>{label}</Text>
                    <Progress.Root w="100%" size={20} style={{ flex: 1 }}>
                      <Progress.Section value={(val / 12) * 100} color={val >= 8 ? "green" : val >= 5 ? "yellow" : "red"} />
                    </Progress.Root>
                    <Text size="sm" fw={600} w={40} ta="right">{val}/12</Text>
                  </Group>
                );
              })}
            </SimpleGrid>

            {profile.notes && (
              <Text size="sm" mt="sm">
                <Text span fw={600}>Особенности: </Text>
                {profile.notes}
              </Text>
            )}
          </>
        )}
      </Card>

      <Modal opened={editModal} onClose={() => setEditModal(false)} title="Редактировать профиль" size="lg" radius="lg">
        <Stack>
          <TextInput label="Организация" value={form.organization as string} onChange={(e) => setForm({ ...form, organization: e.currentTarget.value })} />
          <TextInput label="Город" value={form.city as string} onChange={(e) => setForm({ ...form, city: e.currentTarget.value })} />
          <TextInput label="Департамент" value={form.department as string} onChange={(e) => setForm({ ...form, department: e.currentTarget.value })} />
          <TextInput label="Подразделение" value={form.subdivision as string} onChange={(e) => setForm({ ...form, subdivision: e.currentTarget.value })} />
          <TextInput label="Должность" value={form.position as string} onChange={(e) => setForm({ ...form, position: e.currentTarget.value })} />
          <TextInput label="Специализация" value={form.specialization as string} onChange={(e) => setForm({ ...form, specialization: e.currentTarget.value })} />
          <Textarea label="Особенности" value={form.notes as string} onChange={(e) => setForm({ ...form, notes: e.currentTarget.value })} />

          <Text fw={600} mt="sm">Оценки (1–12)</Text>
          <SimpleGrid cols={2}>
            {NUMERIC_LABELS.map(({ key, label }) => (
              <NumberInput
                key={key}
                label={label}
                min={1}
                max={12}
                value={form[key] as number}
                onChange={(v) => setForm({ ...form, [key]: typeof v === "string" ? parseInt(v) : v ?? 8 })}
              />
            ))}
          </SimpleGrid>

          <Button fullWidth onClick={save} loading={saving} color="indigo" mt="md">Сохранить</Button>
        </Stack>
      </Modal>
    </>
  );
}
