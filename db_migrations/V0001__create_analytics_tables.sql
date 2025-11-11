CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    premium BOOLEAN DEFAULT FALSE,
    total_tokens INTEGER DEFAULT 0,
    dialogs_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dialogs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    telegram_id BIGINT,
    tokens INTEGER DEFAULT 0,
    model VARCHAR(50) DEFAULT 'GPT-3.5',
    status VARCHAR(50) DEFAULT 'Активный',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE token_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    total_tokens INTEGER DEFAULT 0,
    active_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_dialogs_user_id ON dialogs(user_id);
CREATE INDEX idx_dialogs_created_at ON dialogs(created_at);
CREATE INDEX idx_token_stats_date ON token_stats(date);