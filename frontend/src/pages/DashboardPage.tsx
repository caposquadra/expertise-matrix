import { useEffect, useState } from "react";
import { Title, SimpleGrid, Card, Text, Group, Badge, Loader, Center, Table, ThemeIcon, ScrollArea, Anchor } from "@mantine/core";
import { IconUsers, IconChartBar, IconStar, IconHistory, IconClipboardCheck, IconUserX, IconTrendingDown, IconArrowUp, IconFileCheck, IconPercentage } from "@tabler/icons-react";
import client from "../api/client";
import { translateGrade } from "../constants";
import { useAuth } from "../store/auth";
import { Link } from "react-router-dom";

import type { Summary, Change, ReviewCyclesSummary, WeakestSkill, RecentDecision, PromotionReady } from "../types";

const statusLabels: Record<string, string> = {
  draft: "Черновик", manager_review: "У руководителя", interview: "Интервью", decision: "Решение", completed: "Завершено", rejected: "Отклонено",
};
const statusColors: Record<string, string> = {
  draft: "gray", manager_review: "orange", interview: "yellow", decision: "violet", completed: "green", rejected: "red",
};

const fieldLabels: Record<string, string> = {
  self_level: "Самооценка", manager_level: "Оценка руководителя", target_level: "Целевой уровень",
};

export function DashboardPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [changes, setChanges] = useState<Change[]>([]);
  const [cycleSummary, setCycleSummary] = useState<ReviewCyclesSummary | null>(null);
  const [weakest, setWeakest] = useState<WeakestSkill[]>([]);
  const [decisions, setDecisions] = useState<RecentDecision[]>([]);
  const [promotionReady, setPromotionReady] = useState<PromotionReady[]>([]);
  const [expandedStatus, setExpandedStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const isManager = user?.role === "admin" || user?.role === "manager";

  useEffect(() => {
    if (isManager) {
      Promise.all([
        client.get("/reports/team-summary").then((r) => setSummary(r.data)),
        client.get("/reports/review-cycles-summary").then((r) => setCycleSummary(r.data)),
        client.get("/reports/recent-changes?limit=8").then((r) => setChanges(r.data)),
        client.get("/reports/weakest-skills?limit=5").then((r) => setWeakest(r.data)),
        client.get("/reports/recent-decisions?limit=5").then((r) => setDecisions(r.data)),
        client.get("/reports/promotion-ready").then((r) => setPromotionReady(r.data)),
      ]).catch((err) => {
        console.error("Failed to load dashboard data", err);
      }).finally(() => setLoading(false));
    } else setLoading(false);
  }, [user, isManager]);

  if (loading) return <Center h={300}><Loader /></Center>;

  return (
    <>
      <Title order={2} mb="lg" fw={700}>Дашборд</Title>

      {summary && (
        <SimpleGrid cols={{ base: 1, sm: 4 }} mb="md">
          <Card padding="sm" radius="md" style={{ borderLeft: "3px solid var(--mantine-color-indigo-5)" }}>
            <Group>
              <ThemeIcon size="md" radius="md" color="indigo" variant="light"><IconUsers size={18} /></ThemeIcon>
              <div>
                <Text size="xs" c="dimmed" fw={500}>Всего сотрудников</Text>
                <Text fw={700} size="xl">{summary.total_employees}</Text>
              </div>
            </Group>
          </Card>
          <Card padding="sm" radius="md" style={{ borderLeft: "3px solid var(--mantine-color-teal-5)" }}>
            <Group>
              <ThemeIcon size="md" radius="md" color="teal" variant="light"><IconStar size={18} /></ThemeIcon>
              <div>
                <Text size="xs" c="dimmed" fw={500}>Средняя самооценка</Text>
                <Text fw={700} size="xl">{summary.avg_self_level ?? "—"}</Text>
              </div>
            </Group>
          </Card>
          <Card padding="sm" radius="md" style={{ borderLeft: "3px solid var(--mantine-color-orange-5)" }}>
            <Group>
              <ThemeIcon size="md" radius="md" color="orange" variant="light"><IconChartBar size={18} /></ThemeIcon>
              <div>
                <Text size="xs" c="dimmed" fw={500}>Средняя оценка руководителя</Text>
                <Text fw={700} size="xl">{summary.avg_manager_level ?? "—"}</Text>
              </div>
            </Group>
          </Card>
          <Card padding="sm" radius="md" style={{ borderLeft: "3px solid var(--mantine-color-violet-5)" }}>
            <Group>
              <ThemeIcon size="md" radius="md" color="violet" variant="light"><IconClipboardCheck size={18} /></ThemeIcon>
              <div>
                <Text size="xs" c="dimmed" fw={500}>Активных циклов</Text>
                <Text fw={700} size="xl">{cycleSummary?.total_active ?? "—"}</Text>
              </div>
            </Group>
          </Card>
        </SimpleGrid>
      )}

      {cycleSummary && cycleSummary.status_counts.some((s) => s.count > 0) && (
        <Card padding="lg" radius="lg" mb="xl">
          <Group mb="md">
            <ThemeIcon size="md" radius="md" color="violet" variant="light"><IconClipboardCheck size={18} /></ThemeIcon>
            <Title order={5}>Активные циклы оценки</Title>
          </Group>
          <Group mb="xs">
            {cycleSummary.status_counts.map((s) => (
              <Badge
                key={s.status}
                size="lg"
                variant={expandedStatus === s.status ? "filled" : "outline"}
                color={statusColors[s.status] || "gray"}
                style={{ cursor: "pointer" }}
                onClick={() => setExpandedStatus(expandedStatus === s.status ? null : s.status)}
              >
                {statusLabels[s.status] || s.status}: {s.count}
              </Badge>
            ))}
          </Group>
          {expandedStatus && cycleSummary.status_employees[expandedStatus]?.map((e) => (
            <Group key={e.cycle_id} justify="space-between" mb="xs" ml="sm">
              <div>
                <Anchor component={Link} to={`/employees/${e.employee_id}`} size="sm">
                  {e.employee_name}
                </Anchor>
                {e.grade && <Badge size="xs" color="blue" variant="light" ml={6}>{translateGrade(e.grade)}</Badge>}
                {e.profile_grade != null && <Badge size="xs" color="indigo" variant="light" ml={4}>{e.profile_grade}</Badge>}
              </div>
              <Badge color={statusColors[e.status!] || "gray"} variant="light" size="sm">
                {e.days_in_status} дн.
              </Badge>
            </Group>
          ))}
        </Card>
      )}

      {cycleSummary && cycleSummary.employees_without_self_assessment.length > 0 && (
        <Card padding="lg" radius="lg" mb="xl" style={{ borderLeft: "3px solid var(--mantine-color-red-5)" }}>
          <Group mb="md">
            <ThemeIcon size="md" radius="md" color="red" variant="light"><IconUserX size={18} /></ThemeIcon>
            <Title order={5}>Не начали самооценку ({cycleSummary.employees_without_self_assessment.length})</Title>
          </Group>
            {cycleSummary.employees_without_self_assessment.map((e) => (
              <Group key={e.employee_id} justify="space-between" mb="xs">
                <div>
                  <Anchor component={Link} to={`/employees/${e.employee_id}`} size="sm">
                    {e.employee_name}
                  </Anchor>
                  {e.grade && <Badge size="xs" color="blue" variant="light" ml={6}>{translateGrade(e.grade)}</Badge>}
                  {e.profile_grade != null && <Badge size="xs" color="indigo" variant="light" ml={4}>{e.profile_grade}</Badge>}
                </div>
                <Badge color={e.cycle_id ? "red" : "gray"} variant="light">
                  {e.cycle_id ? `${e.days_in_status} дн. в черновике` : "Нет заявок"}
                </Badge>
              </Group>
            ))}
        </Card>
      )}

      {summary && summary.skill_coverage && summary.skill_coverage.length > 0 && (
        <Card padding="lg" radius="lg" mb="xl">
          <Group mb="md">
            <ThemeIcon size="md" radius="md" color="cyan" variant="light"><IconPercentage size={18} /></ThemeIcon>
            <Title order={5}>Покрытие оценки по навыкам</Title>
          </Group>
          <ScrollArea h={240}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Навык</Table.Th>
                  <Table.Th>Категория</Table.Th>
                  <Table.Th>Оценено</Table.Th>
                  <Table.Th>Покрытие</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {summary.skill_coverage.map((c) => (
                  <Table.Tr key={c.skill_name}>
                    <Table.Td><Text size="sm">{c.skill_name}</Text></Table.Td>
                    <Table.Td><Text size="sm" c="dimmed">{c.category}</Text></Table.Td>
                    <Table.Td><Text size="sm">{c.employees_with_assessment}/{c.total_employees}</Text></Table.Td>
                    <Table.Td>
                      <Badge color={c.coverage_percent >= 80 ? "green" : c.coverage_percent >= 50 ? "yellow" : "red"} variant="light">
                        {c.coverage_percent}%
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Card>
      )}

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" mb="xl">
        {weakest.length > 0 && (
          <Card padding="lg" radius="lg">
            <Group mb="md">
              <ThemeIcon size="md" radius="md" color="red" variant="light"><IconTrendingDown size={18} /></ThemeIcon>
              <Title order={5}>Самые слабые навыки</Title>
            </Group>
            {weakest.map((w) => (
              <Group key={w.skill_name} justify="space-between" mb="xs">
                <div>
                  <Text size="sm">{w.skill_name}</Text>
                  <Text size="xs" c="dimmed">{w.category}</Text>
                </div>
                <Badge color="red" variant="light">{w.avg_manager_level}</Badge>
              </Group>
            ))}
          </Card>
        )}

        {promotionReady.length > 0 && (
          <Card padding="lg" radius="lg">
            <Group mb="md">
              <ThemeIcon size="md" radius="md" color="green" variant="light"><IconArrowUp size={18} /></ThemeIcon>
              <Title order={5}>Готовы к повышению</Title>
            </Group>
            {promotionReady.map((p) => (
              <Group key={p.employee_id} justify="space-between" mb="md" wrap="nowrap">
                <div style={{ minWidth: 180 }}>
                  <Anchor component={Link} to={`/employees/${p.employee_id}`} size="sm" fw={500}>
                    {p.employee_name}
                  </Anchor>
                  <Text size="xs" c="dimmed">{translateGrade(p.current_grade)} → {translateGrade(p.target_grade)}</Text>
                </div>
                <Group gap="xs" wrap="nowrap">
                  <Card padding="sm" radius="md" withBorder style={{ minWidth: 110 }}>
                    <Text size="xs" c="dimmed" mb={2}>Общий балл</Text>
                    <Group gap={4}>
                      <Text fw={700} size="md" c={p.target_score != null && p.total_score >= p.target_score ? "green" : "orange"}>
                        {Math.round(p.total_score)}
                      </Text>
                      <Text size="xs" c="dimmed">баллов</Text>
                    </Group>
                  </Card>
                  <Card padding="sm" radius="md" withBorder style={{ minWidth: 110 }}>
                    <Text size="xs" c="dimmed" mb={2}>Цель</Text>
                    <Text fw={700} size="md" c="indigo">
                      {p.target_score != null ? `${Math.round(p.target_score)} баллов` : "—"}
                    </Text>
                  </Card>
                </Group>
              </Group>
            ))}
          </Card>
        )}
      </SimpleGrid>

      {decisions.length > 0 && (
        <Card padding="lg" radius="lg" mb="xl">
          <Group mb="md">
            <ThemeIcon size="md" radius="md" color="blue" variant="light"><IconFileCheck size={18} /></ThemeIcon>
            <Title order={5}>Последние решения</Title>
          </Group>
          {decisions.map((d) => (
              <Group key={`${d.employee_id}-${d.completed_at}`} justify="space-between" mb="xs">
                <div>
                  <Anchor component={Link} to={`/employees/${d.employee_id}`} size="sm" fw={500}>
                    {d.employee_name}
                  </Anchor>
                  <Text size="xs" c="dimmed">{translateGrade(d.current_grade)} → {translateGrade(d.target_grade)}</Text>
                </div>
                <Badge color={d.decision === "promoted" ? "green" : "red"} variant="light">
                  {d.decision === "promoted" ? "Повышен" : "Отклонён"}
                </Badge>
              </Group>
            ))}
        </Card>
      )}

      {changes.length > 0 && (
        <Card padding="lg" radius="lg" mb="xl">
          <Group mb="md">
            <ThemeIcon size="md" radius="md" color="blue" variant="light"><IconHistory size={18} /></ThemeIcon>
            <Title order={5}>Последние изменения</Title>
          </Group>
          <ScrollArea h={240}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Сотрудник</Table.Th>
                  <Table.Th>Навык</Table.Th>
                  <Table.Th>Было → Стало</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {changes.map((c) => (
                  <Table.Tr key={c.id}>
                    <Table.Td><Text size="sm" fw={500}>{c.employee_name}</Text></Table.Td>
                    <Table.Td><Text size="sm">{c.skill_name}</Text></Table.Td>
                    <Table.Td>
                      <Group gap={6}>
                        <Badge size="sm" color="gray">{fieldLabels[c.field_name] || c.field_name}</Badge>
                        <Text size="sm">{c.old_value ?? "—"}</Text>
                        <Text size="sm" c="dimmed">→</Text>
                        <Text size="sm" fw={700} c="violet">{c.new_value ?? "—"}</Text>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </ScrollArea>
        </Card>
      )}

      {!isManager && (
        <Card padding="lg" radius="lg" ta="center">
          <Text c="dimmed">Добро пожаловать, {user?.full_name}. Перейдите в <b>Профиль</b> для самооценки.</Text>
        </Card>
      )}
    </>
  );
}
