import os


def get_files_info(working_directory, directory="."):
    working_dir_abs = os.path.abspath(working_directory)
    target_dir = os.path.normpath(os.path.join(working_dir_abs, directory))

    is_target_dir_valid = (
        os.path.commonprefix([working_dir_abs, target_dir]) == working_dir_abs
    )

    if not is_target_dir_valid:
        raise ValueError(
            f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
        )

    try:
        for file_name in os.listdir(target_dir):
            file_path = os.path.join(target_dir, file_name)
            file_size = os.path.getsize(file_path)
            is_dir = os.path.isdir(file_path)
            print(f"{file_name}: file_size={file_size} bytes, is_dir={is_dir}")
    except Exception as e:
        print(f"Error: {e}")

