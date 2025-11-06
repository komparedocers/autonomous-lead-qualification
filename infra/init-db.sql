-- Database initialization script for Lead Qualification Platform

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create indexes for better performance
-- Note: Most tables are created by SQLAlchemy, but we can add additional indexes here

-- Create hypertables for time-series data
-- This will be done after tables are created by the application

-- Sample data for testing (optional)
-- Uncomment to insert sample data

-- INSERT INTO companies (name, domain, industry, country, size, employee_count, description, tech_stack, sources, metadata, created_at)
-- VALUES
--   ('Acme Corp', 'acme.com', 'Technology', 'United States', '500-1000', 750, 'Leading SaaS company', '["AWS", "Python", "React"]', '[]', '{}', NOW()),
--   ('TechStart Inc', 'techstart.io', 'Fintech', 'United States', '50-200', 120, 'Fintech startup', '["Azure", "Node.js", "MongoDB"]', '[]', '{}', NOW()),
--   ('DataCo Solutions', 'dataco.com', 'Data Analytics', 'United Kingdom', '200-500', 350, 'Data analytics platform', '["GCP", "Python", "Kubernetes"]', '[]', '{}', NOW());

-- Create a default admin user (password: admin123)
-- Note: This will be created by the application, but adding here for reference
-- Password hash is bcrypt hash of 'admin123'

-- Grants and permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app;

-- Vacuum and analyze
VACUUM ANALYZE;
