import { useState } from "react";
import { Badge, Select } from "@mantine/core";
import client from "../api/client";
import type { Assessment } from "../types";

interface SkillLevelEditorProps {
  skillId: string;
  employeeId?: string;
  currentValue: number | null;
  mode: "self" | "manager";
  onSave: (updated: Assessment) => void;
}

const levelOptions = [
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3", label: "3" },
];

export function SkillLevelEditor({ skillId, employeeId, currentValue, mode, onSave }: SkillLevelEditorProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleChange = async (v: string | null) => {
    const numVal = v ? parseInt(v, 10) : NaN;
    if (isNaN(numVal) || numVal < 1 || numVal > 3) return;

    setSaving(true);
    try {
      const body: Record<string, unknown> = {};
      if (mode === "manager" && employeeId) {
        body.manager_level = numVal;
      } else {
        body.self_level = numVal;
      }
      const { data } = await client.put(`/assessments/${skillId}`, body, {
        params: mode === "manager" && employeeId ? { employee_id: employeeId } : undefined,
      });
      onSave(data);
      setEditing(false);
    } catch {
      // revert
    } finally {
      setSaving(false);
    }
  };

  if (editing) {
    return (
      <Select
        size="xs"
        data={levelOptions}
        value={String(currentValue ?? "")}
        onChange={handleChange}
        styles={{ input: { width: 58, textAlign: "center" } }}
        disabled={saving}
        autoFocus
        onBlur={() => setEditing(false)}
      />
    );
  }

  return (
    <Badge color="gray" variant="outline" size="lg" style={{ cursor: "pointer" }} onClick={() => setEditing(true)}>
      {currentValue ?? "—"}
    </Badge>
  );
}
