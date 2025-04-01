-- Reset database script - removes all existing data, tables, types, and policies

-- Drop existing tables with cascade to remove dependencies
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

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
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
  user_id UUID REFERENCES users(id),
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

-- Insert an initial admin user
-- Username: admin@example.com
-- Password: Admin123! (this is hashed below)
INSERT INTO users (id, username, email, password_hash, role)
VALUES (
  uuid_generate_v4(),
  'admin',
  'admin@example.com',
  -- This is a hashed version of 'Admin123!' - you should change this in production
  'pbkdf2:sha256:600000$aCVDv2O3AuiF$a73a6a9827d05b8a63f30b69c4d8f8a32e6c578bec047d3be0d2cab8ba95d13b',
  'admin'
);

/*
Note: For Supabase storage, you'll need to:
1. Create a bucket named 'postcard-images' in the Supabase dashboard
2. Set the appropriate permissions (public access for read, authenticated for write)

To do this programmatically in SQL, you would use:
*/

-- Create storage bucket for postcard images (if using Supabase SQL)
-- Note: This may need to be done in the Supabase dashboard if SQL access to storage isn't available
-- CREATE BUCKET IF NOT EXISTS "postcard-images";
-- ALTER BUCKET "postcard-images" ENABLE public ACCESS;

/*
Storage Policies:
- For reading images (public):
  CREATE POLICY "Public Access" ON STORAGE.OBJECTS
    FOR SELECT USING (bucket_id = 'postcard-images');

- For uploading images (authenticated users only):
  CREATE POLICY "Authenticated Users Can Upload" ON STORAGE.OBJECTS
    FOR INSERT USING (
      bucket_id = 'postcard-images' AND
      auth.role() = 'authenticated'
    );

- For deleting images (only by owner or admin):
  CREATE POLICY "Owner or Admin Can Delete" ON STORAGE.OBJECTS
    FOR DELETE USING (
      bucket_id = 'postcard-images' AND
      (
        auth.uid() = owner OR
        EXISTS (
          SELECT 1 FROM users
          WHERE id = auth.uid() AND role = 'admin'
        )
      )
    );
*/