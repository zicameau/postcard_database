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
CREATE INDEX idx_tags_name ON tags(name);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER update_postcards_modtime
BEFORE UPDATE ON postcards
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();