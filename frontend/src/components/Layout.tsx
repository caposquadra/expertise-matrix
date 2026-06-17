import { Outlet, useNavigate, useLocation } from "react-router-dom";
import {
  AppShell,
  Burger,
  Group,
  Text,
  UnstyledButton,
  Avatar,
  Menu,
  Flex,
  Divider,
  useMantineTheme,
  Box,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import {
  IconDashboard,
  IconMatrix,
  IconUser,
  IconFileReport,
  IconSettings,
  IconLogout,
  IconChevronDown,
  IconLayoutGrid,
  IconClipboardCheck,
} from "@tabler/icons-react";
import { useAuth } from "../store/auth";
import { translateRole } from "../constants";

const navItems = [
  { label: "Дашборд", icon: IconDashboard, path: "/", roles: ["admin", "manager"] },
  { label: "Матрица", icon: IconMatrix, path: "/matrix", roles: ["admin", "manager"] },
  { label: "Профиль", icon: IconUser, path: "/profile", roles: ["admin", "manager", "employee", "expert"] },
  { label: "Оценка", icon: IconClipboardCheck, path: "/reviews", roles: ["admin", "manager", "employee", "expert"] },
  { label: "ИПР", icon: IconFileReport, path: "/ipr", roles: ["admin", "manager", "employee"] },
  { label: "Администрирование", icon: IconSettings, path: "/admin", roles: ["admin"] },
];

export function Layout() {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useMantineTheme();
  const { user, logout } = useAuth();

  return (
    <AppShell
      header={{ height: 64 }}
      navbar={{ width: 240, breakpoint: "sm", collapsed: { mobile: !opened } }}
      padding="lg"
    >
      <AppShell.Header style={{ borderBottom: `1px solid ${theme.colors.gray[2]}`, background: "white" }}>
        <Group h="100%" px="lg" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <IconLayoutGrid size={24} color={theme.colors.indigo[6]} />
            <Text fw={800} size="lg" c={theme.colors.indigo[7]}>
              Матрица компетенций департамента тестирования
            </Text>
          </Group>

          <Menu shadow="lg" width={200} radius="md">
            <Menu.Target>
              <UnstyledButton>
                <Group gap={10}>
                  <Avatar color="indigo" radius="xl" size="sm">
                    {user?.full_name?.charAt(0) || "U"}
                  </Avatar>
                  <Box visibleFrom="sm">
                    <Text size="sm" fw={600}>{user?.full_name}</Text>
                    <Text size="xs" c="dimmed">{translateRole(user?.role)}</Text>
                  </Box>
                  <IconChevronDown size={14} />
                </Group>
              </UnstyledButton>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item color="red" leftSection={<IconLogout size={16} />} onClick={() => { logout(); navigate("/login"); }}>
                Выйти
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm" style={{ background: theme.colors.gray[0], borderRight: `1px solid ${theme.colors.gray[2]}` }}>
        <Flex direction="column" gap={4}>
          {navItems
            .filter((item) => item.roles.includes(user?.role || ""))
            .map((item) => {
              const active = location.pathname === item.path;
              return (
                <UnstyledButton
                  key={item.path}
                  onClick={() => { navigate(item.path); toggle(); }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "12px 14px",
                    borderRadius: theme.radius.md,
                    background: active ? theme.colors.indigo[1] : "transparent",
                    color: active ? theme.colors.indigo[8] : theme.colors.gray[7],
                    fontWeight: active ? 600 : 400,
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    if (!active) e.currentTarget.style.background = theme.colors.gray[2];
                  }}
                  onMouseLeave={(e) => {
                    if (!active) e.currentTarget.style.background = "transparent";
                  }}
                >
                  <item.icon size={20} stroke={active ? 2.5 : 1.8} />
                  <Text size="sm">{item.label}</Text>
                </UnstyledButton>
              );
            })}
        </Flex>
        <Divider my="md" />
        <Text size="xs" c="dimmed" ta="center">v1.0</Text>
      </AppShell.Navbar>

      <AppShell.Main style={{ background: theme.colors.gray[0] }}>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
