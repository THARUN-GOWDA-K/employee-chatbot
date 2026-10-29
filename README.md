# Employee Assistant

A Flask employee management app with a chatbot-first experience and a separate Directory/Admin workspace. Data remains stored in `employees.xlsx` and existing CRUD APIs are preserved.

## Features

- Chat-first home screen with suggested prompts and friendly answers
- Supported assistant queries:
  - show all employees
  - find/search employee by name or ID
  - list roles
  - payroll total
  - average salary
  - highest salary employee
  - help
- Structured chat API response from `POST /api/chat`
- Separate Directory/Admin view for search, add, edit, and delete
- Responsive glassmorphic UI with accessible controls and keyboard-friendly input
- Excel-backed storage with safe temp-file replacement

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/employees?q=term` | List/search employees |
| POST | `/api/employees` | Create employee |
| PUT | `/api/employees/<id>` | Update employee |
| DELETE | `/api/employees/<id>` | Delete employee |
| GET | `/api/stats` | Headcount, roles, payroll, average salary |
| POST | `/api/chat` | Assistant intent + friendly response + structured results |

### `POST /api/chat` request

```json
{ "message": "Find employee by ID 101" }
```

### `POST /api/chat` response shape

```json
{
  "intent": "find_employee",
  "message": "I found Priya Shah for employee ID 101.",
  "results": {
    "employees": [
      { "employee_id": 101, "name": "Priya Shah", "position": "Engineer", "salary": 75000 }
    ]
  },
  "suggested_prompts": ["Show all employees", "List roles", "Show payroll", "Help"]
}
```

## Testing

Run:

```bash
python -m unittest discover -s tests
```

## Configuration

- `EMPLOYEE_DATA_FILE`: custom workbook path (default: `employees.xlsx`)
- `PORT`: Flask port (default: `5000`)
