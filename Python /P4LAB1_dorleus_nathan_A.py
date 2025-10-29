import turtle


screen = turtle.Screen()
screen.title("Square and Triangle with Turtle")

pen = turtle.Turtle()
pen.speed(3)

# Draw a square using a for loop
pen.color("blue")
for _ in range(4):
    pen.forward(100)
    pen.right(90)

# Move to a different position so both shapes are visible
pen.penup()
pen.goto(-150, -50)
pen.pendown()

# Draw a triangle using a for loop
pen.color("pink")
for _ in range(3):
    pen.forward(120)
    pen.left(120)

pen.hideturtle()
turtle.done()

