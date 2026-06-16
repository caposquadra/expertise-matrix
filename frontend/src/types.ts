export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  grade: string | null;
  team_id: string | null;
  is_active: boolean;
}

export interface Employee {
  id: string;
  email: string;
  full_name: string;
  role: string;
  grade: string | null;
  is_active: boolean;
  team_id?: string | null;
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  description?: string | null;
  weight: number;
  sort_order?: number;
  is_active?: boolean;
}

export interface Assessment {
  id: string;
  employee_id?: string;
  skill_id: string;
  self_level: number | null;
  manager_level: number | null;
  target_level: number | null;
}

export interface Cell {
  id: string;
  employee_id: string;
  skill_id: string;
  self_level: number | null;
  manager_level: number | null;
  target_level: number | null;
}

export interface Score {
  current_score: number;
  target_score: number | null;
  total_weight: number;
  assessed_weight: number;
}

export interface Goal {
  id: string;
  skill_id: string;
  current_level: number;
  target_level: number;
  status: string;
  due_date: string | null;
  notes: string | null;
}

export interface IprPlan {
  id: string;
  employee_id: string;
  title: string;
  description: string | null;
  status: string;
  goals: Goal[];
}

export interface ReviewAssessment {
  id: string;
  review_cycle_id: string;
  skill_id: string;
  self_level: number | null;
  self_comment: string | null;
  manager_level: number | null;
  expert_level: number | null;
}

export interface ReviewCycle {
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

export interface Team {
  id: string;
  name: string;
  description: string | null;
  employee_count: number;
}

export interface Summary {
  total_employees: number;
  grade_distribution: { grade: string; count: number }[];
  avg_self_level: number | null;
  avg_manager_level: number | null;
  skill_coverage: {
    skill_name: string;
    category: string;
    employees_with_assessment: number;
    total_employees: number;
    coverage_percent: number;
  }[];
}

export interface Change {
  id: string;
  field_name: string;
  old_value: number | null;
  new_value: number | null;
  employee_name: string | null;
  skill_name: string | null;
  changed_at: string;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface EmployeeCycleInfo {
  employee_name: string;
  employee_id: string;
  cycle_id?: string | null;
  status?: string | null;
  days_in_status?: number;
}

export interface ReviewCyclesSummary {
  status_counts: StatusCount[];
  total_active: number;
  employees_without_self_assessment: EmployeeCycleInfo[];
  status_employees: Record<string, EmployeeCycleInfo[]>;
}

export interface WeakestSkill {
  skill_name: string;
  category: string;
  avg_manager_level: number;
  assessment_count: number;
}

export interface RecentDecision {
  employee_name: string;
  employee_id: string;
  decision: string;
  current_grade: string | null;
  target_grade: string | null;
  completed_at: string;
}

export interface PromotionReady {
  employee_name: string;
  employee_id: string;
  current_grade: string | null;
  target_grade: string | null;
  total_score: number;
  target_score: number | null;
  avg_self_level: number;
  avg_manager_level: number;
}

export interface HistoryEntry {
  id: string;
  field_name: string;
  old_value: number | null;
  new_value: number | null;
  changed_at: string;
}

export interface EmployeeInfo {
  id: string;
  full_name: string;
  email: string;
}

export interface LevelInfo {
  level: number;
  title: string;
  what: string;
}

export interface EmployeeProfile {
  id: string;
  employee_id: string;
  organization: string;
  city: string;
  department: string;
  subdivision: string;
  position: string;
  specialization: string;
  experience: number;
  education: number;
  task_complexity: number;
  autonomy: number;
  communication: number;
  control: number;
  mentoring: number;
  responsibility: number;
  technical_competencies: number;
  notes: string | null;
  grade: number;
}
