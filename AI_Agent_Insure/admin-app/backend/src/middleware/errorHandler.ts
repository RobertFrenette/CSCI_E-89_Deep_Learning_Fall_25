/**
 * Error handling middleware
 */

import { Request, Response, NextFunction } from "express";
import { DatabaseError } from "../types";

const errorHandler = (
  err: DatabaseError,
  _req: Request,
  res: Response,
  _next: NextFunction
): void => {
  console.error("Error:", err);

  // Database errors
  if (err.code) {
    switch (err.code) {
      case "23505": // Unique violation
        res.status(409).json({
          success: false,
          message: "Duplicate entry",
          error: err.detail,
        });
        return;
      case "23503": // Foreign key violation
        res.status(400).json({
          success: false,
          message: "Referenced record not found",
          error: err.detail,
        });
        return;
      case "22P02": // Invalid text representation
        res.status(400).json({
          success: false,
          message: "Invalid data format",
          error: err.message,
        });
        return;
      default:
        res.status(500).json({
          success: false,
          message: "Database error",
          error:
            process.env.NODE_ENV === "development"
              ? err.message
              : "Internal server error",
        });
        return;
    }
  }

  // Default error
  const statusCode = (err as any).statusCode || 500;
  res.status(statusCode).json({
    success: false,
    message: err.message || "Internal server error",
    ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
  });
};

export default errorHandler;
