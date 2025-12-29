/**
 * Database configuration and connection pool
 */

import { Pool } from "pg";
import dotenv from "dotenv";

dotenv.config();

// Database connection configuration
const pool = new Pool({
  host: process.env.POSTGRES_HOST || "postgres",
  port: parseInt(process.env.POSTGRES_PORT || "5432", 10),
  database: process.env.POSTGRES_DB || "insurance_db",
  user: process.env.POSTGRES_USER || "insure_admin",
  password: process.env.POSTGRES_PASSWORD || "insure_secure_pass_2025",
  max: 20, // Maximum number of clients in the pool
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Error handling for the pool
pool.on("error", (err) => {
  console.error("Unexpected error on idle client", err);
  process.exit(-1);
});

// Test connection
pool.query("SELECT NOW()", (err, res) => {
  if (err) {
    console.error("❌ Database connection failed:", err.message);
  } else {
    console.log("✅ Database connected successfully at", res.rows[0].now);
  }
});

export default pool;
