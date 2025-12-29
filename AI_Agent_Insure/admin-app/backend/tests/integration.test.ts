/**
 * Integration tests for Admin Backend API
 * These tests run against running containers and require external services
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
      const axiosError = error;
      return axiosError.response || { status: 500, data: { message: axiosError.message } };
    }
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return { status: 500, data: { message: errorMessage } };
  }
}

describe("Admin Backend Integration Tests", () => {
  describe("Health Check", () => {
    it("should return 200 and health status", async () => {
      const response = await makeRequest("get", "/health");
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty("success");
      expect(response.data.success).toBe(true);
    });
  });

  describe("Policies Endpoint", () => {
    it("should return policies data from Postgres", async () => {
      const response = await makeRequest("get", "/api/policies");
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty("success");
      expect(response.data.success).toBe(true);
      expect(Array.isArray(response.data.data)).toBe(true);
      // Should have at least some policies
      if (response.data.data.length > 0) {
        expect(response.data.data[0]).toHaveProperty("policy_number");
      }
    });
  });

  describe("Stats Endpoint", () => {
    it("should return dashboard stats", async () => {
      const response = await makeRequest("get", "/api/stats/dashboard");
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty("success");
      expect(response.data.success).toBe(true);
      expect(response.data.data).toHaveProperty("overview");
      if (response.data.data.overview) {
        expect(response.data.data.overview).toHaveProperty("total_policies");
        expect(response.data.data.overview).toHaveProperty("total_customers");
        expect(response.data.data.overview).toHaveProperty("total_claims");
      }
    });
  });
});

