-- SQLite: เปิดใช้ foreign key ทุก connection ก่อนเริ่ม transaction
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    fullname TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','teacher','technician')),
    email TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_requests (
    id INTEGER PRIMARY KEY,
    request_no TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    building TEXT NOT NULL,
    room TEXT NOT NULL,
    problem_type TEXT NOT NULL CHECK (problem_type IN ('electrical','furniture','computer','aircon','other')),
    description TEXT NOT NULL,
    urgency TEXT NOT NULL DEFAULT 'medium' CHECK (urgency IN ('low','medium','high')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','in_progress','completed')),
    assigned_to INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    due_date DATE,
    completion_date DATE,
    cost NUMERIC(12,2) CHECK (cost IS NULL OR cost >= 0),
    result TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_images (
    id INTEGER PRIMARY KEY,
    repair_id INTEGER NOT NULL REFERENCES repair_requests(id),
    image_type TEXT NOT NULL CHECK (image_type IN ('before','after')),
    image_path TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY,
    repair_id INTEGER NOT NULL REFERENCES repair_requests(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS request_counters (
    month TEXT PRIMARY KEY NOT NULL,
    sequence INTEGER NOT NULL
);
