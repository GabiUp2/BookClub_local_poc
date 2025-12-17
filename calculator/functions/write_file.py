import os


def write_file(working_directory, file_path, content):
    try:
        target_dir = os.path.normpath(os.path.join(working_directory, file_path))

        working_dir_abs = os.path.abspath(target_dir)

        is_target_dir_valid = (
            os.path.commonprefix([working_dir_abs, target_dir]) == working_dir_abs
        )

        if not is_target_dir_valid:
            raise ValueError(
                f'Error: Cannot list "{file_path}" as it is outside the permitted working directory'
            )

        if not os.path.exists(working_dir_abs):
            os.makedirs(working_dir_abs, exist_ok=True)

        with open(working_dir_abs, "w") as file:
            file.write(content)

        print(
            f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
        )

    except Exception as e:
        raise ValueError(f"Error: {e}")
