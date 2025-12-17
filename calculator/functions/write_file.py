import os


def write_file(working_directory, file_path, content):
    try:
        if os.path.isabs(file_path):
            raise ValueError(
                f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
            )

        working_dir_abs = os.path.abspath(working_directory)
        target_path = os.path.normpath(os.path.join(working_dir_abs, file_path))

        is_target_path_valid = (
            os.path.commonpath([working_dir_abs, target_path]) == working_dir_abs
        )

        if not is_target_path_valid:
            raise ValueError(
                f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
            )

        target_parent = os.path.dirname(target_path)
        if target_parent:
            os.makedirs(target_parent, exist_ok=True)

        with open(target_path, "w") as file:
            file.write(content)

        print(
            f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
        )

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error: {e}")
