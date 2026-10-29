# PeopleDesk

A polished employee-directory web application built with Flask and an Excel-backed data store. PeopleDesk replaces the original terminal prompt with a fast, focused interface for managing employee records.

## Highlights

- Modern responsive dashboard with a restrained glassmorphic visual system
- Create, edit, search, and delete employee records
- Live headcount, role count, payroll, and average-salary metrics
- Server-side validation with helpful errors and duplicate-ID protection
- Safe workbook writes using a temporary file replacement
- Excel remains the source of truth: existing `employees.xlsx` data is preserved

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Data model

The workbook uses four required columns:

| Column | Description |
| --- | --- |
| Employee ID | Unique positive integer |
| Name | Employee’s full name |
| Position | Current role or title |
| Salary | Monthly salary |

## Configuration

Set `EMPLOYEE_DATA_FILE` to use a different workbook path. Set `PORT` to choose another local port.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/employees?q=term | List or search employees |
| POST | /api/employees | Create an employee |
| PUT | /api/employees/:id | Update an employee |
| DELETE | /api/employees/:id | Remove an employee |
| GET | /api/stats | Dashboard statistics |

This app is designed for a trusted local or internal environment. Add authentication and role-based access control before exposing it publicly.
