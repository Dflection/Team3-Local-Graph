import os
from utilities import path


# creates a function that can be called to run the gui streamlit map
def generate_map():
    os.system(f"python -m streamlit run {path('gui_experimental.py')}")


# tells the program to create a gui if this is the main file being called
if __name__ == "__main__":
    generate_map()
