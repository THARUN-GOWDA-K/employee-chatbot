import importlib
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd


class EmployeeAssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def setUp(self):
        self.data_file = Path(self.tempdir.name) / "employees.xlsx"
        pd.DataFrame(
            [
                {"Employee ID": 101, "Name": "Priya Shah", "Position": "Engineer", "Salary": 75000},
                {"Employee ID": 102, "Name": "Ravi Kumar", "Position": "Designer", "Salary": 65000},
                {"Employee ID": 103, "Name": "Maya Nair", "Position": "Engineer", "Salary": 85000},
            ]
        ).to_excel(self.data_file, index=False)

        os.environ["EMPLOYEE_DATA_FILE"] = str(self.data_file)
        import app as app_module

        self.app_module = importlib.reload(app_module)
        self.client = self.app_module.app.test_client()

    def test_chat_help(self):
        response = self.client.post("/api/chat", json={"message": "help"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["intent"], "help")
        self.assertIn("suggested_prompts", payload)

    def test_chat_find_by_id(self):
        response = self.client.post("/api/chat", json={"message": "find employee by ID 101"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["intent"], "find_employee")
        self.assertEqual(payload["results"]["employees"][0]["name"], "Priya Shah")

    def test_chat_payroll(self):
        response = self.client.post("/api/chat", json={"message": "show payroll"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["intent"], "payroll")
        self.assertAlmostEqual(payload["results"]["payroll"], 225000)

    def test_existing_employees_api_still_works(self):
        response = self.client.get("/api/employees?q=priya")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["employees"]), 1)
        self.assertEqual(payload["employees"][0]["employee_id"], 101)


if __name__ == "__main__":
    unittest.main()
