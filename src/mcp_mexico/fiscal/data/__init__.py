from importlib.resources import files


def read_data_file(name: str) -> str:
    return files(__name__).joinpath(name).read_text(encoding="utf-8")
