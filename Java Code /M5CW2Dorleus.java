import java.util.Scanner;

public class M5CW2Dorleus {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int score;
        int totalScore = 0;
        int count = 5; // Number of scores to enter

        for (int i = 1; i <= count; i++) {
            do {
                System.out.print("Enter score " + i + " (between 0-100): ");
                score = scanner.nextInt();
                
                if (score < 0 || score > 100) {
                    System.out.println("Invalid score. Please enter a valid score between 0 and 100.");
                }
            } while (score < 0 || score > 100);
            
            totalScore += score;
        }
        
        // Calculate average
        int average = totalScore / count;
        
        // Determine the grade
        char grade;
        if (average >= 90) {
            grade = 'A';
        } else if (average >= 80) {
            grade = 'B';
        } else if (average >= 70) {
            grade = 'C';
        } else if (average >= 60) {
            grade = 'D';
        } else {
            grade = 'F';
        }
        
        // Display the result
        System.out.println("The student's average score is: " + average);
        System.out.println("The student's grade is: " + grade);
        
        scanner.close();
    }
}