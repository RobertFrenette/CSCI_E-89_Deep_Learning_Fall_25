#!/bin/bash
# MongoDB initialization script

echo "Initializing MongoDB for AI Agent Insurance Platform..."

# Note: Only MONGO_INITDB_ROOT_USERNAME, MONGO_INITDB_ROOT_PASSWORD, and MONGO_INITDB_DATABASE are available

mongosh -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin <<EOF
use $MONGO_INITDB_DATABASE

// Create user_profiles collection with schema validation
db.createCollection("user_profiles", {
  validator: {
    \$jsonSchema: {
      bsonType: "object",
      required: ["email", "username", "password", "created_at"],
      properties: {
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\$",
          description: "User email address"
        },
        username: {
          bsonType: "string",
          description: "Unique username for login"
        },
        password: {
          bsonType: "string",
          description: "Hashed password"
        },
        created_at: {
          bsonType: "date",
          description: "Account creation timestamp"
        },
        updated_at: {
          bsonType: "date",
          description: "Last update timestamp"
        },
        last_login: {
          bsonType: "date",
          description: "Last login timestamp"
        }
      }
    }
  }
})

// Create query_history collection
db.createCollection("query_history", {
  validator: {
    \$jsonSchema: {
      bsonType: "object",
      required: ["user_id", "query_text", "query_timestamp"],
      properties: {
        user_id: {
          bsonType: "objectId",
          description: "Reference to user _id from user_profiles"
        },
        query_text: {
          bsonType: "string",
          description: "User's natural language query"
        },
        query_type: {
          enum: ["policy_info", "claims", "coverage", "general"],
          description: "Category of query"
        },
        rag_response: {
          bsonType: "string",
          description: "AI-generated response"
        },
        sources_used: {
          bsonType: "array",
          items: {
            bsonType: "string"
          }
        },
        satisfaction_rating: {
          bsonType: "int",
          minimum: 1,
          maximum: 5
        },
        query_timestamp: {
          bsonType: "date"
        }
      }
    }
  }
})

// Create indexes
db.user_profiles.createIndex({ "email": 1 }, { unique: true })
db.user_profiles.createIndex({ "username": 1 }, { unique: true })
db.user_profiles.createIndex({ "created_at": -1 })

db.query_history.createIndex({ "user_id": 1 })
db.query_history.createIndex({ "query_timestamp": -1 })
db.query_history.createIndex({ "query_type": 1 })
db.query_history.createIndex({ "user_id": 1, "query_timestamp": -1 })

print("MongoDB collections and indexes created successfully!")
EOF

echo "MongoDB initialization complete!"
