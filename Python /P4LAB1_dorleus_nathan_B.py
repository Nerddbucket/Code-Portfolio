import turtle


screen = turtle.Screen()
screen.title("Initials: ND (Turtle Graphics)")

pen = turtle.Turtle()
pen.speed(3)
pen.color("purple")
pen.pensize(8)

# Parameters for letter sizing and spacing
height = 200
width_n = 120
spacing = 60

# Starting baseline position for the first letter (N)
start_x = -220
start_y = -100

# Draw 'N'
pen.penup()
pen.setpos(start_x, start_y)
pen.pendown()
pen.setpos(start_x, start_y + height)  # Left vertical
pen.setpos(start_x + width_n, start_y)  # Diagonal to bottom-right
pen.setpos(start_x + width_n, start_y + height)  # Right vertical

# Move to position for 'D'
pen.penup()
sx = start_x + width_n + spacing
sy = start_y
pen.setpos(sx, sy)
pen.pendown()

# Draw 'D' (vertical + semicircle)
pen.setpos(sx, sy + height)  # Left vertical of D
pen.setheading(0)  # Face right to start arc
pen.circle(-height / 2, 180)  # Clockwise semicircle to form the right side of 'D'

pen.hideturtle()
turtle.done()


