from flask import Flask, render_template, request, redirect, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key"

DATA_FILE = "data.json"


# ================= LOAD DATA =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "students": [], "attendance": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


# ================= SAVE DATA =================
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        for u in data["users"]:
            if u["username"] == username and u["password"] == password:
                session["user"] = username
                return redirect("/")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================
@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")

    data = load_data()

    selected_date = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
    selected_month = selected_date[:7]

    stats = {}

    # INIT STUDENTS
    for s in data["students"]:
        stats[s["roll"]] = {
            "name": s["name"],
            "image": s["image"],
            "present": 0,
            "absent": 0,
            "leave": 0,
            "history": []
        }

    # FILTER ATTENDANCE
    for a in data["attendance"]:
        if a["date"].startswith(selected_month):
            roll = a["roll"]

            if roll in stats:
                stats[roll]["history"].append(a)

                if a["status"] == "Present":
                    stats[roll]["present"] += 1
                elif a["status"] == "Absent":
                    stats[roll]["absent"] += 1
                elif a["status"] == "Leave":
                    stats[roll]["leave"] += 1

    # PERCENTAGE
    for roll in stats:
        total = stats[roll]["present"] + stats[roll]["absent"] + stats[roll]["leave"]
        stats[roll]["percentage"] = round((stats[roll]["present"] / total) * 100, 1) if total else 0

    return render_template("index.html", stats=stats, selected_date=selected_date)


# ================= MARK ATTENDANCE (STRICT 1 DAY RULE) =================
@app.route("/mark", methods=["POST"])
def mark():
    data = load_data()

    roll = request.form["roll"]
    status = request.form["status"]
    date = request.form["date"]

    # REMOVE OLD ENTRY (same student same day)
    data["attendance"] = [
        a for a in data["attendance"]
        if not (a["roll"] == roll and a["date"] == date)
    ]

    # ADD NEW ENTRY
    data["attendance"].append({
        "roll": roll,
        "date": date,
        "day": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
        "status": status
    })

    save_data(data)
    return redirect(f"/?date={date}")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)