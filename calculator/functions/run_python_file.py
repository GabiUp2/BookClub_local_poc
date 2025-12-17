import os
import subprocess

def run_python_file(working_directory, file_path, args=None):
    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, file_path))

    is_target_dir_valid = (
        os.path.commonprefix([working_dir_abs, target_dir]) == working_dir_abs
    )

    if not is_target_dir_valid:
        raise ValueError(
            f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        )

    if not os.path.isfile(target_dir):
        raise ValueError(f'Error: "{file_path}" does not exist or is not a regular file')

    if not target_dir.endswith(".py"):
        raise ValueError(f'Error: "{file_path}" is not a Python file')

    command = ["python", os.path.abspath(target_dir)]
    if args:
        command.extend(args)

    try:
        
        result = subprocess.run(command, cwd=os.path.dirname(target_dir), timeout=30, check=True, capture_output=True, text=True)
        stdout = result.stdout
        stderr = result.stderr

        output = ""
        if result.returncode != 0:
            output += f"Process exited with code {result.returncode}. "
        elif not stdout and not stderr:
            output += "No output produced."
        else:
            output += f"STDOUT: {stdout}\nSTDERR: {stderr}"

        print(output)
        
    except Exception as e:
        raise ValueError(f"Error: executing Python file: {e}")
