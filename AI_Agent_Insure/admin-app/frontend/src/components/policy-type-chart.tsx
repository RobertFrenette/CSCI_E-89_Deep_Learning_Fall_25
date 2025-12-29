"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Cell } from "recharts";

interface PolicyTypeData {
  policy_type: string;
  count: string;
  total_premium: string;
}

// Chart colors - using actual color values that work with Recharts
const CHART_COLORS = [
  "#3b82f6", // Blue
  "#10b981", // Green
  "#f59e0b", // Orange
  "#8b5cf6", // Purple
  "#ef4444", // Red
  "#06b6d4", // Cyan
  "#f97316", // Orange-red
];

export function PolicyTypeChart({ data }: { data: PolicyTypeData[] }) {
  const chartData = data.map((item) => ({
    name: item.policy_type.replace(" Insurance", "").substring(0, 20),
    count: Number(item.count),
    premium: Number(item.total_premium),
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis
          dataKey="name"
          fontSize={12}
          angle={-45}
          textAnchor="end"
          height={100}
          stroke="hsl(var(--muted-foreground))"
        />
        <YAxis fontSize={12} stroke="hsl(var(--muted-foreground))" />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
