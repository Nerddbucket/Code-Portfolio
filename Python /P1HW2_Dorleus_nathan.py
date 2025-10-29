# Nathan Dorleus
# 20 Sept 2025
# P1HW2
# A program that calculates travel expenses and remaining budget

# budget
budget = float(input("Enter Budget: "))

# travel destination
destination = input("Enter your travel destination: ")

# gas
gas = float(input("How much do you think you will spend on gas? "))

# accommodation
accommodation = float(input("Approximately, how much will you spend on accommodation? "))

# food
food = float(input("Last, how much do you think you will spend on food? "))

# Add expenses
total_expenses = gas + accommodation + food

# Subtract expenses from budget
remaining_budget = budget - total_expenses

# Display results
print()
print("------------Travel Budget Details------------")
print(f"Location: {destination}")
print(f"Initial Budget: ${budget:.2f}")
print()
print(f"Fuel: ${gas:.2f}")
print(f"Accommodation: ${accommodation:.2f}")
print(f"Food: ${food:.2f}")
print()
print(f"Total Expenses: ${total_expenses:.2f}")
print()
print(f"Remaining Balance: ${remaining_budget:.2f}")