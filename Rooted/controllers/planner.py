import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "data/rooted.db"

class Planner:
    def __init__(self):
        # Prioriteiten mappen naar gewichten
        self.priority_weights = {
            "Zeer hoog": 5,
            "Hoog": 4,
            "Normaal": 3,
            "Laag": 2,
            "Geen": 1,
        }

    def calculate_task_score(self, taak):
        score = 0
        # Prioriteit
        score += self.priority_weights.get(taak["priority"], 0)

        # Deadline dichterbij = hogere score
        deadline = taak["deadline"]
        if deadline:
            days_left = (datetime.fromisoformat(deadline) - datetime.now()).days
            if days_left <= 0:
                score += 5
            elif days_left == 1:
                score += 4
            elif days_left <= 7:
                score += 3
            elif days_left <= 14:
                score += 2
            elif days_left <= 30:
                score += 1

        return score

    def get_expected_duration(self, cursor, taak):
        """Bepaal verwachte duur via focus_logs of fallback = 30 min."""
        # Eerst check view of logs
        if taak["template_id"]:
            cursor.execute("""
                SELECT AVG(actual_duration) as avg_dur
                FROM focus_logs
                WHERE template_id=?
            """, (taak["template_id"],))
            row = cursor.fetchone()
            if row and row["avg_dur"]:
                return int(row["avg_dur"])
        return 30  # fallback

    def calculate_scores_for_all_tasks(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT task_id, template_id, priority, deadline, status
            FROM taken
            WHERE status='open'
        """)
        taken = cursor.fetchall()

        result = []
        for taak in taken:
            score = self.calculate_task_score(dict(taak))
            result.append({
                "id": taak["task_id"],
                "template_id": taak["template_id"],
                "score": score
            })

        result.sort(key=lambda x: x["score"], reverse=True)
        conn.close()
        return result

    def plan_next_task(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM taken
            WHERE status='open'
            ORDER BY deadline ASC, priority DESC
            LIMIT 1
        """)
        taak = cursor.fetchone()

        if not taak:
            print("[Rooted] ✅ Geen open taken meer.")
            conn.close()
            return

        duur = self.get_expected_duration(cursor, taak)
        starttijd = datetime.now().replace(second=0, microsecond=0)
        eindtijd = starttijd + timedelta(minutes=duur)

        cursor.execute("""
            UPDATE taken
            SET planned_start=?, planned_end=?, status='ingepland'
            WHERE task_id=?
        """, (
            starttijd.strftime("%Y-%m-%d %H:%M:%S"),
            eindtijd.strftime("%Y-%m-%d %H:%M:%S"),
            taak["task_id"]
        ))
        conn.commit()

        print(f"[Rooted] ➡️ Taak {taak['task_id']} ingepland van {starttijd} tot {eindtijd}.")
        conn.close()
