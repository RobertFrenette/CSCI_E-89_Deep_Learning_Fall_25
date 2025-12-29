/**
 * Swagger/OpenAPI Configuration
 * API documentation for Admin Backend
 */

import swaggerJsdoc from "swagger-jsdoc";

const options: swaggerJsdoc.Options = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "AI Agent Insurance Platform - Admin API",
      version: "1.0.0",
      description:
        "REST API for the Admin Dashboard of the AI Agent Insurance Platform. Provides endpoints for managing policies, customers, claims, and analytics.",
      contact: {
        name: "API Support",
        email: "support@aiagentinsure.com",
      },
    },
    servers: [
      {
        url: "http://localhost:3001",
        description: "Development server",
      },
      {
        url: "http://localhost:3001/api",
        description: "API base path",
      },
    ],
    tags: [
      {
        name: "Health",
        description: "Health check endpoints",
      },
      {
        name: "Policies",
        description: "Insurance policy management",
      },
      {
        name: "Customers",
        description: "Customer/insured management",
      },
      {
        name: "Claims",
        description: "Claims management and statistics",
      },
      {
        name: "Stats",
        description: "Dashboard statistics and analytics",
      },
    ],
    components: {
      schemas: {
        Insured: {
          type: "object",
          properties: {
            insured_id: { type: "string", example: "INS001" },
            first_name: { type: "string", example: "John" },
            last_name: { type: "string", example: "Doe" },
            email: { type: "string", example: "john.doe@example.com" },
            phone: { type: "string", example: "+1-555-0100" },
            company_name: {
              type: "string",
              nullable: true,
              example: "TechCorp",
            },
            date_of_birth: {
              type: "string",
              format: "date",
              example: "1985-05-15",
            },
            address: { type: "string", example: "123 Main St, City, ST 12345" },
          },
        },
        Policy: {
          type: "object",
          properties: {
            policy_number: { type: "string", example: "POL001" },
            insured_id: { type: "string", example: "INS001" },
            policy_type: {
              type: "string",
              example: "Agentic AI Liability Insurance",
            },
            coverage_amount: { type: "number", example: 1000000 },
            premium_amount: { type: "number", example: 12000 },
            start_date: {
              type: "string",
              format: "date",
              example: "2024-01-01",
            },
            end_date: { type: "string", format: "date", example: "2025-01-01" },
            status: { type: "string", example: "Active" },
          },
        },
        CoverageDetails: {
          type: "object",
          properties: {
            coverage_id: { type: "string", example: "COV001" },
            policy_number: { type: "string", example: "POL001" },
            coverage_type: { type: "string", example: "Liability" },
            coverage_limit: { type: "number", example: 500000 },
            deductible: { type: "number", example: 5000 },
          },
        },
        AIRiskProfile: {
          type: "object",
          properties: {
            risk_profile_id: { type: "string", example: "RISK001" },
            policy_number: { type: "string", example: "POL001" },
            ai_system_type: { type: "string", example: "RAG" },
            deployment_scale: { type: "string", example: "Enterprise" },
            data_sensitivity: { type: "string", example: "High" },
            regulatory_classification: { type: "string", example: "High-Risk" },
            risk_score: { type: "number", example: 75 },
          },
        },
        Claim: {
          type: "object",
          properties: {
            claim_id: { type: "string", example: "CLM001" },
            policy_number: { type: "string", example: "POL001" },
            claim_date: {
              type: "string",
              format: "date",
              example: "2024-03-15",
            },
            claim_type: { type: "string", example: "AI Incident" },
            claim_amount: { type: "number", example: 50000 },
            claim_status: { type: "string", example: "Open" },
            description: {
              type: "string",
              nullable: true,
              example: "Model hallucination incident",
            },
          },
        },
        ApiResponse: {
          type: "object",
          properties: {
            success: { type: "boolean", example: true },
            data: { type: "object" },
            message: { type: "string", example: "Success" },
          },
        },
        ErrorResponse: {
          type: "object",
          properties: {
            success: { type: "boolean", example: false },
            message: { type: "string", example: "Error message" },
            error: { type: "string", example: "Detailed error information" },
          },
        },
      },
      responses: {
        NotFound: {
          description: "Resource not found",
          content: {
            "application/json": {
              schema: { $ref: "#/components/schemas/ErrorResponse" },
            },
          },
        },
        ServerError: {
          description: "Internal server error",
          content: {
            "application/json": {
              schema: { $ref: "#/components/schemas/ErrorResponse" },
            },
          },
        },
      },
    },
  },
  apis: [
    "./src/routes/*.ts",
    "./src/server.ts",
    "./dist/routes/*.js",
    "./dist/server.js",
  ],
};

export const swaggerSpec = swaggerJsdoc(options);
