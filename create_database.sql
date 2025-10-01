-- SQL script to create romskjema database
-- Note: This needs to be run by a user with database creation permissions
-- Connect to the 'master' database first, then run this command

CREATE DATABASE romskjema;

-- Optional: Set database options
ALTER DATABASE romskjema SET READ_COMMITTED_SNAPSHOT ON;
ALTER DATABASE romskjema SET ALLOW_SNAPSHOT_ISOLATION ON;