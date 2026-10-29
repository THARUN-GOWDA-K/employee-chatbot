from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = Path(os.environ.get("EMPLOYEE_DATA_FILE", BASE_DIR / "employees.xlsx"))
COLUMNS = ["Employee ID", "Name", "Position", "Salary"]
SUGGESTED_PROMPTS = [
    "Show all employees",
    "Find employee by ID 101",
    "Search employee by name Priya",
    "List roles",
    "Show payroll",
    "Show average salary",
    "Who has the highest salary?",
    "Help",
]
lock = threading.RLock()

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


def empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def load_employees() -> pd.DataFrame:
    if not DATA_FILE.exists():
        return empty_frame()
    try:
        frame = pd.read_excel(DATA_FILE)
    except Exception as exc:
        raise RuntimeError("Could not read the employee workbook.") from exc
    missing = [column for column in COLUMNS if column not in frame.columns]
    if missing:
        raise RuntimeError("The employee workbook is missing required columns.")
    frame = frame[COLUMNS].copy()
    frame["Employee ID"] = pd.to_numeric(frame["Employee ID"], errors="coerce")
    frame["Salary"] = pd.to_numeric(frame["Salary"], errors="coerce")
    return frame.dropna(subset=["Employee ID", "Name", "Position", "Salary"])


def save_employees(frame: pd.DataFrame) -> None:
    temporary = DATA_FILE.with_suffix(".tmp.xlsx")
    frame.to_excel(temporary, index=False)
    temporary.replace(DATA_FILE)


def validate_employee(payload: dict[str, Any], *, updating: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {}
    required = [] if updating else ["employee_id", "name", "position", "salary"]
    for key in required:
        if key not in payload:
            raise ValueError(f"{key.replace('_', ' ').title()} is required.")

    if "employee_id" in payload:
        try:
            employee_id = int(payload["employee_id"])
        except (TypeError, ValueError):
            raise ValueError("Employee ID must be a whole number.")
        if employee_id <= 0:
            raise ValueError("Employee ID must be greater than zero.")
        data["Employee ID"] = employee_id

    for source, target, label in [("name", "Name", "Name"), ("position", "Position", "Position")]:
        if source in payload:
            value = str(payload[source]).strip()
            if len(value) < 2 or len(value) > 80:
                raise ValueError(f"{label} must be between 2 and 80 characters.")
            data[target] = value

    if "salary" in payload:
        try:
            salary = float(payload["salary"])
        except (TypeError, ValueError):
            raise ValueError("Salary must be a valid number.")
        if salary < 0 or salary > 100_000_000:
            raise ValueError("Salary must be between 0 and 100,000,000.")
        data["Salary"] = salary
    return data


def to_record(row: pd.Series) -> dict[str, Any]:
    return {
        "employee_id": int(row["Employee ID"]),
        "name": str(row["Name"]),
        "position": str(row["Position"]),
        "salary": float(row["Salary"]),
    }


def to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    ordered = frame.sort_values(["Name", "Employee ID"], kind="stable")
    return [to_record(row) for _, row in ordered.iterrows()]


def chat_response(intent: str, message: str, results: dict[str, Any] | None = None):
    return jsonify({
        "intent": intent,
        "message": message,
        "results": results or {},
        "suggested_prompts": SUGGESTED_PROMPTS,
    })


def extract_name_term(message: str) -> str:
    quoted = re.search(r'"([^"]{2,80})"', message)
    if quoted:
        return quoted.group(1).strip()

    lowered = message.lower()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    cleaned = re.sub(
        r"\b(show|list|find|search|lookup|employee|employees|by|name|id|for|please|me|the|a|an|with|called|named)\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) >= 2:
        return cleaned
    return ""


def parse_employee_id(message: str) -> int | None:
    numbers = re.findall(r"\d+", message)
    if not numbers:
        return None
    return int(numbers[0])


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/employees")
def list_employees():
    query = request.args.get("q", "").strip().lower()
    with lock:
        frame = load_employees()
    if query:
        matches = frame.astype(str).apply(lambda column: column.str.lower().str.contains(query, regex=False))
        frame = frame[matches.any(axis=1)]
    frame = frame.sort_values(["Name", "Employee ID"], kind="stable")
    return jsonify({"employees": [to_record(row) for _, row in frame.iterrows()]})


@app.get("/api/stats")
def stats():
    with lock:
        frame = load_employees()
    total_salary = float(frame["Salary"].sum()) if not frame.empty else 0
    return jsonify({
        "headcount": int(len(frame)),
        "payroll": total_salary,
        "average_salary": total_salary / len(frame) if len(frame) else 0,
        "roles": int(frame["Position"].nunique()) if not frame.empty else 0,
    })


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        raise ValueError("Please enter a message for the assistant.")

    normalized = message.lower()

    with lock:
        frame = load_employees()

    if any(keyword in normalized for keyword in ["help", "what can you do", "commands", "options"]):
        return chat_response(
            "help",
            "I can search the directory, list roles, and answer payroll questions. Try one of the suggested prompts.",
            {
                "capabilities": [
                    "Show all employees",
                    "Find employee by ID or name",
                    "List available roles",
                    "Show payroll totals and salary insights",
                ],
            },
        )

    if any(keyword in normalized for keyword in ["all employees", "show employees", "list employees", "show all"]):
        employees = to_records(frame)
        return chat_response(
            "show_all_employees",
            "Here is the full employee directory." if employees else "No employees are currently available.",
            {"employees": employees, "count": len(employees)},
        )

    if "role" in normalized or "position" in normalized:
        if frame.empty:
            return chat_response("list_roles", "No roles are available because the directory is empty.", {"roles": []})
        role_counts = frame["Position"].astype(str).value_counts().sort_index()
        roles = [{"name": role, "count": int(count)} for role, count in role_counts.items()]
        return chat_response("list_roles", "Here are the roles in your directory.", {"roles": roles})

    if "highest" in normalized and "salary" in normalized or "top salary" in normalized or "highest paid" in normalized:
        if frame.empty:
            return chat_response("highest_salary", "No salary data is available yet.", {})
        top = frame.loc[frame["Salary"].idxmax()]
        employee = to_record(top)
        return chat_response(
            "highest_salary",
            f"{employee['name']} has the highest salary right now.",
            {"employee": employee, "highest_salary": employee["salary"]},
        )

    if "average" in normalized and "salary" in normalized:
        average_salary = float(frame["Salary"].mean()) if not frame.empty else 0.0
        return chat_response(
            "average_salary",
            "Here is the current average salary.",
            {"average_salary": average_salary, "headcount": int(len(frame))},
        )

    if "payroll" in normalized or ("total" in normalized and "salary" in normalized):
        payroll_value = float(frame["Salary"].sum()) if not frame.empty else 0.0
        return chat_response(
            "payroll",
            "Here is the current payroll total.",
            {"payroll": payroll_value, "headcount": int(len(frame))},
        )

    if any(keyword in normalized for keyword in ["find", "search", "lookup", "employee id", "by id", "by name"]):
        employee_id = parse_employee_id(message)
        if employee_id is not None:
            matches = frame[frame["Employee ID"] == employee_id]
            if matches.empty:
                return chat_response(
                    "find_employee",
                    f"I could not find an employee with ID {employee_id}.",
                    {"employees": [], "query": {"employee_id": employee_id}},
                )
            employees = to_records(matches)
            return chat_response(
                "find_employee",
                f"I found {employees[0]['name']} for employee ID {employee_id}.",
                {"employees": employees, "query": {"employee_id": employee_id}},
            )

        term = extract_name_term(message)
        if term:
            matches = frame[frame["Name"].astype(str).str.contains(term, case=False, regex=False)]
            employees = to_records(matches)
            if employees:
                return chat_response(
                    "find_employee",
                    f"I found {len(employees)} matching employee(s) for “{term}”.",
                    {"employees": employees, "query": {"name": term}},
                )
            return chat_response(
                "find_employee",
                f"I could not find anyone matching “{term}”.",
                {"employees": [], "query": {"name": term}},
            )

        return chat_response(
            "find_employee",
            "Please include an employee name or ID to search.",
            {"employees": []},
        )

    return chat_response(
        "unknown",
        "I did not understand that yet. Try asking for employees, roles, payroll, or say help.",
        {},
    )


@app.post("/api/employees")
def create_employee():
    payload = request.get_json(silent=True) or {}
    data = validate_employee(payload)
    with lock:
        frame = load_employees()
        if data["Employee ID"] in frame["Employee ID"].values:
            return jsonify({"error": "An employee with this ID already exists."}), 409
        frame = pd.concat([frame, pd.DataFrame([data])], ignore_index=True)
        save_employees(frame)
    return jsonify({"employee": {key.lower().replace(" ", "_"): value for key, value in data.items()}}), 201


@app.put("/api/employees/<int:employee_id>")
def update_employee(employee_id: int):
    data = validate_employee(request.get_json(silent=True) or {}, updating=True)
    if not data:
        return jsonify({"error": "Send at least one field to update."}), 400
    data.pop("Employee ID", None)
    with lock:
        frame = load_employees()
        match = frame["Employee ID"] == employee_id
        if not match.any():
            return jsonify({"error": "Employee not found."}), 404
        for column, value in data.items():
            frame.loc[match, column] = value
        save_employees(frame)
        employee = to_record(frame.loc[match].iloc[0])
    return jsonify({"employee": employee})


@app.delete("/api/employees/<int:employee_id>")
def delete_employee(employee_id: int):
    with lock:
        frame = load_employees()
        match = frame["Employee ID"] == employee_id
        if not match.any():
            return jsonify({"error": "Employee not found."}), 404
        save_employees(frame.loc[~match].copy())
    return "", 204


@app.errorhandler(ValueError)
def handle_validation(error: ValueError):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(RuntimeError)
def handle_storage(error: RuntimeError):
    return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
