import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SidebarTrigger } from "@/components/ui/sidebar";

function formatCurrency(value: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getStatusColor(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status.toLowerCase()) {
    case "active":
      return "default";
    case "expired":
      return "secondary";
    case "cancelled":
      return "destructive";
    default:
      return "outline";
  }
}

export default async function PoliciesPage() {
  const response = await api.getPolicies();
  const policies = response.data || [];

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">Policies</h1>
          <p className="text-muted-foreground">
            Manage all insurance policies ({response.count || 0} total)
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Policies</CardTitle>
          <CardDescription>View and manage insurance policies</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Policy Number</TableHead>
                <TableHead>Policy Type</TableHead>
                <TableHead>Insured</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Effective Date</TableHead>
                <TableHead>Annual Premium</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {policies.map((policy) => (
                <TableRow key={policy.policy_number}>
                  <TableCell className="font-mono text-sm">{policy.policy_number}</TableCell>
                  <TableCell className="max-w-xs">
                    <div className="truncate" title={policy.policy_type}>
                      {policy.policy_type}
                    </div>
                  </TableCell>
                  <TableCell>
                    {policy.first_name} {policy.last_name}
                  </TableCell>
                  <TableCell>{policy.company_name || "—"}</TableCell>
                  <TableCell>{formatDate(policy.effective_date)}</TableCell>
                  <TableCell className="font-medium">
                    {formatCurrency(policy.annual_premium)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusColor(policy.policy_status)}>
                      {policy.policy_status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
