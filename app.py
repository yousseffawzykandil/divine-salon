from datetime import datetime
import sqlite3
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_NAME = "database.db"


def init_db():
  with sqlite3.connect(DB_NAME) as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barber TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                UNIQUE(date, barber, time)
            )
        """)
    conn.commit()


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/barber.html")
def barber_panel():
  return render_template("barber.html")


@app.route("/api/taken", methods=["GET"])
def get_taken():
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, barber, time FROM bookings WHERE date >= ?",
        (datetime.now().strftime("%Y-%m-%d"),),
    )
    rows = cursor.fetchall()
  return jsonify([{"date": r[0], "barber": r[1], "time": r[2]} for r in rows])


@app.route("/api/book", methods=["POST"])
def book_slot():
  data = request.json
  barber = data.get("barber")
  date = data.get("date")
  time = data.get("time")
  name = data.get("name")
  phone = data.get("phone")

  if not all([barber, date, time, name, phone]):
    return jsonify({"success": False, "error": "Missing fields"}), 400

  barbers_to_try = ["sheriff", "fox"] if barber == "any" else [barber]

  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    for b in barbers_to_try:
      cursor.execute(
          "SELECT id FROM bookings WHERE date = ? AND barber = ? AND time = ?",
          (date, b, time),
      )
      if cursor.fetchone():
        continue

      try:
        cursor.execute(
            "INSERT INTO bookings (barber, date, time, name, phone) VALUES"
            " (?, ?, ?, ?, ?)",
            (b, date, time, name, phone),
        )
        conn.commit()
        return jsonify({"success": True, "barber": b})
      except sqlite3.IntegrityError:
        continue

  return jsonify(
      {
          "success": False,
          "error": "Sorry, that slot was just taken. Pick another.",
      }
  ), 409


@app.route("/api/bookings", methods=["GET"])
def get_bookings():
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, barber, date, time, name, phone FROM bookings WHERE date >="
        " ? ORDER BY date, time",
        (datetime.now().strftime("%Y-%m-%d"),),
    )
    rows = cursor.fetchall()
  return jsonify([{
      "id": r[0],
      "barber": r[1],
      "date": r[2],
      "time": r[3],
      "name": r[4],
      "phone": r[5],
  } for r in rows])


@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
  with sqlite3.connect(DB_NAME) as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()
  return jsonify({"success": True})


if __name__ == "__main__":
  init_db()
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
