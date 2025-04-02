-- Comprehensive Database Schema for Postcard Database

-- Ensure UUID extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Reset database script - removes all existing data, tables, types, and policies
DROP TABLE IF EXISTS postcard_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS postcards CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop existing types
DROP TYPE IF EXISTS postcard_type CASCADE;
DROP TYPE IF EXISTS postcard_era CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

-- Drop existing functions
DROP FUNCTION IF EXISTS update_modified_column CASCADE;
DROP FUNCTION IF EXISTS handle_new_user CASCADE;

-- Create enum for postcard types
CREATE TYPE postcard_type AS ENUM (
  'RPPC', 
  'Divided Back', 
  'Undivided Back', 
  'Linen', 
  'Chrome', 
  'Continental'
);

-- Create enum for decades/eras
CREATE TYPE postcard_era AS ENUM (
  '1860s',
  '1870s',
  '1880s',
  '1890s',
  '1900s',
  '1910s',
  '1920s',
  '1930s',
  '1940s',
  '1950s',
  '1960s',
  '1970s',
  '1980s',
  '1990s',
  '2000s',
  '2010s',
  '2020s'
);

-- Create enum for user roles
CREATE TYPE user_role AS ENUM (
  'admin',
  'user'
);

-- Users table (modified to work with Supabase Auth)
CREATE TABLE users (
  id UUID PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255),
  role user_role NOT NULL DEFAULT 'user',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Main postcards table
CREATE TABLE postcards (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  era postcard_era,
  is_posted BOOLEAN DEFAULT FALSE,
  is_written BOOLEAN DEFAULT FALSE,
  manufacturer VARCHAR(255),
  type postcard_type,
  front_image_url TEXT,
  back_image_url TEXT,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table for tags (for better searchability)
CREATE TABLE tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(50) NOT NULL UNIQUE
);

-- Junction table for postcards and tags (many-to-many)
CREATE TABLE postcard_tags (
  postcard_id UUID REFERENCES postcards(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (postcard_id, tag_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_postcards_era ON postcards(era);
CREATE INDEX idx_postcards_type ON postcards(type);
CREATE INDEX idx_postcards_manufacturer ON postcards(manufacturer);
CREATE INDEX idx_postcards_user_id ON postcards(user_id);
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update the updated_at column
CREATE TRIGGER update_postcards_modtime
BEFORE UPDATE ON postcards
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_users_modtime
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE postcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE postcard_tags ENABLE ROW LEVEL SECURITY;

-- User table policies
-- Allow users to view and update their own data
CREATE POLICY "Users can view their own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- IMPORTANT: Allow the application service role to insert new users
CREATE POLICY "Service role can insert users" ON users
    FOR INSERT WITH CHECK (true);

-- IMPORTANT: Allow the application service role to manage all users for admin functions
CREATE POLICY "Service role can manage all users" ON users
    FOR ALL USING (true);

-- Postcard table policies
-- Allow authenticated users to create, view, update, and delete their own postcards
CREATE POLICY "Users can create postcards" ON postcards
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own postcards" ON postcards
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own postcards" ON postcards
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own postcards" ON postcards
    FOR DELETE USING (auth.uid() = user_id);

-- Admin policies for postcards
CREATE POLICY "Admins can manage all postcards" ON postcards
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Tag policies
-- Allow authenticated users to view tags
CREATE POLICY "Users can view tags" ON tags
    FOR SELECT USING (auth.role() = 'authenticated');

-- Postcard tag policies
CREATE POLICY "Users can view postcard tags" ON postcard_tags
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM postcards 
            WHERE postcards.id = postcard_tags.postcard_id 
            AND postcards.user_id = auth.uid()
        )
    );

-- Insert an initial admin user for manual testing (optional)
-- Note: In production, prefer creating admin users through Supabase Auth
INSERT INTO users (id, username, email, password_hash, role)
VALUES (
  uuid_generate_v4(),
  'admin',
  'admin@example.com',
  -- This is a placeholder - in production, use Supabase Auth to create admin users
  'placeholder_hash',
  'admin'
);

-- Optional: Initial tag seeding
INSERT INTO tags (name) VALUES 
  ('vintage'),
  ('landscape'),
  ('historical'),
  ('travel'),
  ('architecture');