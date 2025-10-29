# Nathan Dorleus
# 1 Oct 2025
# P2LAB
# This program takes the radius of a circle (entered by the user) and calculates
# the diameter, circumference, and area. The results are displayed with specific formatting.

import math

# Get radius from user
radius = float(input("Enter the radius of the circle: "))

# Calculations
diameter = 2 * radius
circumference = 2 * math.pi * radius
area = math.pi * (radius ** 2)

# Display results with formatting
print(f"Diameter of the circle: {diameter:.1f}")
print(f"Circumference of circle : {circumference:.2f}")
print(f"Area of the Circle : {area:.3f}")
