import java.util.Scanner;
public class M6Project_dorleus {
    private static final Scanner SCANNER = new Scanner(System.in);


    public static void main(String[] args)
    {
    runProgram();
    }
    public static void runProgram()
    {
        System.out.println("Method Project");
        String keep_going = "yes";
        while(keep_going.equalsIgnoreCase("yes"))
        {
                if (!displayMenu()) {
                        break;
                }
                System.out.println();
                System.out.print("Do you want to run the program again? Enter yes or no: ");
                keep_going = SCANNER.next();
                SCANNER.nextLine();
                System.out.println();
        }
        System.out.println("Program has terminated!");
        SCANNER.close();
}
public static boolean displayMenu()
        {
System.out.println();
System.out.println("Menu");
System.out.println();
    // give your programs better names
System.out.println("1) M6HW1: ");
System.out.println("2) M6HW2: ");
System.out.println("3) M6HW3: ");
System.out.println("4) Exit: ");
System.out.println();
System.out.print ( "Selection: " );
    // change the cases below to better reflect the programs you are running
        int selection = SCANNER.nextInt();
        SCANNER.nextLine();
        switch ( selection )
        {
        case 1:
                getM6HW1();
                return true;
        case 2:
                getM6HW2();
                System.out.println ( "You picked M6HW2" );
                return true;
        case 3:
                getM6HW3();
                System.out.println ( "You picked M6HW3" );
                return true;
        case 4:
                System.out.println("");
                System.out.println ( "Exiting the program" );
                return false;
        default:
                System.out.println("");
                System.out.println ( "Unrecognized option..Try again" );
                System.out.println("");
                return true;
        }

}
    // new methods containg the other programs should go here
    // I completed the first method structure for you
    // the 2nd and third method structure will follow the same pattern // just copy and paste the code
    // You will need to add your code from M6HW1 in the method

        public static void getM6HW1()
        {
                System.out.println("");
                System.out.println("");
                System.out.println ( "You picked M6HW1" );
                System.out.println ( "" );
                // add your code here for M6HW1
        System.out.println("Enter the name of the employee: ");
        String employeeName = SCANNER.nextLine();
        
        System.out.print("Enter your hourly pay rate: ");
        double payRate = SCANNER.nextDouble();

        System.out.print("Enter the number of hours worked: ");
        double hoursWorked = SCANNER.nextDouble();
        SCANNER.nextLine();

        
        double grossPay = payRate * hoursWorked;

        
        System.out.println("\n--- Employee Payroll Information ---");
        System.out.println("Employee Name: " + employeeName);
        System.out.println("Pay Rate: $" + String.format("%.2f", payRate));
        System.out.println("Hours Worked: " + hoursWorked);
        System.out.println("Gross Pay: $" + String.format("%.2f", grossPay));
        }



        public static void getM6HW2()
        {
                System.out.println("");
                System.out.println("");
                System.out.println ( "You picked M6HW2" );
                System.out.println ( "" );
                
                        double perGallonrate= .20;
                        double baseFee= 50.00;
                        double totalCharge,previousReading,currentReading,waterUsed;
                        String homeownersName;
                
                
                        System.out.println("Enter the name of the homeowner: ");
                        homeownersName = SCANNER.nextLine();
                        System.out.println("Enter Previos water meter reading: ");
                        previousReading = SCANNER.nextDouble();
                        System.out.println("Enter current water meter reading:");
                        currentReading = SCANNER.nextDouble();
                        SCANNER.nextLine();
                
                        waterUsed= currentReading - previousReading;
                
                        totalCharge= baseFee + (waterUsed * perGallonrate);
                
                        System.out.println("\n----Water Bill----");
                        System.out.printf("Monthly Charge: $%.2f\n", totalCharge);
                        System.out.println("Homeowner: " + homeownersName);
                        System.out.println("Previos water meter reading: " + previousReading +" gallons");
                        System.out.println("Water used: " + waterUsed + " gallons");
                        System.out.println("Current water meter reading: " + currentReading + " gallons");
                }
                
                public static void getM6HW3()
                {
                
                System.out.println("");
                System.out.println("");
                System.out.println ( "You picked M6HW3" );
                System.out.println ( "" );
                
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
        salesPerson = SCANNER.nextLine();

        System.out.print("Enter monthly salary: ");
        monthlySalary = SCANNER.nextDouble();
            // Get weekly sales
                for (int i = 0; i < 4; i++) {
                System.out.printf("Enter widgets sold in week %d: ", i + 1);
                weeklySales[i] = SCANNER.nextInt();
                totalSold += weeklySales[i];
                }
            // Get weekly returns
                for (int i = 0; i < 4; i++) {
                System.out.printf("Enter widgets returned in week %d: ", i + 1);
                weeklyReturns[i] = SCANNER.nextInt();
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
            commission = widgetSales_amount * commRate;
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
            SCANNER.nextLine(); // Clear the newline
        runAgain = SCANNER.nextLine().trim().toLowerCase();
        } while (runAgain.equals("yes") || runAgain.equals("y"));

        System.out.println("Program ended. Goodbye!");
        
        
        
        }
}