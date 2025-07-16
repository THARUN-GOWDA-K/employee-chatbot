import pandas as pd
import os

# Load greetings from a text file
def load_greetings(filepath='c:\\Users\\tharu\\OneDrive\\Desktop\\chatbot\\employee\\greetings.txt'):
    try:
        with open(filepath, 'r') as file:
            greetings = file.readlines()
        return [g.strip() for g in greetings]
    except FileNotFoundError:
        print("Greetings file not found. Default greetings will be used.")
        return ["Hi there!", "Hello!", "Hey! How can I help you?"]

# Load employee data from an Excel file
def load_employees(filename='employees.xlsx'):
    if os.path.exists(filename):
        return pd.read_excel(filename)
    else:
        return pd.DataFrame(columns=['Employee ID', 'Name', 'Position', 'Salary'])

# Save employee data to an Excel file
def save_employees(df, filename='employees.xlsx'):
    df.to_excel(filename, index=False)

# Add a new employee
def add_employee(df, emp_id, name, position, salary):
    if emp_id in df['Employee ID'].values:
        print("Employee ID already exists. Try a different ID.")
        return df
    new_employee = pd.DataFrame([[emp_id, name, position, salary]], columns=df.columns)
    return pd.concat([df, new_employee], ignore_index=True)

# Update an existing employee
def update_employee(df, emp_id, name=None, position=None, salary=None):
    if emp_id not in df['Employee ID'].values:
        print("Employee not found.")
        return df

    if name:
        df.loc[df['Employee ID'] == emp_id, 'Name'] = name
    if position:
        df.loc[df['Employee ID'] == emp_id, 'Position'] = position
    if salary is not None:
        df.loc[df['Employee ID'] == emp_id, 'Salary'] = salary

    return df

# Delete an employee
def delete_employee(df, emp_id):
    if emp_id not in df['Employee ID'].values:
        print("Employee not found.")
        return df
    return df[df['Employee ID'] != emp_id]

# Display employee information
def display_employee(df, emp_id):
    employee = df[df['Employee ID'] == emp_id]
    if employee.empty:
        print("Employee not found.")
    else:
        print("\n--- Employee Details ---")
        print(f"ID: {employee.iloc[0]['Employee ID']}")
        print(f"Name: {employee.iloc[0]['Name']}")
        print(f"Position: {employee.iloc[0]['Position']}")
        print(f"Salary: {employee.iloc[0]['Salary']}")

# Main chatbot function
def chatbot():
    greetings = load_greetings()
    employees = load_employees()

    print("Welcome to the Employee Information System!")
    print(greetings[0])  # Greet the user

    while True:
        user_input = input("\nYou: ").strip().lower()

        if user_input == 'exit':
            print("Goodbye! Have a great day!")
            break

        elif "hi" in user_input:
            print(greetings[1])

        elif "hello" in user_input:
            print(greetings[2])

        elif "add employee" in user_input:
            try:
                emp_id = int(input("Enter Employee ID: "))
                name = input("Enter Name: ").strip()
                position = input("Enter Position: ").strip()
                salary = float(input("Enter Salary: "))
                employees = add_employee(employees, emp_id, name, position, salary)
                save_employees(employees)
                print("✅ Employee added successfully.")
            except ValueError:
                print("❌ Invalid input. Please enter correct ID and Salary.")

        elif "update employee" in user_input:
            try:
                emp_id = int(input("Enter Employee ID to update: "))
                name = input("Enter new Name (leave blank to skip): ").strip()
                position = input("Enter new Position (leave blank to skip): ").strip()
                salary_input = input("Enter new Salary (leave blank to skip): ").strip()
                salary = float(salary_input) if salary_input else None

                employees = update_employee(employees, emp_id, name or None, position or None, salary)
                save_employees(employees)
                print("✅ Employee updated successfully.")
            except ValueError:
                print("❌ Invalid salary input.")

        elif "delete employee" in user_input:
            try:
                emp_id = int(input("Enter Employee ID to delete: "))
                employees = delete_employee(employees, emp_id)
                save_employees(employees)
                print("✅ Employee deleted successfully.")
            except ValueError:
                print("❌ Invalid Employee ID.")

        elif "employee details" in user_input:
            try:
                emp_id = int(input("Enter Employee ID: "))
                display_employee(employees, emp_id)
            except ValueError:
                print("❌ Invalid Employee ID.")

        else:
            print("🤖 I'm sorry, I can only help with employee information (add, update, delete, view).")

if __name__ == "__main__":
    chatbot()
