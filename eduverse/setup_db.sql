-- Create the database
CREATE DATABASE eduverse_db;

-- Create the user
CREATE USER eduverse_db_user WITH PASSWORD 'eduversestrongpassword';

-- Grant database-level privileges
GRANT ALL PRIVILEGES ON DATABASE eduverse_db TO eduverse_db_user;

-- IMPORTANT: Connect to the new database to grant schema permissions
-- If running manually in psql, type: \c contextid_db
\c eduverse_db

-- Grant schema-level privileges (Fixes the "Permission Denied" error)
GRANT ALL ON SCHEMA public TO eduverse_db_user;

-- Optional: Make the user the owner of the schema for full control
ALTER SCHEMA public OWNER TO eduverse_db_user;

-- To run `python manage.py test`, able to create a temporary test database
ALTER ROLE eduverse_db_user CREATEDB;