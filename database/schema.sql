-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (minimal info for privacy)
CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    pin_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Drop IDs table
CREATE TABLE IF NOT EXISTS drop_ids (
    id VARCHAR(10) PRIMARY KEY,
    owner_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    is_single_use BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Messages/Files table
CREATE TABLE IF NOT EXISTS inbox_items (
    id BIGSERIAL PRIMARY KEY,
    drop_id VARCHAR(10) REFERENCES drop_ids(id) ON DELETE CASCADE,
    sender_anon_id VARCHAR(20),
    file_id TEXT,
    file_type VARCHAR(50),
    message_text TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_drop_ids_owner ON drop_ids(owner_id);
CREATE INDEX IF NOT EXISTS idx_drop_ids_active ON drop_ids(is_active);
CREATE INDEX IF NOT EXISTS idx_inbox_items_drop_id ON inbox_items(drop_id);
CREATE INDEX IF NOT EXISTS idx_inbox_items_created_at ON inbox_items(created_at);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE drop_ids ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbox_items ENABLE ROW LEVEL SECURITY;