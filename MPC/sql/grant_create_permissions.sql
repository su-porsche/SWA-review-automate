-- Grant CREATE permissions to swaagent user
-- Run manually: sudo -u postgres psql swadocs < grant_create_permissions.sql

-- Grant CREATE on schema
GRANT CREATE ON SCHEMA public TO swaagent;

-- Grant all privileges on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO swaagent;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO swaagent;
