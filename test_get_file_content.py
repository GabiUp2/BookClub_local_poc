from calculator.functions.get_file_content import get_file_content

try:
    get_file_content("calculator", "lorem.txt")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_file_content("calculator", "main.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_file_content("calculator", "pkg/calculator.py")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_file_content("calculator", "/bin/cat")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_file_content("calculator", "pkg/does_not_exist.py")
except ValueError as e:
    print(f"Error: {e}")
