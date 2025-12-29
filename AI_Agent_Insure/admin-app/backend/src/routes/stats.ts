/**
 * Statistics and dashboard routes
 */

import { Router, Request, Response, NextFunction } from "express";
import pool from "../config/database";
import { DashboardStats, RiskAnalysis, ApiResponse } from "../types";

const router = Router();

/**
 * @openapi
 * /api/stats/dashboard:
 *   get:
 *     tags:
 *       - Stats
 *     summary: Get dashboard statistics
 *     description: Retrieve comprehensive dashboard statistics including overview, policy breakdown, AI system types, and recent claims
 *     responses:
 *       200:
 *         description: Dashboard statistics
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   type: object
 *                   properties:
 *                     overview:
 *                       type: object
 *                       properties:
 *                         total_customers:
 *                           type: string
 *                         total_policies:
 *                           type: string
 *                         active_policies:
 *                           type: string
 *                         total_claims:
 *                           type: string
 *                         active_claims:
 *                           type: string
 *                         total_premium_value:
 *                           type: string
 *                     policyByType:
 *                       type: array
 *                       items:
 *                         type: object
 *                         properties:
 *                           policy_type:
 *                             type: string
 *                           count:
 *                             type: string
 *                           total_premium:
 *                             type: string
 *                     aiSystemTypes:
 *                       type: array
 *                       items:
 *                         type: object
 *                         properties:
 *                           ai_system_type:
 *                             type: string
 *                           count:
 *                             type: string
 *                           avg_risk_score:
 *                             type: string
 *                     recentClaims:
 *                       type: array
 *                       items:
 *                         $ref: '#/components/schemas/Claim'
 *       500:
 *         $ref: '#/components/responses/ServerError'
 */
router.get(
  "/dashboard",
  async (
    _req: Request,
    res: Response<ApiResponse<DashboardStats>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      // Get overall stats
      const overallQuery = `
      SELECT 
        (SELECT COUNT(*) FROM insureds) as total_customers,
        (SELECT COUNT(*) FROM policies) as total_policies,
        (SELECT COUNT(*) FROM policies WHERE policy_status = 'Active') as active_policies,
        (SELECT COUNT(*) FROM claims_history) as total_claims,
        (SELECT COUNT(*) FROM claims_history WHERE claim_status = 'Active') as active_claims,
        (SELECT COALESCE(SUM(annual_premium), 0) FROM policies WHERE policy_status = 'Active') as total_premium_value
    `;

      const overallResult = await pool.query(overallQuery);

      // Get policy type breakdown
      const policyTypeQuery = `
      SELECT 
        policy_type,
        COUNT(*) as count,
        COALESCE(SUM(annual_premium), 0) as total_premium
      FROM policies
      WHERE policy_status = 'Active'
      GROUP BY policy_type
      ORDER BY count DESC
    `;

      const policyTypeResult = await pool.query(policyTypeQuery);

      // Get AI system type breakdown
      const aiTypeQuery = `
      SELECT 
        ai_system_type,
        COUNT(*) as count,
        AVG(risk_score_internal) as avg_risk_score
      FROM ai_risk_profile
      GROUP BY ai_system_type
      ORDER BY count DESC
    `;

      const aiTypeResult = await pool.query(aiTypeQuery);

      // Get recent claims
      const recentClaimsQuery = `
      SELECT 
        c.claim_id,
        c.claim_date,
        c.claim_type,
        c.claim_status,
        c.claim_amount,
        i.company_name,
        p.policy_type
      FROM claims_history c
      JOIN insureds i ON c.insured_id = i.insured_id
      JOIN policies p ON c.policy_number = p.policy_number
      ORDER BY c.claim_date DESC
      LIMIT 10
    `;

      const recentClaimsResult = await pool.query(recentClaimsQuery);

      res.json({
        success: true,
        data: {
          overview: overallResult.rows[0],
          policyByType: policyTypeResult.rows,
          aiSystemTypes: aiTypeResult.rows,
          recentClaims: recentClaimsResult.rows,
        },
      });
    } catch (error) {
      next(error);
    }
  }
);

/**
 * GET /api/stats/risk-analysis
 * Get risk analysis data
 */
router.get(
  "/risk-analysis",
  async (
    _req: Request,
    res: Response<ApiResponse<RiskAnalysis[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const query = `
      SELECT 
        a.regulatory_classification,
        COUNT(*) as policy_count,
        AVG(a.risk_score_internal) as avg_risk_score,
        AVG(a.number_of_active_agents) as avg_active_agents,
        COUNT(CASE WHEN a.has_high_risk_use_cases THEN 1 END) as high_risk_count
      FROM ai_risk_profile a
      JOIN policies p ON a.policy_number = p.policy_number
      WHERE p.policy_status = 'Active'
      GROUP BY a.regulatory_classification
      ORDER BY policy_count DESC
    `;

      const result = await pool.query<RiskAnalysis>(query);

      res.json({
        success: true,
        data: result.rows,
      });
    } catch (error) {
      next(error);
    }
  }
);

export default router;
