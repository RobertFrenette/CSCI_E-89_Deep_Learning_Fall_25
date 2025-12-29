/**
 * Data management routes (CSV refresh, etc.)
 */

import { Router, Request, Response, NextFunction } from "express";
import { exec } from "child_process";
import { promisify } from "util";
import { ApiResponse } from "../types";
import path from "path";

const execAsync = promisify(exec);
const router = Router();

/**
 * @openapi
 * /api/data/refresh:
 *   post:
 *     tags:
 *       - Data
 *     summary: Refresh PostgreSQL data from CSV files
 *     description: Reloads all CSV data from the data/insured_data directory into PostgreSQL
 *     responses:
 *       200:
 *         description: Data refresh initiated successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                 message:
 *                   type: string
 *       500:
 *         $ref: '#/components/responses/ServerError'
 */
router.post(
  "/refresh",
  async (
    _req: Request,
    res: Response<ApiResponse<{ message: string }>>,
    next: NextFunction
  ): Promise<void> => {
    try {
      // Path to the load_data.py script
      // From admin-backend container, we need to access the database-init directory
      // The script is at the project root level
      const scriptPath = path.join(
        __dirname,
        "../../../../database-init/load_data.py"
      );

      // Execute the Python script
      const { stdout, stderr } = await execAsync(
        `python3 ${scriptPath}`,
        {
          env: {
            ...process.env,
            POSTGRES_HOST: process.env.POSTGRES_HOST || "postgres",
            POSTGRES_PORT: process.env.POSTGRES_PORT || "5432",
            POSTGRES_DB: process.env.POSTGRES_DB || "insurance_db",
            POSTGRES_USER: process.env.POSTGRES_USER || "insure_admin",
            POSTGRES_PASSWORD:
              process.env.POSTGRES_PASSWORD || "insure_secure_pass_2025",
          },
          maxBuffer: 10 * 1024 * 1024, // 10MB buffer for output
        }
      );

      if (stderr && !stderr.includes("Warning")) {
        // Only treat as error if it's not just a warning
        console.error("Data refresh stderr:", stderr);
      }

      console.log("Data refresh stdout:", stdout);

      res.json({
        success: true,
        message: "Data refresh completed successfully",
        data: {
          message: "PostgreSQL data has been refreshed from CSV files",
        },
      });
    } catch (error: any) {
      console.error("Data refresh error:", error);
      next(error);
    }
  }
);

export default router;

