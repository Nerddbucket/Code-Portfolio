# Nathan Dorleus
# 1 Oct 2025
# P2LAB
# This program allows the user to choose a vehicle from a dictionary of cars
# and their MPG values. It then calculates how many gallons of gas are required
# to drive a given number of miles.

# Dictionary of cars with their MPG
cars = {
    "Camaro": 18.21,
    "Prius": 52.36,
    "Model S": 110,
    "Silverado": 26
}

# Get the dictionary keys
keys = cars.keys()

print(keys)
vehicle = input("Enter a vehicle to see its mpg: ")

mpg = cars[vehicle]
print(f"\nThe {vehicle} gets {mpg} mpg.")

miles = float(input(f"\nHow many miles will you drive the {vehicle}? "))

gallons = miles / mpg

print(f"\n{gallons:.2f} gallon(s) of gas are needed to drive the {vehicle} {miles:.1f} miles.")
