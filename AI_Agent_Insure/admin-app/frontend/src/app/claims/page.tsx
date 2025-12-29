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
import { AlertCircle, CheckCircle, Clock } from "lucide-react";

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
    case "open":
    case "active":
      return "destructive";
    case "closed":
      return "secondary";
    case "pending":
      return "outline";
    default:
      return "default";
  }
}

export default async function ClaimsPage() {
  const [claimsResponse, statsResponse] = await Promise.all([
    api.getClaims(),
    api.getClaimsStats(),
  ]);

  const claims = claimsResponse.data || [];
  const stats = statsResponse.data;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">Claims</h1>
          <p className="text-muted-foreground">
            Insurance claims management ({claimsResponse.count || 0} total)
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_claims}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Claims</CardTitle>
              <Clock className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_claims}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Closed Claims</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.closed_claims}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Amount</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.total_claim_amount)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Claims Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Claims</CardTitle>
          <CardDescription>View and manage insurance claims</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Claim ID</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Policy Number</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {claims.map((claim) => (
                <TableRow key={claim.claim_id}>
                  <TableCell className="font-mono text-sm">{claim.claim_id}</TableCell>
                  <TableCell>{formatDate(claim.claim_date)}</TableCell>
                  <TableCell className="font-mono text-sm">{claim.policy_number}</TableCell>
                  <TableCell>{claim.company_name || "—"}</TableCell>
                  <TableCell className="max-w-xs">
                    <div className="truncate text-sm" title={claim.policy_type}>
                      {claim.policy_type}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">{formatCurrency(claim.claim_amount)}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusColor(claim.claim_status)}>{claim.claim_status}</Badge>
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
