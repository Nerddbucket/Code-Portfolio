import java.util.ArrayList;
import java.util.Scanner;
class Task {
    String name;
    boolean isCompleted;
    Task(String name) {
        this.name = name;
        this.isCompleted = false;
    }
    void markComplete() {
        isCompleted = true;
    }
    @Override
    public String toString() {
        return name + (isCompleted ? " [Completed]" : "");
    }
}
public class To_Do_List {
    public static void main(String[] args) {
        ArrayList<Task> GETSHITDONE = new ArrayList<>();
        Scanner BANDZ = new Scanner(System.in);
        while (true) {
            System.out.println("\nTo-Do List:");
            System.out.println("1. Add Task");
            System.out.println("2. Remove Task");
            System.out.println("3. View Tasks");
            System.out.println("4. Mark Task Completed");
            System.out.println("5. Exit");
            System.out.print("Choose an option: ");
            int choice = BANDZ.nextInt();
            BANDZ.nextLine();
            switch (choice) {
                case 1: // Add Task
                    System.out.print("Enter task name: ");
                    String taskName = BANDZ.nextLine();
                    GETSHITDONE.add(new Task(taskName));
                    System.out.println("Task added: " + taskName);
                    break;
                    case 2: // Remove Task
                        System.out.print("Enter task number to remove: ");
                        int removeIndex = BANDZ.nextInt();
                        if (removeIndex >= 0 && removeIndex < GETSHITDONE.size()) {
                            Task removedTask = GETSHITDONE.remove(removeIndex);
                            System.out.println("Removed task: " + removedTask.name);
                        } else {
                            System.out.println("Invalid task number.");
                        }
                        break;
                            case 3: // View Tasks
                            if (GETSHITDONE.isEmpty()) {
                                System.out.println("No tasks available.");
                            } else {
                                System.out.println("Tasks:");
                                for (int i = 0; i < GETSHITDONE.size(); i++) {
                                    System.out.println(i + ": " + GETSHITDONE.get(i));
                                }
                            }
                            break;
                                case 4: // Mark Task Completed
                                System.out.print("Enter task number to mark as completed: ");
                                int completeIndex = BANDZ.nextInt();
                                if (completeIndex >= 0 && completeIndex < GETSHITDONE.size()) {
                                    Task taskToComplete = GETSHITDONE.get(completeIndex);
                                    taskToComplete.markComplete();
                                    System.out.println("Marked task as completed: " + taskToComplete.name);
                                } else {
                                    System.out.println("Invalid task number.");
                                }
                                break;
                                        case 5: // Exit
                                        System.out.println("Exiting...");
                                        BANDZ.close();
                                        return;
                    default:
                    System.out.println("Invalid choice. Please try again.");
                    break;
            }
        }
    }
}