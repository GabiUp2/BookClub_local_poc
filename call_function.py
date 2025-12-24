from google.genai import types
from calculator.functions.get_files_info import schema_get_files_info, get_files_info
from calculator.functions.get_file_content import (
    schema_get_file_content,
    get_file_content,
)
from calculator.functions.run_python_file import schema_run_python_file, run_python_file
from calculator.functions.write_file import schema_write_file, write_file

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ],
)


def call_function(function_call: types.FunctionCall, verbose=False):
    if verbose:
        print(f"Calling function: {function_call.name}({function_call.args})")
    else:
        print(f" - Calling function: {function_call.name}")

    function_call.args["working_directory"] = "./calculator"

    matching_dict = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "run_python_file": run_python_file,
        "write_file": write_file,
    }

    try:
        for function_name, function in matching_dict.items():
            if function_name == function_call.name:
                function_result = function(**function_call.args)
                return types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name=function_call.name,
                            response={"result": function_result},
                        )
                    ],
                )

    except KeyError:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call.name,
                    args=function_call.args,
                    response={"error": f"Unknown function: {function_call.name}"},
                )
            ],
        )
