# Nate Dorleus
# 10/17/2025
# P3HW2
# This program calculates user Salary.



## Pseudocode:
#1. Display program purpose
#2. Ask user to enter employee name
#3. Ask user to enter number of hours worked
#4. Ask user to enter hourly pay rate
#5. If hours worked > 40:
#      overtime_hours = hours_worked - 40
#      overtime_pay = overtime_hours * (pay_rate * 1.5)
#      regular_pay = 40 * pay_rate
#   Else:
#      overtime_hours = 0
#      overtime_pay = 0
#      regular_pay = hours_worked * pay_rate
#6. Calculate gross_pay = regular_pay + overtime_pay
#7. Display employee name, pay rate, number of hours worked,
# overtime hours, overtime pay, regular pay, and gross pay


employee_name = input("Enter employee's name: ")
hours_worked = float(input("Enter number of hours worked this week: "))
pay_rate = float(input("Enter employee's pay rate: "))

if hours_worked > 40:
    overtime_hours = hours_worked - 40
    overtime_pay = overtime_hours * (pay_rate * 1.5)
    regular_pay = 40 * pay_rate
else:
    overtime_hours = 0
    overtime_pay = 0
    regular_pay = hours_worked * pay_rate

gross_pay = regular_pay + overtime_pay


print("\n----------------------------------------")
print(f"Employee Name:     {employee_name}")
print(f"Pay Rate:          ${pay_rate:.2f}")
print(f"Hours Worked:      {hours_worked}")
print(f"Overtime Hours:    {overtime_hours}")
print(f"Overtime Pay:      ${overtime_pay:.2f}")
print(f"Regular Pay:       ${regular_pay:.2f}")
print(f"Gross Pay:         ${gross_pay:.2f}")
print("----------------------------------------")
