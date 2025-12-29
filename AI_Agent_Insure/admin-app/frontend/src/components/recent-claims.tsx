import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Claim {
  claim_id: string;
  claim_date: string;
  claim_type: string;
  claim_status: string;
  claim_amount: string;
  company_name: string | null;
  policy_type: string;
}

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
    default:
      return "outline";
  }
}

export function RecentClaims({ claims }: { claims: Claim[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Claim ID</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Company</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Amount</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {claims.slice(0, 10).map((claim) => (
          <TableRow key={claim.claim_id}>
            <TableCell className="font-mono text-sm">{claim.claim_id}</TableCell>
            <TableCell>{formatDate(claim.claim_date)}</TableCell>
            <TableCell>{claim.company_name || "—"}</TableCell>
            <TableCell className="text-sm">{claim.policy_type.substring(0, 30)}</TableCell>
            <TableCell className="font-medium">{formatCurrency(claim.claim_amount)}</TableCell>
            <TableCell>
              <Badge variant={getStatusColor(claim.claim_status)}>{claim.claim_status}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
