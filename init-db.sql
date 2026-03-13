CREATE TABLE IF NOT EXISTS page_view_counts (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    page_url TEXT,
    view_count BIGINT,
    PRIMARY KEY (window_start, page_url)
);

CREATE TABLE IF NOT EXISTS active_users (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    active_user_count BIGINT,
    PRIMARY KEY (window_start, window_end) -- Added window_end to PK for sliding windows
);

CREATE TABLE IF NOT EXISTS user_sessions (
    user_id TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds DOUBLE PRECISION,
    PRIMARY KEY (user_id, start_time) -- Allows one user to have multiple sessions
);