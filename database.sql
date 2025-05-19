-- Users table (extension users)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP
);

-- User preferences
CREATE TABLE user_preferences (
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  selected_creator_id INTEGER,
  openai_api_key VARCHAR(255),
  model_name VARCHAR(100) DEFAULT 'gpt-3.5-turbo',
  num_suggestions INTEGER DEFAULT 3,
  PRIMARY KEY (user_id)
);

-- Creators table
CREATE TABLE creators (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  avatar_url VARCHAR(255),
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Creator writing styles
CREATE TABLE creator_styles (
  creator_id INTEGER REFERENCES creators(id) ON DELETE CASCADE,
  approved_emojis TEXT[], -- Array of approved emojis
  case_style VARCHAR(50), -- e.g., "lowercase", "sentence_case", "custom"
  text_replacements JSONB, -- e.g., {"you": "u", "your": "ur"}
  sentence_separators TEXT[], -- e.g., ["emoji", "new_message"]
  punctuation_rules JSONB, -- e.g., {"comma": false, "period": false}
  abbreviations JSONB, -- e.g., {"on my way": "omw", "by the way": "btw"}
  message_length_preference VARCHAR(50), -- e.g., "short", "medium", "match_fan"
  style_instructions TEXT, -- General style instructions
  tone_range VARCHAR(50), -- e.g., "friendly_to_flirty"
  PRIMARY KEY (creator_id)
);

-- Style examples for each creator
CREATE TABLE style_examples (
  id SERIAL PRIMARY KEY,
  creator_id INTEGER REFERENCES creators(id) ON DELETE CASCADE,
  fan_message TEXT NOT NULL,
  creator_responses TEXT[] NOT NULL, -- Array of response messages
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector store for conversation history per creator
CREATE TABLE vector_store (
  id SERIAL PRIMARY KEY,
  creator_id INTEGER REFERENCES creators(id) ON DELETE CASCADE,
  fan_message TEXT NOT NULL,
  creator_responses TEXT[] NOT NULL,
  embedding VECTOR(1536), -- Using pgvector extension
  similarity_score FLOAT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_vector_store_creator ON vector_store(creator_id);

-- Create IVF index for vector similarity search
-- The number of lists (100) can be adjusted based on data size
CREATE INDEX idx_vector_embedding ON vector_store 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);