//Nathan Dorleus
//M6HW3
//this program calculates the average score and grade of a student based on user input using a loop. will use in mod 6 for modules.
import java.util.Scanner;

public class M5HW2_dorleus {

    public static void main(String[] args) {
        Scanner Bandz = new Scanner(System.in);
        String salesPerson;
        double widget_price = 4.79;
        String runAgain;

        do {
            int[] weeklySales = new int[4];
            int[] weeklyReturns = new int[4];
            int totalSold = 0, totalReturned = 0;
            int netWidgetsales;
            double widgetSales_amount, commRate, commission;
            double monthlySalary=500.00;

            // Get salesperson's name and base monthly salary
            System.out.print("Enter the name of the salesperson: ");
            salesPerson = Bandz.nextLine();

            System.out.print("Enter monthly salary: ");
            monthlySalary = Bandz.nextDouble();

            // Get weekly sales
            for (int i = 0; i < 4; i++) {
                System.out.printf("Enter widgets sold in week %d: ", i + 1);
                weeklySales[i] = Bandz.nextInt();
                totalSold += weeklySales[i];
            }

            // Get weekly returns
            for (int i = 0; i < 4; i++) {
                System.out.printf("Enter widgets returned in week %d: ", i + 1);
                weeklyReturns[i] = Bandz.nextInt();
                totalReturned += weeklyReturns[i];
            }

            // Calculate net widgets sold and widget sales amount
            netWidgetsales = totalSold - totalReturned;
            widgetSales_amount = netWidgetsales * widget_price;

            // Determine commission rate
            if (netWidgetsales <= 100) {
                commRate = 0.10;
            } else if (netWidgetsales <= 199) {
                commRate = 0.15;
            } else if (netWidgetsales <= 299) {
                commRate = 0.20;
            } else {
                commRate = 0.25;
            }

            // Calculate commission and total monthly pay
            commission = widgetSales_amount * 0.10;
            double monthly_pay = monthlySalary + commission;

            // Output results
            System.out.printf("\nSalesperson: %s\n", salesPerson);
            System.out.printf("Total Widgets Sold: %d\n", totalSold);
            System.out.printf("Total Widgets Returned: %d\n", totalReturned);
            System.out.printf("Net Widgets Sold: %d\n", netWidgetsales);
            System.out.printf("Widget Sales Amount: $%.2f\n", widgetSales_amount);
            System.out.printf("Commission Rate: %.2f%%\n", commRate * 100);
            System.out.printf("Commission Earned: $%.2f\n", commission);
            System.out.printf("Monthly Salary: $%.2f\n", monthlySalary);
            System.out.printf("Total Monthly Pay: $%.2f\n", monthly_pay);

            // Ask if the user wants to run the program again
            System.out.print("\nWould you like to run the program again? (yes/no): ");
            Bandz.nextLine(); // Clear the newline
            runAgain = Bandz.nextLine().trim().toLowerCase();
        } while (runAgain.equals("yes") || runAgain.equals("y"));

        System.out.println("Program ended. Goodbye!");

        
    }
}