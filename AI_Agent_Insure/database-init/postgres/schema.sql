-- AI Insurance Database Schema
-- Created: 2025-12-19
-- Description: Schema for AI Agent Insurance platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean re-initialization)
DROP TABLE IF EXISTS claims_history CASCADE;
DROP TABLE IF EXISTS ai_risk_profile CASCADE;
DROP TABLE IF EXISTS coverage_details CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS insureds CASCADE;

-- Create insureds table (customers)
CREATE TABLE insureds (
    insured_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    phone_number VARCHAR(20),
    email_address VARCHAR(255) UNIQUE NOT NULL,
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    company_name VARCHAR(255),
    industry VARCHAR(100),
    contact_person VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create policies table
CREATE TABLE policies (
    policy_number VARCHAR(50) PRIMARY KEY,
    insured_id VARCHAR(50) NOT NULL,
    policy_type VARCHAR(255) NOT NULL,
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    policy_status VARCHAR(50) DEFAULT 'Active',
    payment_status VARCHAR(50) DEFAULT 'Pending',
    annual_premium DECIMAL(12, 2),
    monthly_premium DECIMAL(12, 2),
    payment_method VARCHAR(50),
    broker VARCHAR(255),
    discounts_applied TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (insured_id) REFERENCES insureds(insured_id) ON DELETE CASCADE,
    CONSTRAINT chk_dates CHECK (expiration_date > effective_date)
);

-- Create coverage_details table
CREATE TABLE coverage_details (
    policy_number VARCHAR(50) PRIMARY KEY,
    coverage_limit DECIMAL(15, 2) NOT NULL,
    deductible DECIMAL(12, 2) NOT NULL,
    coverage_tier VARCHAR(50),
    optional_addons_selected TEXT,
    regulatory_addons_selected TEXT,
    business_interruption_coverage BOOLEAN DEFAULT FALSE,
    cyber_extension BOOLEAN DEFAULT FALSE,
    incident_response_addon BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_number) REFERENCES policies(policy_number) ON DELETE CASCADE
);

-- Create ai_risk_profile table
CREATE TABLE ai_risk_profile (
    policy_number VARCHAR(50) PRIMARY KEY,
    ai_system_type VARCHAR(100),
    deployment_stage VARCHAR(50),
    number_of_active_agents INTEGER DEFAULT 0,
    critical_workflows_protected BOOLEAN DEFAULT FALSE,
    incident_history_count INTEGER DEFAULT 0,
    last_ai_incident_date DATE,
    has_high_risk_use_cases BOOLEAN DEFAULT FALSE,
    regulatory_classification VARCHAR(50),
    risk_score_internal INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_number) REFERENCES policies(policy_number) ON DELETE CASCADE,
    CONSTRAINT chk_risk_score CHECK (risk_score_internal >= 0 AND risk_score_internal <= 100)
);

-- Create claims_history table
CREATE TABLE claims_history (
    claim_id VARCHAR(50) PRIMARY KEY,
    policy_number VARCHAR(50) NOT NULL,
    insured_id VARCHAR(50) NOT NULL,
    claim_date DATE NOT NULL,
    claim_type VARCHAR(100),
    claim_description TEXT,
    claim_status VARCHAR(50) DEFAULT 'Pending',
    claim_amount DECIMAL(12, 2),
    amount_paid DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_number) REFERENCES policies(policy_number) ON DELETE CASCADE,
    FOREIGN KEY (insured_id) REFERENCES insureds(insured_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_policies_insured_id ON policies(insured_id);
CREATE INDEX idx_policies_status ON policies(policy_status);
CREATE INDEX idx_policies_type ON policies(policy_type);
CREATE INDEX idx_claims_policy_number ON claims_history(policy_number);
CREATE INDEX idx_claims_insured_id ON claims_history(insured_id);
CREATE INDEX idx_claims_status ON claims_history(claim_status);
CREATE INDEX idx_claims_date ON claims_history(claim_date);
CREATE INDEX idx_insureds_email ON insureds(email_address);
CREATE INDEX idx_insureds_company ON insureds(company_name);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_insureds_updated_at BEFORE UPDATE ON insureds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_coverage_details_updated_at BEFORE UPDATE ON coverage_details
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_risk_profile_updated_at BEFORE UPDATE ON ai_risk_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_history_updated_at BEFORE UPDATE ON claims_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant privileges (optional, for future multi-user scenarios)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO insure_admin;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO insure_admin;
