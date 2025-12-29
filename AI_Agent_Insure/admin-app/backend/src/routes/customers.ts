/**
 * Customer (Insureds) routes
 */

import { Router, Request, Response, NextFunction } from "express";
import pool from "../config/database";
import {
  CustomerWithStats,
  CustomerDetails,
  PolicyWithCoverage,
  ApiResponse,
} from "../types";

const router = Router();

/**
 * GET /api/customers
 * Get all customers with policy counts
 */
router.get(
  "/",
  async (
    _req: Request,
    res: Response<ApiResponse<CustomerWithStats[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const query = `
      SELECT 
        i.*,
        COUNT(p.policy_number) as policy_count,
        COALESCE(SUM(p.annual_premium), 0) as total_premium
      FROM insureds i
      LEFT JOIN policies p ON i.insured_id = p.insured_id
      GROUP BY i.insured_id
      ORDER BY i.last_name, i.first_name
    `;

      const result = await pool.query<CustomerWithStats>(query);

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
 * GET /api/customers/:insuredId
 * Get a specific customer with all details
 */
router.get(
  "/:insuredId",
  async (
    req: Request,
    res: Response<ApiResponse<CustomerDetails>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { insuredId } = req.params;

      const customerQuery = `
      SELECT *
      FROM insureds
      WHERE insured_id = $1
    `;

      const customerResult = await pool.query(customerQuery, [insuredId]);

      if (customerResult.rows.length === 0) {
        res.status(404).json({
          success: false,
          message: "Customer not found",
        });
        return;
      }

      // Get customer's policies
      const policiesQuery = `
      SELECT 
        p.*,
        c.coverage_tier,
        c.coverage_limit,
        a.ai_system_type,
        a.risk_score_internal
      FROM policies p
      LEFT JOIN coverage_details c ON p.policy_number = c.policy_number
      LEFT JOIN ai_risk_profile a ON p.policy_number = a.policy_number
      WHERE p.insured_id = $1
      ORDER BY p.effective_date DESC
    `;

      const policiesResult = await pool.query<PolicyWithCoverage>(
        policiesQuery,
        [insuredId]
      );

      res.json({
        success: true,
        data: {
          customer: customerResult.rows[0],
          policies: policiesResult.rows,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/customers/:insuredId/claims
 * Get all claims for a specific customer
 */
router.get(
  "/:insuredId/claims",
  async (
    req: Request,
    res: Response<ApiResponse<any[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { insuredId } = req.params;

      const query = `
      SELECT 
        c.*,
        p.policy_type
      FROM claims_history c
      JOIN policies p ON c.policy_number = p.policy_number
      WHERE c.insured_id = $1
      ORDER BY c.claim_date DESC
    `;

      const result = await pool.query(query, [insuredId]);

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

export default router;
