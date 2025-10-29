# Nathan Dorleus
#P3HW1_Dorleusnathan
# This program takes a number grade , determines average and displays letter grade for average.

# Enter grades for six modules

mod_1 = float(input("Enter grade for Module 1: "))
mod_2 = float(input("Enter grade for Module 2: "))
mod_3 = float(input("Enter grade for Module 3: "))
mod_4 = float(input("Enter grade for Module 4: "))
mod_5 = float(input("Enter grade for Module 5: "))
mod_6 = float(input("Enter grade for Module 6: "))

# add grades entered to a list

grades = [mod_1, mod_2, mod_3, mod_4, mod_5, mod_6]

#  determine lowest, highest , sum and average for grades
low = min(grades)
high = max(grades)
total = sum(grades)
avg = total / len(grades)

# Display summary
print("\n----------- Results -----------")
print(f"Lowest Grade:     {low}")
print(f"Highest Grade:    {high}")
print(f"Sum of Grades:    {total}")
print(f"Average:          {avg:.2f}")
print("-------------------------------")


# determine letter grade for average
if avg >= 90:
    letter_grade = "A"
elif avg >= 80:
    letter_grade = "B"
elif avg >= 70:
    letter_grade = "C"
elif avg >= 60:
    letter_grade = "D"
else:
    letter_grade = "F"
print(f"Your grade is: {letter_grade}")





