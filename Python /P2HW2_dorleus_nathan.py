# Nate Dorleus
# October 4, 2025
# P2HW2
# This program asks the user to enter grades for six modules,
# stores them in a list, and then displays the lowest, highest,
# total, and average of the grades entered.


#Pseudocode:
#  Display a message asking user to enter grades for six modules.
#  Input the grade for Module 1 and store it in a list.
#  Input the grade for Module 2 and store it in the list.
#  Input the grade for Module 3 and store it in the list.
#  Input the grade for Module 4 and store it in the list.
#  Input the grade for Module 5 and store it in the list.
#  Input the grade for Module 6 and store it in the list.
#  Display all entered grades (optional check step).
#  Calculate the lowest grade using min().
#  Calculate the highest grade using max().
#  Calculate the sum of all grades using sum().
#  Calculate the average by dividing the sum by the number of grades.
#  Display results:
#  Lowest grade
#  Highest grade
#  Sum of grades
#  Average grade (formatted to 2 decimal places)


# Step 1: Create an empty list to hold grades
module_grades = []

# Step 2: Collect grades from the user
module_grades.append(float(input("Enter grade for Module 1: ")))
module_grades.append(float(input("Enter grade for Module 2: ")))
module_grades.append(float(input("Enter grade for Module 3: ")))
module_grades.append(float(input("Enter grade for Module 4: ")))
module_grades.append(float(input("Enter grade for Module 5: ")))
module_grades.append(float(input("Enter grade for Module 6: ")))

# Step 3: Perform calculations
lowest = min(module_grades)
highest = max(module_grades)
total = sum(module_grades)
average = total / len(module_grades)

# Step 4: Display results
print("\n------------Results------------")
print(f"Lowest Grade:       {lowest}")
print(f"Highest Grade:      {highest}")
print(f"Sum of Grades:      {total}")
print(f"Average:            {average:.2f}")
print("--------------------------------")
