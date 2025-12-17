from calculator.functions.write_file import write_file

try:
    write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
except ValueError as e:
    print(f"Error: {e}")

try:
    write_file("calculator", "pkg/morelorem.txt", "lorem ipsum dolor sit amet")
except ValueError as e:
    print(f"Error: {e}")

try:
    write_file("calculator", "/tmp/temp.txt", "this should not be allowed")
except ValueError as e:
    print(f"Error: {e}")
