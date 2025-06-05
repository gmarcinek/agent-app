from .generate_code import GenerateCodeCommand
from .write_file import WriteFileCommand
from .run_script import RunScriptCommand
from .make_directory import MakeDirectoryCommand
from .change_directory import ChangeDirectoryCommand
from .delete import DeleteCommand
from .patch_file import PatchFileCommand

def get_command(command_type: str, step: dict):
    if command_type == "generate_code":
        return GenerateCodeCommand(step)
    elif command_type == "patch_file":
        return PatchFileCommand(step)
    elif command_type == "write_file":
        return WriteFileCommand(step)
    elif command_type == "run_script":
        return RunScriptCommand(step)
    elif command_type == "mkdir":
        return MakeDirectoryCommand(step)
    elif command_type == "cd":
        return ChangeDirectoryCommand(step)
    elif command_type == "delete":
        return DeleteCommand(step)
    raise ValueError(f"Nieznany typ komendy: {command_type}")