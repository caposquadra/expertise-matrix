import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import { Card, Text, Group, Badge, Table, Loader, Center, Button, ThemeIcon, Title } from "@mantine/core";
import { IconArrowLeft, IconBook2 } from "@tabler/icons-react";
import client from "../api/client";

interface Skill { id: string; name: string; category: string; description: string | null; weight: number; }

interface LevelInfo { level: number; title: string; what: string; }

const levelInfos: LevelInfo[] = [
  {
    level: 1,
    title: "Начальный",
    what: "Знает базовые понятия и термины. Выполняет простые задачи под руководством. Требуется помощь наставника.",
  },
  {
    level: 2,
    title: "Базовый",
    what: "Самостоятельно выполняет типовые задачи. Понимает основные принципы и подходы. Может объяснить базовые концепции.",
  },
  {
    level: 3,
    title: "Средний",
    what: "Уверенно решает задачи средней сложности. Выбирает подходящие инструменты и методы. Может обучать коллег начального уровня.",
  },
  {
    level: 4,
    title: "Продвинутый",
    what: "Эксперт в области. Оптимизирует процессы и внедряет улучшения. Разрабатывает стандарты и подходы. Может обучать коллег любого уровня.",
  },
];

export function SkillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    client.get(`/skills/${id}`).then((r) => setSkill(r.data)).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Center h={300}><Loader /></Center>;
  if (!skill) return <Center h={300}><Text c="dimmed">Навык не найден</Text></Center>;

  return (
    <>
      <Button variant="subtle" leftSection={<IconArrowLeft size={16} />} onClick={() => navigate("/matrix")} mb="md" c="gray">
        Назад к матрице
      </Button>

      <Group mb="xl">
        <ThemeIcon size="lg" radius="md" color="indigo" variant="light"><IconBook2 size={20} /></ThemeIcon>
        <div>
          <Title order={2} fw={700}>{skill.name}</Title>
          <Group gap={8} mt={2}>
            <Badge color="indigo" variant="light">{skill.category}</Badge>
            {skill.description && <Text size="sm" c="dimmed">{skill.description}</Text>}
          </Group>
        </div>
      </Group>

      <Card padding="0" radius="lg" mb="md" style={{ overflow: "hidden" }}>
        <Table striped={false}>
          <Table.Thead>
            <Table.Tr style={{ background: "var(--mantine-color-gray-0)" }}>
              <Table.Th w={80} ta="center">Уровень</Table.Th>
              <Table.Th w={160}>Название</Table.Th>
              <Table.Th>Что нужно знать и уметь</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {levelInfos.map((li) => (
              <Table.Tr key={li.level}>
                <Table.Td ta="center">
                  <Badge color={["red", "orange", "yellow", "green"][li.level - 1]} variant="filled" size="xl">{li.level}</Badge>
                </Table.Td>
                <Table.Td fw={600}>{li.title}</Table.Td>
                <Table.Td><Text size="sm">{li.what}</Text></Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>
    </>
  );
}
