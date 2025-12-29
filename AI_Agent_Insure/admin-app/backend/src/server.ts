/**
 * Admin Backend Server
 * Express API for AI Agent Insurance Platform - Admin Dashboard
 */

import express, { Request, Response, Application } from "express";
import cors from "cors";
import morgan from "morgan";
import helmet from "helmet";
import dotenv from "dotenv";
import swaggerUi from "swagger-ui-express";

import errorHandler from "./middleware/errorHandler";
import policiesRoutes from "./routes/policies";
import customersRoutes from "./routes/customers";
import claimsRoutes from "./routes/claims";
import statsRoutes from "./routes/stats";
import dataRoutes from "./routes/data";
import { swaggerSpec } from "./config/swagger";
import pool from "./config/database";

dotenv.config();

const app: Application = express();
const PORT = process.env.ADMIN_BACKEND_PORT || 3001;

// Middleware
app.use(helmet()); // Security headers
app.use(cors()); // Enable CORS
app.use(morgan("dev")); // Logging
app.use(express.json()); // Parse JSON bodies
app.use(express.urlencoded({ extended: true })); // Parse URL-encoded bodies

/**
 * @openapi
 * /health:
 *   get:
 *     tags:
 *       - Health
 *     summary: Health check endpoint
 *     description: Returns the health status of the API server
 *     responses:
 *       200:
 *         description: Server is healthy
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 success:
 *                   type: boolean
 *                   example: true
 *                 message:
 *                   type: string
 *                   example: Admin backend is running
 *                 timestamp:
 *                   type: string
 *                   format: date-time
 */
// Liveness check endpoint (service is running)
app.get("/health", (_req: Request, res: Response) => {
  res.json({
    success: true,
    message: "Admin backend is running",
    timestamp: new Date().toISOString(),
  });
});

// Readiness check endpoint (service can serve requests - DB connected and has data)
app.get("/health/ready", async (_req: Request, res: Response): Promise<void> => {
  try {
    // Check database connection
    const result = await pool.query("SELECT COUNT(*) as count FROM policies");
    const policyCount = parseInt(result.rows[0].count);
    
    if (policyCount === 0) {
      res.status(503).json({
        success: false,
        message: "Service not ready - database has no data",
        database: "connected",
        data_loaded: false,
      });
      return;
    }
    
    res.json({
      success: true,
      message: "Admin backend is ready",
      database: "connected",
      data_loaded: true,
      policy_count: policyCount,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    res.status(503).json({
      success: false,
      message: "Service not ready - database connection failed",
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

// API Documentation
app.use(
  "/docs",
  swaggerUi.serve,
  swaggerUi.setup(swaggerSpec, {
    customCss: ".swagger-ui .topbar { display: none }",
    customSiteTitle: "Admin API Documentation",
  })
);

// Swagger JSON endpoint
app.get("/docs.json", (_req: Request, res: Response) => {
  res.setHeader("Content-Type", "application/json");
  res.send(swaggerSpec);
});

// API routes
app.use("/api/policies", policiesRoutes);
app.use("/api/customers", customersRoutes);
app.use("/api/claims", claimsRoutes);
app.use("/api/stats", statsRoutes);
app.use("/api/data", dataRoutes);

// 404 handler
app.use((_req: Request, res: Response) => {
  res.status(404).json({
    success: false,
    message: "Route not found",
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════╗
║   Admin Backend API - AI Agent Insurance Platform         ║
╚════════════════════════════════════════════════════════════╝
    
✓ Server running on port ${PORT}
✓ Environment: ${process.env.NODE_ENV || "development"}
✓ Health check: http://localhost:${PORT}/health
✓ API Documentation: http://localhost:${PORT}/docs
✓ OpenAPI Spec: http://localhost:${PORT}/docs.json
    
API Endpoints:
  GET  /api/policies              - List all policies
  GET  /api/policies/:id          - Get policy details
  GET  /api/policies/:id/claims   - Get policy claims
  
  GET  /api/customers             - List all customers
  GET  /api/customers/:id         - Get customer details
  GET  /api/customers/:id/claims  - Get customer claims
  
  GET  /api/claims                - List all claims
  GET  /api/claims/:id            - Get claim details
  GET  /api/claims/stats/summary  - Get claims statistics
  
  GET  /api/stats/dashboard       - Get dashboard stats
  GET  /api/stats/risk-analysis   - Get risk analysis
  
  POST /api/data/refresh          - Refresh PostgreSQL data from CSV files
  
Press Ctrl+C to stop
    `);
  });
}

export default app;
