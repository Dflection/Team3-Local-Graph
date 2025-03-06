import os


# creates a function called path that allows the computer to find files without specific file paths being coded in.
def path(file_name: str) -> str:
    DIRECTORY_PATH = os.path.dirname(__file__)

    FILE_PATH = os.path.join(DIRECTORY_PATH, file_name)
    return FILE_PATH
