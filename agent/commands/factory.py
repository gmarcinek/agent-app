from .generate_code import GenerateCodeCommand

def get_command(name: str, params: dict):
    if name == "generate_code":
        return GenerateCodeCommand(params)
    raise ValueError(f"Nieznana komenda: {name}")
