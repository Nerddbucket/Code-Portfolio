import javax.swing.JOptionPane;

public class JavaCode_areaRec_JOpt_Dorleus_nathan {

    // Rectangle variables
    public static double length;
    public static double width;
    public static double rectArea;

    // Circle variables
    public static double radius;
    public static double circArea;

    public static void main(String[] args) {
        // Ask user which shape they want to calculate
        String choice = JOptionPane.showInputDialog(
            "Choose a shape to calculate area:\n1. Rectangle\n2. Circle");

        if (choice.equals("1")) {
            getLength();
            getWidth();
            displayRectArea();
        } else if (choice.equals("2")) {
            getRadius();
            displayCircArea();
        } else {
            JOptionPane.showMessageDialog(null, "Invalid choice. Please restart the program.");
        }
    }

    //Rectangle methods
        public static void getLength() {
        length = Double.parseDouble(JOptionPane.showInputDialog("Enter the length of the rectangle:"));
    }

        public static void getWidth() {
        width = Double.parseDouble(JOptionPane.showInputDialog("Enter the width of the rectangle:"));
    }

        public static void displayRectArea() {
        rectArea = length * width;
        JOptionPane.showMessageDialog(null, "Area of rectangle is: " + rectArea);
    }

    //Circle methods
            public static void getRadius() {
            radius = Double.parseDouble(JOptionPane.showInputDialog("Enter the radius of the circle:"));
        }

            public static void displayCircArea() {
            circArea = Math.PI * radius * radius;
            JOptionPane.showMessageDialog(null, "Area of circle is: " + circArea);
        }
}
