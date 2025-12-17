from calculator.functions.get_files_info import get_files_info

try:
    get_files_info("calculator", ".")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_files_info("calculator", "pkg")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_files_info("calculator", "/bin")
except ValueError as e:
    print(f"Error: {e}")

try:
    get_files_info("calculator", "../")
except ValueError as e:
    print(f"Error: {e}")
