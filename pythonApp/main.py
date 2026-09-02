import math_engine


def main():
    print("Successfully imported C++ math_engine!")

    result = math_engine.test_connection(5, 7)

    print(f"C++ test_connection(5, 7) returned: {result}")

    if result == 12:
        print("Bridge is fully operational.")


if __name__ == "__main__":
    main()

