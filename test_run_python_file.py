from calculator.functions.run_python_file import run_python_file

try:
    run_python_file("calculator", "main.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    run_python_file("calculator", "main.py", ["3 + 5"])
except ValueError as e:
    print(f"Error: {e}")

try:
    run_python_file("calculator", "tests.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    run_python_file("calculator", "../main.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    run_python_file("calculator", "nonexistent.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    run_python_file("calculator", "lorem.txt")
except ValueError as e:
    print(f"Error: {e}")
