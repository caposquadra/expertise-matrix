export const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  manager: "Руководитель",
  employee: "Сотрудник",
  expert: "Эксперт",
};

export const GRADE_LABELS: Record<string, string> = {
  junior: "Младший тестировщик",
  middle: "Тестировщик",
  senior: "Старший тестировщик",
};

export function translateRole(role: string | null | undefined): string {
  return role ? ROLE_LABELS[role] || role : "—";
}

export function translateGrade(grade: string | null | undefined): string {
  return grade ? GRADE_LABELS[grade] || grade : "—";
}
