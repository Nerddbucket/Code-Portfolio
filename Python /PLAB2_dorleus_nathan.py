def run_once():
    try:
        user_input = input("Enter an integer: ").strip()
        number = int(user_input)
    except ValueError:
        print("Invalid input. Please enter a whole number (integer).")
        return

    if number < 0:
        print("Cannot accept negative values.")
        return

    print(f"Multiplication table for {number} (1 to 12):")
    for i in range(1, 13):
        print(f"{number} x {i} = {number * i}")


def main():
    while True:
        run_once()
        again = input("Do you want to run it again? (yes/no): ").strip().lower()
        if again == "yes":
            continue
        if again == "no":
            print("Goodbye!")
            break
        # For any other response, default to ending gracefully
        print("This program does not accecpt Miscellaneous values, Sorry.")
        break


if __name__ == "__main__":
    main()


