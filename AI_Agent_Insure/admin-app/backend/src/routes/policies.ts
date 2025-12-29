/**
 * Policy routes
 */

import { Router, Request, Response, NextFunction } from "express";
import pool from "../config/database";
import { PolicyWithInsured, PolicyDetails, Claim, ApiResponse } from "../types";

const router = Router();

/**
 * @openapi
 * /api/policies:
 *   get:
 *     tags:
 *       - Policies
 *     summary: List all policies
 *     description: Retrieve all insurance policies with associated insured information
 *     responses:
 *       200:
 *         description: List of policies with insured details
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 count:
 *                   type: number
 *                 data:
 *                   type: array
 *                   items:
 *                     allOf:
 *                       - $ref: '#/components/schemas/Policy'
 *                       - type: object
 *                         properties:
 *                           insured_id:
 *                             type: string
 *                           first_name:
 *                             type: string
 *                           last_name:
 *                             type: string
 *                           email_address:
 *                             type: string
 *                           company_name:
 *                             type: string
 *                           industry:
 *                             type: string
 *       500:
 *         $ref: '#/components/responses/ServerError'
 */
router.get(
  "/",
  async (
    _req: Request,
    res: Response<ApiResponse<PolicyWithInsured[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const query = `
      SELECT 
        p.policy_number,
        p.policy_type,
        p.effective_date,
        p.expiration_date,
        p.policy_status,
        p.payment_status,
        p.annual_premium,
        p.monthly_premium,
        p.payment_method,
        p.broker,
        i.insured_id,
        i.first_name,
        i.last_name,
        i.email_address,
        i.company_name,
        i.industry
      FROM policies p
      JOIN insureds i ON p.insured_id = i.insured_id
      ORDER BY p.effective_date DESC
    `;

      const result = await pool.query<PolicyWithInsured>(query);

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
 * @openapi
 * /api/policies/{policyNumber}:
 *   get:
 *     tags:
 *       - Policies
 *     summary: Get policy details
 *     description: Retrieve complete details for a specific policy including insured info, coverage, and risk profile
 *     parameters:
 *       - in: path
 *         name: policyNumber
 *         required: true
 *         schema:
 *           type: string
 *         description: The policy number
 *     responses:
 *       200:
 *         description: Policy details
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 data:
 *                   allOf:
 *                     - $ref: '#/components/schemas/Policy'
 *                     - $ref: '#/components/schemas/Insured'
 *                     - $ref: '#/components/schemas/CoverageDetails'
 *                     - $ref: '#/components/schemas/AIRiskProfile'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/ServerError'
 */
router.get(
  "/:policyNumber",
  async (
    req: Request,
    res: Response<ApiResponse<PolicyDetails>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { policyNumber } = req.params;

      const query = `
      SELECT 
        p.*,
        i.first_name,
        i.last_name,
        i.email_address,
        i.company_name,
        i.industry,
        i.phone_number,
        i.address_line1,
        i.city,
        i.state,
        i.postal_code,
        c.coverage_limit,
        c.deductible,
        c.coverage_tier,
        c.business_interruption_coverage,
        c.cyber_extension,
        c.incident_response_addon,
        a.ai_system_type,
        a.deployment_stage,
        a.number_of_active_agents,
        a.risk_score_internal,
        a.regulatory_classification
      FROM policies p
      JOIN insureds i ON p.insured_id = i.insured_id
      LEFT JOIN coverage_details c ON p.policy_number = c.policy_number
      LEFT JOIN ai_risk_profile a ON p.policy_number = a.policy_number
      WHERE p.policy_number = $1
    `;

      const result = await pool.query<PolicyDetails>(query, [policyNumber]);

      if (result.rows.length === 0) {
        res.status(404).json({
          success: false,
          message: "Policy not found",
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
 * @openapi
 * /api/policies/{policyNumber}/claims:
 *   get:
 *     tags:
 *       - Policies
 *     summary: Get policy claims
 *     description: Retrieve all claims associated with a specific policy
 *     parameters:
 *       - in: path
 *         name: policyNumber
 *         required: true
 *         schema:
 *           type: string
 *         description: The policy number
 *     responses:
 *       200:
 *         description: List of claims for the policy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 count:
 *                   type: number
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/Claim'
 *       500:
 *         $ref: '#/components/responses/ServerError'
 */
router.get(
  "/:policyNumber/claims",
  async (
    req: Request,
    res: Response<ApiResponse<Claim[]>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      const { policyNumber } = req.params;

      const query = `
      SELECT *
      FROM claims_history
      WHERE policy_number = $1
      ORDER BY claim_date DESC
    `;

      const result = await pool.query<Claim>(query, [policyNumber]);

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
