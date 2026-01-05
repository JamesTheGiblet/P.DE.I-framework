import sqlite3
import os
from pathlib import Path

def seed_database():
    # Define path relative to project root
    root_dir = Path(__file__).parent.parent
    db_dir = root_dir / "data" / "db"
    db_path = db_dir / "memory.db"

    # Ensure directory exists
    if not db_dir.exists():
        print(f"📂 Creating directory: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)

    print(f"🌱 Seeding database at: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_code TEXT,
            corrected_code TEXT,
            context TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check if data exists
    cursor.execute("SELECT count(*) FROM corrections")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"ℹ️  Database already contains {count} records. Skipping seed.")
        conn.close()
        return

    # Sample Data: Forge Theory Violations -> Fixes
    samples = [
        ("val = exp(t/tau);", "val = exp(-t/tau);", "decay formula"),
        ("heat = exp(t/tau);", "heat = (1 - exp(-t/tau));", "growth formula"),
        ("servo.write(target * (1 - exp(t/tau)));", "servo.write(target * (1 - exp(-t/tau)));", "step response"),
        ("delay(1000);", "if (millis() - last > 1000) { ... }", "non-blocking"),
        ("integral += error;", "integral += error * dt;", "pid control"),
        ("ldr = (ldr + raw) / 2;", "ldr = ldr * (1 - alpha) + raw * alpha;", "smoothing"),
        ("door_width = 30;", "door_width = 36; // ADA Compliance", "architecture"),
        ("sql = 'SELECT * FROM users WHERE id=' + id;", "sql = 'SELECT * FROM users WHERE id=?'; // Parameterized", "security"),
        ("GameObject.Find('Player'); // Inside Update", "// Cache in Start()\nplayer = GameObject.Find('Player');", "unity optimization"),
        ("M104 S200; // No wait", "M109 S200; // Wait for temp", "3d printing")
    ]

    print(f"📝 Inserting {len(samples)} sample correction records...")
    cursor.executemany(
        "INSERT INTO corrections (original_code, corrected_code, context) VALUES (?, ?, ?)",
        samples
    )
    
    conn.commit()
    conn.close()
    print("✅ Database seeded successfully.")

if __name__ == "__main__":
    seed_database()