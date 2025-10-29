# Nate Dorleus
# 10/17/2025
# P3LAB
# This program takes calculates the number of dollars, quarters, dimes, nickels, and pennies

#Pseudocode:
#1. Ask user to enter an amount of money as a float
#2. Convert amount to cents (multiply by 100 and round to nearest integer)
#3. Calculate number of each denomination:
#      dollars = total_cents // 100
#      total_cents = total_cents - (dollars * 100)
#      quarters = total_cents // 25
#      total_cents = total_cents - (quarters * 25)
#      dimes = total_cents // 10
#      total_cents = total_cents - (dimes * 10)
#      nickels = total_cents // 5
#      total_cents = total_cents - (nickels * 5)
#      pennies = total_cents
#4. For each denomination, only print if count > 0
#5. Use singular form if count == 1, plural form if count > 1



amount = float(input("Enter amount of money: "))

cents = round(amount * 100)

dollars = cents // 100
cents = cents - (dollars * 100)

quarters = cents // 25
cents = cents - (quarters * 25)

dimes = cents // 10
cents = cents - (dimes * 10)

nickels = cents // 5
cents = cents - (nickels * 5)

pennies = cents

# Output Section
if amount == 0:
    print("No change")
else:
    print("\nYour change is:")

    if dollars > 0:
        print(f"{dollars} dollar" if dollars == 1 else f"{dollars} dollars")

    if quarters > 0:
        print(f"{quarters} quarter" if quarters == 1 else f"{quarters} quarters")

    if dimes > 0:
        print(f"{dimes} dime" if dimes == 1 else f"{dimes} dimes")

    if nickels > 0:
        print(f"{nickels} nickel" if nickels == 1 else f"{nickels} nickels")

    if pennies > 0:
        print(f"{pennies} penny" if pennies == 1 else f"{pennies} pennies")
