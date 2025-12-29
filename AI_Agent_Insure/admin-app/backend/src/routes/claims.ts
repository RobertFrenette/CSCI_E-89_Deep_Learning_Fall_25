/**
 * Claims routes
 */

import { Router, Request, Response, NextFunction } from "express";
import pool from "../config/database";
import {
  ClaimWithDetails,
  ClaimDetails,
  ClaimsStats,
  ApiResponse,
} from "../types";

const router = Router();

/**
 * GET /api/claims
 * Get all claims with policy and customer information
 */
router.get(
  "/",
  async (
    req: Request,
    res: Response<ApiResponse<ClaimWithDetails[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { status } = req.query;

      let query = `
      SELECT 
        c.*,
        p.policy_type,
        i.first_name,
        i.last_name,
        i.company_name
      FROM claims_history c
      JOIN policies p ON c.policy_number = p.policy_number
      JOIN insureds i ON c.insured_id = i.insured_id
    `;

      const params: string[] = [];

      if (status) {
        query += ` WHERE c.claim_status = $1`;
        params.push(status as string);
      }

      query += ` ORDER BY c.claim_date DESC`;

      const result = await pool.query<ClaimWithDetails>(query, params);

      res.json({
        success: true,
        count: result.rows.length,
        data: result.rows,
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/claims/:claimId
 * Get a specific claim with full details
 */
router.get(
  "/:claimId",
  async (
    req: Request,
    res: Response<ApiResponse<ClaimDetails>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { claimId } = req.params;

      const query = `
      SELECT 
        c.*,
        p.policy_type,
        p.policy_status,
        p.annual_premium,
        i.first_name,
        i.last_name,
        i.email_address,
        i.phone_number,
        i.company_name,
        cd.coverage_limit,
        cd.deductible,
        cd.coverage_tier
      FROM claims_history c
      JOIN policies p ON c.policy_number = p.policy_number
      JOIN insureds i ON c.insured_id = i.insured_id
      LEFT JOIN coverage_details cd ON p.policy_number = cd.policy_number
      WHERE c.claim_id = $1
    `;

      const result = await pool.query<ClaimDetails>(query, [claimId]);

      if (result.rows.length === 0) {
        res.status(404).json({
          success: false,
          message: "Claim not found",
        });
        return;
      }

      res.json({
        success: true,
        data: result.rows[0],
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/claims/stats/summary
 * Get claims statistics summary
 */
router.get(
  "/stats/summary",
  async (
    _req: Request,
    res: Response<ApiResponse<ClaimsStats>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const query = `
      SELECT 
        COUNT(*) as total_claims,
        COUNT(CASE WHEN claim_status = 'Active' THEN 1 END) as active_claims,
        COUNT(CASE WHEN claim_status = 'Closed' THEN 1 END) as closed_claims,
        COALESCE(SUM(claim_amount), 0) as total_claim_amount,
        COALESCE(SUM(amount_paid), 0) as total_amount_paid,
        COALESCE(AVG(claim_amount), 0) as avg_claim_amount
      FROM claims_history
    `;

      const result = await pool.query<ClaimsStats>(query);

      res.json({
        success: true,
        data: result.rows[0],
      });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
