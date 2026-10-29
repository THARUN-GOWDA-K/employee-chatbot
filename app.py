"""
Employee Chatbot - Flask Backend
A conversational employee information assistant with a modern glassmorphic UI.
"""

import os
import re
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "employees.xlsx")

# ─────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────

def load_employees():
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame(columns=["Employee ID", "Name", "Position", "Salary"])


def save_employees(df: pd.DataFrame):
    df.to_excel(EXCEL_FILE, index=False)


def df_to_list(df: pd.DataFrame):
    records = []
    for _, row in df.iterrows():
        records.append({
            "id":       int(row["Employee ID"]),
            "name":     str(row["Name"]).strip().title(),
            "position": str(row["Position"]).strip().title(),
            "salary":   float(row["Salary"]),
        })
    return records


# ─────────────────────────────────────────────
# NLP / intent engine
# ─────────────────────────────────────────────

def parse_intent(text: str):
    t = text.lower().strip()

    greetings = {"hi", "hello", "hey", "hiya", "howdy", "good morning",
                 "good afternoon", "good evening", "what's up", "wassup"}
    if any(g in t for g in greetings):
        return ("greeting", {})

    farewells = {"bye", "goodbye", "see you", "later", "exit", "quit"}
    if any(f in t for f in farewells):
        return ("farewell", {})

    if re.search(r"\b(help|what can you do|commands|options)\b", t):
        return ("help", {})

    # Payroll / salary stats
    if re.search(r"\b(payroll|total salary|salary (summary|total|stats)|budget|wage)\b", t):
        return ("payroll_summary", {})

    # Highest/lowest paid — check before list_all
    if re.search(r"\b(highest|most earn|top earn|best paid|highest paid|who earn|who makes|earns? the most|most paid)\b", t):
        return ("top_earner", {})
    if re.search(r"\b(lowest|least|minimum|min)[\w\s]*(paid|salary|earn)\b", t):
        return ("bottom_earner", {})

    # Count — check before list_all
    if re.search(r"\b(how many|count|number of)\b.*\b(employee|staff|people|person)\b", t):
        return ("count", {})

    # Show all
    if re.search(r"\b(all|list|show all|every|everyone|employees)\b", t):
        return ("list_all", {})

    # Average salary
    if re.search(r"\b(average|avg|mean)\b.*\b(salary|pay|wage)\b", t):
        return ("avg_salary", {})

    # Find by ID
    id_match = re.search(r"\b(?:id|employee id|emp)[\s#:]*(\d+)\b", t)
    if id_match:
        return ("find_by_id", {"id": int(id_match.group(1))})

    # Search by position / role
    pos_keywords = re.search(
        r"\b(manager|developer|engineer|designer|analyst|hr|admin|intern|ceo|cto|cfo|director|lead|senior|junior)\b",
        t
    )
    if pos_keywords:
        return ("search_by_position", {"position": pos_keywords.group(1)})

    # Salary of a person
    salary_person = re.search(
        r"\b(?:salary|pay|earn(?:ing)?s?|wage)\b[\s\w]*(?:of|for)\b[\s]+([a-z ]{2,30})",
        t
    )
    if salary_person:
        return ("salary_of", {"name": salary_person.group(1).strip()})

    # Find by name
    name_match = re.search(
        r"\b(?:find|search|show|who is|details? (?:of|for)|info (?:of|for)|about|get)\b[\s]+([a-z ]{2,30})",
        t
    )
    if name_match:
        return ("find_by_name", {"name": name_match.group(1).strip()})

    return ("unknown", {})


def generate_reply(intent: str, params: dict, df: pd.DataFrame):
    employees = df_to_list(df)
    n = len(employees)

    if intent == "greeting":
        return {
            "type": "text",
            "message": "👋 Hello! I'm your **Employee Assistant**. I can help you find employee info, payroll summaries, and more. Try one of the suggestions below or type your question!",
        }

    if intent == "farewell":
        return {
            "type": "text",
            "message": "👋 Goodbye! Have a productive day!",
        }

    if intent == "help":
        return {
            "type": "text",
            "message": (
                "Here's what I can do:\n\n"
                "• **List employees** — *Show all employees*\n"
                "• **Find by name** — *Find Tharun*\n"
                "• **Find by ID** — *Employee ID 16*\n"
                "• **Search by role** — *Show all managers*\n"
                "• **Payroll summary** — *Total payroll*\n"
                "• **Top earner** — *Who earns the most?*\n"
                "• **Average salary** — *What's the average salary?*\n"
                "• **Count** — *How many employees do we have?*"
            ),
        }

    if intent == "list_all":
        if not employees:
            return {"type": "text", "message": "No employees found in the database."}
        return {
            "type": "employee_list",
            "message": f"Here are all **{n}** employee{'s' if n != 1 else ''}:",
            "employees": employees,
        }

    if intent == "count":
        return {
            "type": "text",
            "message": f"We currently have **{n}** employee{'s' if n != 1 else ''} in the system.",
        }

    if intent == "payroll_summary":
        if not employees:
            return {"type": "text", "message": "No payroll data available."}
        total = sum(e["salary"] for e in employees)
        avg   = total / n
        top   = max(employees, key=lambda e: e["salary"])
        low   = min(employees, key=lambda e: e["salary"])
        return {
            "type": "payroll",
            "message": "💰 **Payroll Summary**",
            "stats": {
                "total_employees": n,
                "total_payroll":   total,
                "average_salary":  avg,
                "highest_paid":    top,
                "lowest_paid":     low,
            },
        }

    if intent == "top_earner":
        if not employees:
            return {"type": "text", "message": "No employees found."}
        top = max(employees, key=lambda e: e["salary"])
        return {
            "type": "employee_list",
            "message": f"🏆 The highest-paid employee is **{top['name']}** at ₹{top['salary']:,.0f}/yr:",
            "employees": [top],
        }

    if intent == "bottom_earner":
        if not employees:
            return {"type": "text", "message": "No employees found."}
        low = min(employees, key=lambda e: e["salary"])
        return {
            "type": "employee_list",
            "message": f"📉 The lowest-paid employee is **{low['name']}** at ₹{low['salary']:,.0f}/yr:",
            "employees": [low],
        }

    if intent == "avg_salary":
        if not employees:
            return {"type": "text", "message": "No payroll data available."}
        avg = sum(e["salary"] for e in employees) / n
        return {
            "type": "text",
            "message": f"📊 The average salary across all {n} employees is **₹{avg:,.0f}** per year.",
        }

    if intent == "find_by_id":
        eid = params["id"]
        match = [e for e in employees if e["id"] == eid]
        if match:
            return {
                "type": "employee_list",
                "message": f"Found employee with ID **{eid}**:",
                "employees": match,
            }
        return {"type": "text", "message": f"❌ No employee found with ID **{eid}**."}

    if intent == "find_by_name":
        query = params["name"].lower()
        match = [e for e in employees if query in e["name"].lower()]
        if match:
            return {
                "type": "employee_list",
                "message": f"Found **{len(match)}** result{'s' if len(match) != 1 else ''} for \"{params['name'].title()}\":",
                "employees": match,
            }
        return {"type": "text", "message": f"❌ No employee found matching **\"{params['name'].title()}\"**."}

    if intent == "search_by_position":
        pos = params["position"]
        match = [e for e in employees if pos.lower() in e["position"].lower()]
        if match:
            return {
                "type": "employee_list",
                "message": f"Found **{len(match)}** {pos.title()}{'s' if len(match) != 1 else ''}:",
                "employees": match,
            }
        return {"type": "text", "message": f"❌ No employees found with role **\"{pos.title()}\"**."}

    if intent == "salary_of":
        query = params["name"].lower()
        match = [e for e in employees if query in e["name"].lower()]
        if match:
            names = ", ".join(f"**{e['name']}** (₹{e['salary']:,.0f})" for e in match)
            return {"type": "text", "message": f"💵 Salary info: {names}"}
        return {"type": "text", "message": f"❌ No employee found matching \"{params['name'].title()}\"."}

    return {
        "type": "text",
        "message": (
            "🤖 I didn't quite understand that. Try asking:\n"
            "• *Show all employees*\n"
            "• *Find [name]*\n"
            "• *Who earns the most?*\n"
            "• *Total payroll*\n"
            "Or type **help** to see all commands."
        ),
    }


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    df = load_employees()
    intent, params = parse_intent(message)
    reply = generate_reply(intent, params, df)
    return jsonify(reply)


# ─────────────────────────────────────────────
# Employee CRUD API
# ─────────────────────────────────────────────

@app.route("/api/employees", methods=["GET"])
def get_employees():
    df = load_employees()
    return jsonify(df_to_list(df))


@app.route("/api/employees", methods=["POST"])
def add_employee():
    data = request.get_json(silent=True) or {}
    required = ["id", "name", "position", "salary"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields: id, name, position, salary"}), 400

    df = load_employees()
    emp_id = int(data["id"])
    if emp_id in df["Employee ID"].values:
        return jsonify({"error": f"Employee ID {emp_id} already exists"}), 409

    new_row = pd.DataFrame([[emp_id, data["name"].strip(), data["position"].strip(), float(data["salary"])]],
                            columns=["Employee ID", "Name", "Position", "Salary"])
    df = pd.concat([df, new_row], ignore_index=True)
    save_employees(df)
    return jsonify({"message": "Employee added", "employee": df_to_list(df)[-1]}), 201


@app.route("/api/employees/<int:emp_id>", methods=["PUT"])
def update_employee(emp_id):
    df = load_employees()
    if emp_id not in df["Employee ID"].values:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json(silent=True) or {}
    if "name"     in data: df.loc[df["Employee ID"] == emp_id, "Name"]     = data["name"].strip()
    if "position" in data: df.loc[df["Employee ID"] == emp_id, "Position"] = data["position"].strip()
    if "salary"   in data: df.loc[df["Employee ID"] == emp_id, "Salary"]   = float(data["salary"])

    save_employees(df)
    updated = df_to_list(df[df["Employee ID"] == emp_id])[0]
    return jsonify({"message": "Employee updated", "employee": updated})


@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):
    df = load_employees()
    if emp_id not in df["Employee ID"].values:
        return jsonify({"error": "Employee not found"}), 404

    df = df[df["Employee ID"] != emp_id]
    save_employees(df)
    return jsonify({"message": f"Employee {emp_id} deleted"})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    df = load_employees()
    employees = df_to_list(df)
    n = len(employees)
    if n == 0:
        return jsonify({"total": 0, "payroll": 0, "average": 0, "positions": {}})

    total   = sum(e["salary"] for e in employees)
    average = total / n
    positions = {}
    for e in employees:
        positions[e["position"]] = positions.get(e["position"], 0) + 1

    return jsonify({
        "total":     n,
        "payroll":   total,
        "average":   average,
        "positions": positions,
        "top":       max(employees, key=lambda e: e["salary"]),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
