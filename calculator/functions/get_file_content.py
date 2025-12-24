import os
from config import MAX_CHARACTERS
from google.genai import types


schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description=f"Gets up to {MAX_CHARACTERS} of the content of a file, trunates if there is more, file name relative to the working directory",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_name": types.Schema(
                type=types.Type.STRING,
                description="File name to get content from, relative to the working directory",
            ),
        },
    ),
)

def get_file_content(working_directory, file_name):
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_file = os.path.normpath(os.path.join(working_directory, file_name))

        target_file_abs = os.path.abspath(target_file)

        if not os.path.isfile(target_file_abs):
            raise ValueError(f'Error: "{target_file_abs}" is not a file')

        is_target_file_valid = (
            os.path.commonprefix([working_dir_abs, target_file_abs]) == working_dir_abs
        )

        if not is_target_file_valid:
            raise ValueError(
                f'Error: Cannot list "{file_name}" as it is outside the permitted working directory'
            )

        with open(target_file_abs, "r") as file:
            file_content = file.read(MAX_CHARACTERS)
            if len(file_content) == MAX_CHARACTERS:
                file_content += f'[...File "{target_file}" truncated at {MAX_CHARACTERS} characters]'
            print(file_content)
    except Exception as e:
        raise ValueError(f"Error: {e}")
