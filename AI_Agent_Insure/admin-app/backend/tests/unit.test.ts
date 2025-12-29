/**
 * Unit Tests with Mocked Database
 * These tests run during Docker build without requiring a real database
 */

import request from "supertest";

// Mock the database pool before importing the app
jest.mock("../src/config/database", () => {
  return {
    __esModule: true,
    default: {
      query: jest.fn(),
      end: jest.fn(),
    },
  };
});

import app from "../src/server";
import pool from "../src/config/database";

const mockQuery = pool.query as jest.Mock;

describe("Admin Backend Unit Tests (Mocked DB)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("GET /health", () => {
    it("should return health status", async () => {
      const response = await request(app).get("/health").expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.message).toBe("Admin backend is running");
    });
  });

  describe("GET /api/policies", () => {
    it("should return list of policies", async () => {
      const mockPolicies = [
        {
          policy_number: "POL-001",
          policy_type: "Cyber Liability",
          first_name: "John",
          last_name: "Doe",
          company_name: "TechCorp",
          effective_date: "2024-01-01",
          expiration_date: "2025-01-01",
        },
      ];

      mockQuery.mockResolvedValueOnce({
        rows: mockPolicies,
        rowCount: 1,
      } as any);

      const response = await request(app).get("/api/policies").expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.count).toBe(1);
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it("should return policies with required fields", async () => {
      const mockPolicies = [
        {
          policy_number: "POL-001",
          policy_type: "Cyber Liability",
          first_name: "John",
          last_name: "Doe",
          company_name: "TechCorp",
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockPolicies } as any);

      const response = await request(app).get("/api/policies").expect(200);

      const policy = response.body.data[0];
      expect(policy).toHaveProperty("policy_number");
      expect(policy).toHaveProperty("policy_type");
      expect(policy).toHaveProperty("first_name");
      expect(policy).toHaveProperty("last_name");
      expect(policy).toHaveProperty("company_name");
    });
  });

  describe("GET /api/policies/:policyNumber", () => {
    it("should return a specific policy", async () => {
      const mockPolicy = {
        policy_number: "POL-001",
        policy_type: "Cyber Liability",
        first_name: "John",
        last_name: "Doe",
        email: "john@example.com",
        company_name: "TechCorp",
      };

      mockQuery.mockResolvedValueOnce({
        rows: [mockPolicy],
        rowCount: 1,
      } as any);

      const response = await request(app)
        .get("/api/policies/POL-001")
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.policy_number).toBe("POL-001");
    });

    it("should return 404 for non-existent policy", async () => {
      mockQuery.mockResolvedValueOnce({ rows: [], rowCount: 0 } as any);

      await request(app).get("/api/policies/INVALID").expect(404);
    });
  });

  describe("GET /api/customers", () => {
    it("should return list of customers", async () => {
      const mockCustomers = [
        {
          insured_id: 1,
          first_name: "John",
          last_name: "Doe",
          email: "john@example.com",
          policy_count: 2,
        },
      ];

      mockQuery.mockResolvedValueOnce({
        rows: mockCustomers,
        rowCount: 1,
      } as any);

      const response = await request(app).get("/api/customers").expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.data)).toBe(true);
    });
  });

  describe("GET /api/claims", () => {
    it("should return list of claims", async () => {
      const mockClaims = [
        {
          claim_number: "CLM-001",
          policy_number: "POL-001",
          claim_status: "Active",
          claim_amount: 5000,
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockClaims, rowCount: 1 } as any);

      const response = await request(app).get("/api/claims").expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it("should filter claims by status", async () => {
      const mockClaims = [
        {
          claim_number: "CLM-001",
          claim_status: "Active",
        },
      ];

      mockQuery.mockResolvedValueOnce({ rows: mockClaims } as any);

      const response = await request(app)
        .get("/api/claims?status=Active")
        .expect(200);

      expect(response.body.success).toBe(true);
    });
  });

  describe("GET /api/claims/stats/summary", () => {
    it("should return claims statistics", async () => {
      const mockStats = {
        total_claims: 100,
        active_claims: 50,
        closed_claims: 45,
        denied_claims: 5,
        total_amount: 500000,
      };

      mockQuery.mockResolvedValueOnce({ rows: [mockStats] } as any);

      const response = await request(app)
        .get("/api/claims/stats/summary")
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty("total_claims");
      expect(response.body.data).toHaveProperty("total_amount");
    });
  });
});
