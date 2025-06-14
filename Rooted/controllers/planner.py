import sqlite3
from datetime import datetime, timedelta

DATABASE_PATH = "data/rooted.db"

class Planner:
    def __init__(self):
        self.weights = {
            "deadline_type": {
                "harde": 5,
                "zachte": 3,
                "advies": 2,
                "geen": 1,
            },
            "prioriteit": {i: i for i in range(1, 6)},
            "deadline_group": {
                "vandaag": 5,
                "morgen": 4,
                "deze week": 3,
                "komende 2 weken": 2,
                "komende maand": 1,
                "meer dan een maand": 0,
            },
            "risk_factor": 1,
            "leftover": 1
        }

    def calculate_task_score(self, taak):
        score = 0
        score += self.weights["deadline_type"].get(taak["deadline_type"], 0)
        # Fallback voor ontbrekende prioriteit
        prioriteit = taak.get("prioriteit")
        if prioriteit is None:
            prioriteit = 0
        else:
            prioriteit = int(prioriteit)
        score += self.weights["prioriteit"].get(prioriteit, 0)
        score += self.weights["deadline_group"].get(taak["deadline_group"], 0)
        score += float(taak["risk_factor"] or 0) * self.weights["risk_factor"]
        score += int(taak["leftover"] or 0) * self.weights["leftover"]
        return score

    def calculate_scores_for_all_tasks(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Alleen uitvoerbare taken (type='taak')
        cursor.execute("""
            SELECT id, naam, deadline_type, prioriteit, deadline_group, risk_factor, leftover
            FROM taak
            WHERE status = 'open' AND type = 'taak'
        """)
        taken = cursor.fetchall()
        conn.close()

        result = []
        for taak in taken:
            score = self.calculate_task_score(dict(taak))
            result.append({
                "id": taak["id"],
                "naam": taak["naam"],
                "score": score
            })

        result.sort(key=lambda x: x["score"], reverse=True)
        return result

    def plan_tasks(self, dagen=5):
        taken = self.calculate_scores_for_all_tasks()

        now = datetime.now().replace(second=0, microsecond=0)
        if now.hour < 8:
            starttijd = now.replace(hour=8, minute=0)
        else:
            starttijd = now

        eindtijd = starttijd.replace(hour=17, minute=0)
        geplande_dagen = 0

        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        for taak in taken:
            if geplande_dagen >= dagen:
                break

            cursor.execute("SELECT verwachte_duur FROM taak WHERE id=?", (taak["id"],))
            duur = cursor.fetchone()["verwachte_duur"]

            if duur is None:
                print(
                    f"[Rooted] ⚠️ Taak ID {taak['id']} ('{taak['naam']}') heeft geen verwachte_duur → wordt overgeslagen.")
                continue

            taak_eindtijd = starttijd + timedelta(minutes=duur)
            if taak_eindtijd > eindtijd:
                # Volgende dag om 08:00
                starttijd = (starttijd + timedelta(days=1)).replace(hour=8, minute=0)
                eindtijd = starttijd.replace(hour=17, minute=0)
                geplande_dagen += 1

                if geplande_dagen >= dagen:
                    break

                taak_eindtijd = starttijd + timedelta(minutes=duur)

            print(
                f"[Rooted] ➡️ Plan taak ID {taak['id']} ('{taak['naam']}') vanaf {starttijd.strftime('%Y-%m-%d %H:%M:%S')}")
            cursor.execute("""
                UPDATE taak SET ingepland_vanaf=? WHERE id=?
            """, (starttijd.strftime("%Y-%m-%d %H:%M:%S"), taak["id"]))
            conn.commit()

            starttijd = taak_eindtijd

        conn.close()

    def plan_next_task(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        while True:
            cursor.execute("""
                SELECT * FROM taak
                WHERE status = 'open'
                ORDER BY prioriteit DESC, deadline ASC
                LIMIT 1
            """)
            taak = cursor.fetchone()

            if not taak:
                print("[Rooted] ✅ Geen open taken meer.")
                break

            taak = dict(taak)
            taak_type = taak.get("type", "taak")
            print(f"[Rooted] ▶️ Bezig met taak ID {taak['id']} ('{taak['naam']}') - type: {taak_type}")

            if taak_type == "taak":
                # Plan deze taak direct in
                starttijd = datetime.now().replace(second=0, microsecond=0)
                eindtijd = starttijd + timedelta(minutes=taak["verwachte_duur"] or 15)
                cursor.execute("""
                    UPDATE taak SET ingepland_vanaf=?, status='ingepland' WHERE id=?
                """, (starttijd.strftime("%Y-%m-%d %H:%M:%S"), taak["id"]))
                conn.commit()
                print(f"[Rooted] ➡️ Taak '{taak['naam']}' ingepland vanaf {starttijd}.")
                break  # Stop na deze taak!

            elif taak_type == "popup":
                print(f"[Rooted] 🔔 Popup: {taak['beschrijving']}")
                # TODO: Roep GUI-functie aan om popup te tonen
                break

            elif taak_type == "wachttijd":
                print(f"[Rooted] ⏳ Wachttijd-taak '{taak['naam']}' - wachten op trigger.")
                break

            elif taak_type == "answertask":
                correct = self.check_answer_filter(taak)
                if correct:
                    print(f"[Rooted] ✅ Antwoord klopt voor '{taak['naam']}', ga door met volgende taak.")
                    cursor.execute("""
                        UPDATE taak SET status='afgerond' WHERE id=?
                    """, (taak["id"],))
                    conn.commit()
                    continue  # Direct door naar de volgende taak
                else:
                    print(f"[Rooted] ❌ Antwoord klopt niet voor '{taak['naam']}', planner stopt.")
                    break

        conn.close()

    def check_answer_filter(self, taak):
        # TODO: Echte logica voor antwoordfilter
        return True  # Voor nu altijd "juist"
