/**
 * Type definitions for AI Agent Insurance Platform
 */

import { Request, Response, NextFunction } from "express";

// Database Models
export interface Insured {
  insured_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: Date | null;
  phone_number: string | null;
  email_address: string;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  country: string;
  company_name: string | null;
  industry: string | null;
  contact_person: string | null;
  created_at: Date;
  updated_at: Date;
}

export interface Policy {
  policy_number: string;
  insured_id: string;
  policy_type: string;
  effective_date: Date;
  expiration_date: Date;
  policy_status: string;
  payment_status: string;
  annual_premium: number;
  monthly_premium: number;
  payment_method: string | null;
  broker: string | null;
  discounts_applied: string | null;
  created_at: Date;
  updated_at: Date;
}

export interface CoverageDetails {
  policy_number: string;
  coverage_limit: number;
  deductible: number;
  coverage_tier: string | null;
  optional_addons_selected: string | null;
  regulatory_addons_selected: string | null;
  business_interruption_coverage: boolean;
  cyber_extension: boolean;
  incident_response_addon: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface AIRiskProfile {
  policy_number: string;
  ai_system_type: string | null;
  deployment_stage: string | null;
  number_of_active_agents: number;
  critical_workflows_protected: boolean;
  incident_history_count: number;
  last_ai_incident_date: Date | null;
  has_high_risk_use_cases: boolean;
  regulatory_classification: string | null;
  risk_score_internal: number;
  created_at: Date;
  updated_at: Date;
}

export interface Claim {
  claim_id: string;
  policy_number: string;
  insured_id: string;
  claim_date: Date;
  claim_type: string | null;
  claim_description: string | null;
  claim_status: string;
  claim_amount: number;
  amount_paid: number;
  created_at: Date;
  updated_at: Date;
}

// Extended types with JOINs
export interface PolicyWithInsured extends Policy {
  first_name: string;
  last_name: string;
  email_address: string;
  company_name: string | null;
  industry: string | null;
}

export interface PolicyDetails extends PolicyWithInsured {
  phone_number: string | null;
  address_line1: string | null;
  city: string | null;
  state: string | null;
  postal_code: string | null;
  coverage_limit: number;
  deductible: number;
  coverage_tier: string | null;
  business_interruption_coverage: boolean;
  cyber_extension: boolean;
  incident_response_addon: boolean;
  ai_system_type: string | null;
  deployment_stage: string | null;
  number_of_active_agents: number;
  risk_score_internal: number;
  regulatory_classification: string | null;
}

export interface CustomerWithStats extends Insured {
  policy_count: number;
  total_premium: number;
}

export interface CustomerDetails {
  customer: Insured;
  policies: PolicyWithCoverage[];
}

export interface PolicyWithCoverage extends Policy {
  coverage_tier: string | null;
  coverage_limit: number;
  ai_system_type: string | null;
  risk_score_internal: number;
}

export interface ClaimWithDetails extends Claim {
  policy_type: string;
  first_name: string;
  last_name: string;
  company_name: string | null;
}

export interface ClaimDetails extends Claim {
  policy_type: string;
  policy_status: string;
  annual_premium: number;
  first_name: string;
  last_name: string;
  email_address: string;
  phone_number: string | null;
  company_name: string | null;
  coverage_limit: number;
  deductible: number;
  coverage_tier: string | null;
}

// Statistics types
export interface DashboardOverview {
  total_customers: string;
  total_policies: string;
  active_policies: string;
  total_claims: string;
  active_claims: string;
  total_premium_value: string;
}

export interface PolicyByType {
  policy_type: string;
  count: string;
  total_premium: string;
}

export interface AISystemType {
  ai_system_type: string;
  count: string;
  avg_risk_score: string;
}

export interface RecentClaim {
  claim_id: string;
  claim_date: Date;
  claim_type: string;
  claim_status: string;
  claim_amount: number;
  company_name: string | null;
  policy_type: string;
}

export interface DashboardStats {
  overview: DashboardOverview;
  policyByType: PolicyByType[];
  aiSystemTypes: AISystemType[];
  recentClaims: RecentClaim[];
}

export interface ClaimsStats {
  total_claims: string;
  active_claims: string;
  closed_claims: string;
  total_claim_amount: string;
  total_amount_paid: string;
  avg_claim_amount: string;
}

export interface RiskAnalysis {
  regulatory_classification: string;
  policy_count: string;
  avg_risk_score: string;
  avg_active_agents: string;
  high_risk_count: string;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  count?: number;
  message?: string;
  error?: string;
}

// Error types
export interface DatabaseError extends Error {
  code?: string;
  detail?: string;
}

// Middleware types
export type ErrorHandler = (
  err: DatabaseError,
  req: Request,
  res: Response,
  next: NextFunction
) => void;

export type AsyncRequestHandler = (
  req: Request,
  res: Response,
  next: NextFunction
) => Promise<void>;
