/**
 * API Integration Tests
 * Tests the running container via HTTP requests
 */

import axios from "axios";

// Get API base URL from environment or default to localhost
const API_BASE_URL = process.env.ADMIN_BACKEND_URL || "http://localhost:3001";

// Helper function to handle axios errors
async function makeRequest(method: "get" | "post" | "put" | "delete", url: string, data?: any) {
  try {
    const response = await axios({
      method,
      url: `${API_BASE_URL}${url}`,
      data,
      headers: {
        "Content-Type": "application/json",
      },
      validateStatus: () => true, // Don't throw on any status code
    });
    return response;
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      // TypeScript now knows error is AxiosError
      const axiosError = error;
      return axiosError.response || { status: 500, data: { message: axiosError.message } };
    }
    // For non-axios errors, return a generic error response
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return { status: 500, data: { message: errorMessage } };
  }
}

describe("Admin Backend API Tests", () => {
  describe("GET /health", () => {
    it("should return health status", async () => {
      const response = await makeRequest("get", "/health");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.message).toBe("Admin backend is running");
    });
  });

  describe("GET /api/policies", () => {
    it("should return list of policies", async () => {
      const response = await makeRequest("get", "/api/policies");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.count).toBeGreaterThan(0);
      expect(Array.isArray(response.data.data)).toBe(true);
    });

    it("should return policies with required fields", async () => {
      const response = await makeRequest("get", "/api/policies");

      expect(response.status).toBe(200);
      const policy = response.data.data[0];
      expect(policy).toHaveProperty("policy_number");
      expect(policy).toHaveProperty("policy_type");
      expect(policy).toHaveProperty("first_name");
      expect(policy).toHaveProperty("last_name");
      expect(policy).toHaveProperty("company_name");
    });
  });

  describe("GET /api/policies/:policyNumber", () => {
    it("should return a specific policy", async () => {
      // First, get a valid policy number
      const listResponse = await makeRequest("get", "/api/policies");
      const policyNumber = listResponse.data.data[0].policy_number;

      const response = await makeRequest("get", `/api/policies/${policyNumber}`);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data.policy_number).toBe(policyNumber);
    });

    it("should return 404 for non-existent policy", async () => {
      const response = await makeRequest("get", "/api/policies/INVALID123");

      expect(response.status).toBe(404);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toBe("Policy not found");
    });
  });

  // Customers Endpoints
  describe("GET /api/customers", () => {
    it("should return list of customers", async () => {
      const response = await makeRequest("get", "/api/customers");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.count).toBeGreaterThan(0);
      expect(Array.isArray(response.data.data)).toBe(true);
    });

    it("should return customers with policy counts", async () => {
      const response = await makeRequest("get", "/api/customers");

      expect(response.status).toBe(200);
      const customer = response.data.data[0];
      expect(customer).toHaveProperty("insured_id");
      expect(customer).toHaveProperty("policy_count");
      expect(customer).toHaveProperty("total_premium");
    });
  });

  describe("GET /api/customers/:insuredId", () => {
    it("should return a specific customer with policies", async () => {
      // First, get a valid insured ID
      const listResponse = await makeRequest("get", "/api/customers");
      const insuredId = listResponse.data.data[0].insured_id;

      const response = await makeRequest("get", `/api/customers/${insuredId}`);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty("customer");
      expect(response.data.data).toHaveProperty("policies");
      expect(response.data.data.customer.insured_id).toBe(insuredId);
    });

    it("should return 404 for non-existent customer", async () => {
      const response = await makeRequest("get", "/api/customers/INVALID123");

      expect(response.status).toBe(404);
      expect(response.data.success).toBe(false);
    });
  });

  // Claims Endpoints
  describe("GET /api/claims", () => {
    it("should return list of claims", async () => {
      const response = await makeRequest("get", "/api/claims");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.count).toBeGreaterThan(0);
      expect(Array.isArray(response.data.data)).toBe(true);
    });

    it("should filter claims by status", async () => {
      const response = await makeRequest("get", "/api/claims?status=Active");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      response.data.data.forEach((claim: any) => {
        expect(claim.claim_status).toBe("Active");
      });
    });
  });

  describe("GET /api/claims/stats/summary", () => {
    it("should return claims statistics", async () => {
      const response = await makeRequest("get", "/api/claims/stats/summary");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty("total_claims");
      expect(response.data.data).toHaveProperty("active_claims");
      expect(response.data.data).toHaveProperty("total_claim_amount");
    });
  });

  // Stats Endpoints
  describe("GET /api/stats/dashboard", () => {
    it("should return dashboard statistics", async () => {
      const response = await makeRequest("get", "/api/stats/dashboard");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty("overview");
      expect(response.data.data).toHaveProperty("policyByType");
      expect(response.data.data).toHaveProperty("aiSystemTypes");
      expect(response.data.data).toHaveProperty("recentClaims");
    });

    it("should have valid overview statistics", async () => {
      const response = await makeRequest("get", "/api/stats/dashboard");

      expect(response.status).toBe(200);
      const overview = response.data.data.overview;
      // PostgreSQL COUNT returns strings in some cases, parse them
      expect(parseInt(overview.total_customers)).toBeGreaterThan(0);
      expect(parseInt(overview.total_policies)).toBeGreaterThan(0);
      expect(parseInt(overview.total_claims)).toBeGreaterThan(0);
    });
  });

  describe("GET /api/stats/risk-analysis", () => {
    it("should return risk analysis data", async () => {
      const response = await makeRequest("get", "/api/stats/risk-analysis");

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(Array.isArray(response.data.data)).toBe(true);
    });
  });

  // Error Handling
  describe("Error Handling", () => {
    it("should return 404 for non-existent routes", async () => {
      const response = await makeRequest("get", "/api/nonexistent");

      expect(response.status).toBe(404);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toBe("Route not found");
    });
  });
});
