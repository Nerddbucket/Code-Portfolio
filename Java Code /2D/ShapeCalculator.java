import javax.swing.JOptionPane;
import java.text.DecimalFormat;
import java.util.ArrayList;

// Abstract base class for all shapes
abstract class Shape {
    protected String name;
    
    public Shape(String name) {
        this.name = name;
    }
    
    public String getName() {
        return name;
    }
    
    public abstract String getInfo();
}

// Abstract class for 2D shapes
abstract class Shape2D extends Shape {
    public Shape2D(String name) {
        super(name);
    }
    
    public abstract double calculateArea();
    
    @Override
    public String getInfo() {
        DecimalFormat df = new DecimalFormat("#.##");
        return name + " - Area: " + df.format(calculateArea()) + " sq units";
    }
}

// Abstract class for 3D shapes
abstract class Shape3D extends Shape {
    public Shape3D(String name) {
        super(name);
    }
    
    public abstract double calculateVolume();
    public abstract double calculateSurfaceArea();
    
    @Override
    public String getInfo() {
        DecimalFormat df = new DecimalFormat("#.##");
        return name + " - Volume: " + df.format(calculateVolume()) + 
            " cubic units, Surface Area: " + df.format(calculateSurfaceArea()) + " sq units";
    }
}

// 2D Shape Classes
class Circle extends Shape2D {
    private double radius;
    
    public Circle(double radius) {
        super("Circle");
        this.radius = radius;
    }
    
    @Override
    public double calculateArea() {
        return Math.PI * radius * radius;
    }
}

class Rectangle extends Shape2D {
    private double length, width;
    
    public Rectangle(double length, double width) {
        super("Rectangle");
        this.length = length;
        this.width = width;
    }
    
    @Override
    public double calculateArea() {
        return length * width;
    }
}

class Triangle extends Shape2D {
    private double base, height;
    
    public Triangle(double base, double height) {
        super("Triangle");
        this.base = base;
        this.height = height;
    }
    
    @Override
    public double calculateArea() {
        return 0.5 * base * height;
    }
}

class Square extends Shape2D {
    private double side;
    
    public Square(double side) {
        super("Square");
        this.side = side;
    }
    
    @Override
    public double calculateArea() {
        return side * side;
    }
}

class Trapezoid extends Shape2D {
    private double base1, base2, height;
    
    public Trapezoid(double base1, double base2, double height) {
        super("Trapezoid");
        this.base1 = base1;
        this.base2 = base2;
        this.height = height;
    }
    
    @Override
    public double calculateArea() {
        return 0.5 * (base1 + base2) * height;
    }
}

// 3D Shape Classes
class Sphere extends Shape3D {
    private double radius;
    
    public Sphere(double radius) {
        super("Sphere");
        this.radius = radius;
    }
    
    @Override
    public double calculateVolume() {
        return (4.0/3.0) * Math.PI * Math.pow(radius, 3);
    }
    
    @Override
    public double calculateSurfaceArea() {
        return 4 * Math.PI * radius * radius;
    }
}

class Cube extends Shape3D {
    private double side;
    
    public Cube(double side) {
        super("Cube");
        this.side = side;
    }
    
    @Override
    public double calculateVolume() {
        return Math.pow(side, 3);
    }
    
    @Override
    public double calculateSurfaceArea() {
        return 6 * side * side;
    }
}

class Cylinder extends Shape3D {
    private double radius, height;
    
    public Cylinder(double radius, double height) {
        super("Cylinder");
        this.radius = radius;
        this.height = height;
    }
    
    @Override
    public double calculateVolume() {
        return Math.PI * radius * radius * height;
    }
    
    @Override
    public double calculateSurfaceArea() {
        return 2 * Math.PI * radius * (radius + height);
    }
}

class Cone extends Shape3D {
    private double radius, height;
    
    public Cone(double radius, double height) {
        super("Cone");
        this.radius = radius;
        this.height = height;
    }
    
    @Override
    public double calculateVolume() {
        return (1.0/3.0) * Math.PI * radius * radius * height;
    }
    
    @Override
    public double calculateSurfaceArea() {
        double slantHeight = Math.sqrt(radius * radius + height * height);
        return Math.PI * radius * (radius + slantHeight);
    }
}

class RectangularPrism extends Shape3D {
    private double length, width, height;
    
    public RectangularPrism(double length, double width, double height) {
        super("Rectangular Prism");
        this.length = length;
        this.width = width;
        this.height = height;
    }
    
    @Override
    public double calculateVolume() {
        return length * width * height;
    }
    
    @Override
    public double calculateSurfaceArea() {
        return 2 * (length * width + width * height + height * length);
    }
}

// Main Application Class
public class ShapeCalculator {
    private ArrayList<Shape2D> shapes2D;
    private ArrayList<Shape3D> shapes3D;
    private DecimalFormat df;
    
    public ShapeCalculator() {
        shapes2D = new ArrayList<>();
        shapes3D = new ArrayList<>();
        df = new DecimalFormat("#.##");
    }
    
    public void run() {
        while (true) {
            String[] options = {
                "Create 2D Shape",
                "Create 3D Shape",
                "View All Shapes",
                "Calculate Total Area (2D)",
                "Calculate Total Volume (3D)",
                "Compare 2D Shapes",
                "Compare 3D Shapes",
                "Exit"
            };
            
            int choice = JOptionPane.showOptionDialog(
                null,
                "Shape Calculator - Choose an option:",
                "Shape Calculator",
                JOptionPane.DEFAULT_OPTION,
                JOptionPane.INFORMATION_MESSAGE,
                null,
                options,
                options[0]
            );
            
            if (choice == -1 || choice == 7) {
                JOptionPane.showMessageDialog(null, "Thank you for using Shape Calculator!");
                break;
            }
            
            switch (choice) {
                case 0: create2DShape(); break;
                case 1: create3DShape(); break;
                case 2: viewAllShapes(); break;
                case 3: calculateTotalArea(); break;
                case 4: calculateTotalVolume(); break;
                case 5: compare2DShapes(); break;
                case 6: compare3DShapes(); break;
            }
        }
    }
    
    private void create2DShape() {
        String[] shapeTypes = {"Circle", "Rectangle", "Triangle", "Square", "Trapezoid"};
        String choice = (String) JOptionPane.showInputDialog(
            null,
            "Select 2D Shape Type:",
            "Create 2D Shape",
            JOptionPane.QUESTION_MESSAGE,
            null,
            shapeTypes,
            shapeTypes[0]
        );
        
        if (choice == null) return;
        
        try {
            switch (choice) {
                case "Circle":
                    double radius = getDoubleInput("Enter radius:");
                    shapes2D.add(new Circle(radius));
                    break;
                case "Rectangle":
                    double length = getDoubleInput("Enter length:");
                    double width = getDoubleInput("Enter width:");
                    shapes2D.add(new Rectangle(length, width));
                    break;
                case "Triangle":
                    double base = getDoubleInput("Enter base:");
                    double height = getDoubleInput("Enter height:");
                    shapes2D.add(new Triangle(base, height));
                    break;
                case "Square":
                    double side = getDoubleInput("Enter side length:");
                    shapes2D.add(new Square(side));
                    break;
                case "Trapezoid":
                    double base1 = getDoubleInput("Enter first base:");
                    double base2 = getDoubleInput("Enter second base:");
                    double trapHeight = getDoubleInput("Enter height:");
                    shapes2D.add(new Trapezoid(base1, base2, trapHeight));
                    break;
            }
            JOptionPane.showMessageDialog(null, choice + " created successfully!");
        } catch (Exception e) {
            JOptionPane.showMessageDialog(null, "Error creating shape: " + e.getMessage());
        }
    }
    
    private void create3DShape() {
        String[] shapeTypes = {"Sphere", "Cube", "Cylinder", "Cone", "Rectangular Prism"};
        String choice = (String) JOptionPane.showInputDialog(
            null,
            "Select 3D Shape Type:",
            "Create 3D Shape",
            JOptionPane.QUESTION_MESSAGE,
            null,
            shapeTypes,
            shapeTypes[0]
        );
        
        if (choice == null) return;
        
        try {
            switch (choice) {
                case "Sphere":
                    double radius = getDoubleInput("Enter radius:");
                    shapes3D.add(new Sphere(radius));
                    break;
                case "Cube":
                    double side = getDoubleInput("Enter side length:");
                    shapes3D.add(new Cube(side));
                    break;
                case "Cylinder":
                    double cylRadius = getDoubleInput("Enter radius:");
                    double cylHeight = getDoubleInput("Enter height:");
                    shapes3D.add(new Cylinder(cylRadius, cylHeight));
                    break;
                case "Cone":
                    double coneRadius = getDoubleInput("Enter radius:");
                    double coneHeight = getDoubleInput("Enter height:");
                    shapes3D.add(new Cone(coneRadius, coneHeight));
                    break;
                case "Rectangular Prism":
                    double length = getDoubleInput("Enter length:");
                    double width = getDoubleInput("Enter width:");
                    double height = getDoubleInput("Enter height:");
                    shapes3D.add(new RectangularPrism(length, width, height));
                    break;
            }
            JOptionPane.showMessageDialog(null, choice + " created successfully!");
        } catch (Exception e) {
            JOptionPane.showMessageDialog(null, "Error creating shape: " + e.getMessage());
        }
    }
    
    private void viewAllShapes() {
        StringBuilder sb = new StringBuilder();
        sb.append("=== 2D SHAPES ===\n");
        if (shapes2D.isEmpty()) {
            sb.append("No 2D shapes created yet.\n");
        } else {
            for (int i = 0; i < shapes2D.size(); i++) {
                sb.append((i + 1) + ". " + shapes2D.get(i).getInfo() + "\n");
            }
        }
        
        sb.append("\n=== 3D SHAPES ===\n");
        if (shapes3D.isEmpty()) {
            sb.append("No 3D shapes created yet.\n");
        } else {
            for (int i = 0; i < shapes3D.size(); i++) {
                sb.append((i + 1) + ". " + shapes3D.get(i).getInfo() + "\n");
            }
        }
        
        JOptionPane.showMessageDialog(null, sb.toString(), "All Shapes", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void calculateTotalArea() {
        if (shapes2D.isEmpty()) {
            JOptionPane.showMessageDialog(null, "No 2D shapes to calculate!");
            return;
        }
        
        double totalArea = 0;
        for (Shape2D shape : shapes2D) {
            totalArea += shape.calculateArea();
        }
        
        JOptionPane.showMessageDialog(null, 
            "Total Area of all 2D shapes: " + df.format(totalArea) + " square units",
            "Total Area",
            JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void calculateTotalVolume() {
        if (shapes3D.isEmpty()) {
            JOptionPane.showMessageDialog(null, "No 3D shapes to calculate!");
            return;
        }
        
        double totalVolume = 0;
        for (Shape3D shape : shapes3D) {
            totalVolume += shape.calculateVolume();
        }
        
        JOptionPane.showMessageDialog(null, 
            "Total Volume of all 3D shapes: " + df.format(totalVolume) + " cubic units",
            "Total Volume",
            JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void compare2DShapes() {
        if (shapes2D.size() < 2) {
            JOptionPane.showMessageDialog(null, "Need at least 2 shapes to compare!");
            return;
        }
        
        Shape2D largest = shapes2D.get(0);
        Shape2D smallest = shapes2D.get(0);
        
        for (Shape2D shape : shapes2D) {
            if (shape.calculateArea() > largest.calculateArea()) {
                largest = shape;
            }
            if (shape.calculateArea() < smallest.calculateArea()) {
                smallest = shape;
            }
        }
        
        String message = "Largest: " + largest.getInfo() + "\n" +
                        "Smallest: " + smallest.getInfo();
        
        JOptionPane.showMessageDialog(null, message, "2D Shape Comparison", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private void compare3DShapes() {
        if (shapes3D.size() < 2) {
            JOptionPane.showMessageDialog(null, "Need at least 2 shapes to compare!");
            return;
        }
        
        Shape3D largest = shapes3D.get(0);
        Shape3D smallest = shapes3D.get(0);
        
        for (Shape3D shape : shapes3D) {
            if (shape.calculateVolume() > largest.calculateVolume()) {
                largest = shape;
            }
            if (shape.calculateVolume() < smallest.calculateVolume()) {
                smallest = shape;
            }
        }
        
        String message = "Largest Volume: " + largest.getInfo() + "\n" +
                        "Smallest Volume: " + smallest.getInfo();
        
        JOptionPane.showMessageDialog(null, message, "3D Shape Comparison", JOptionPane.INFORMATION_MESSAGE);
    }
    
    private double getDoubleInput(String prompt) {
        String input = JOptionPane.showInputDialog(prompt);
        if (input == null) throw new RuntimeException("Input cancelled");
        return Double.parseDouble(input);
    }
    
    public static void main(String[] args) {
        ShapeCalculator calculator = new ShapeCalculator();
        calculator.run();
    }
}