
# The Local Graph, RUN_LOCAL_GRAPH file - by Chase Varvayanis
# Handles installation of dependencies and launches Streamlit webapp
# 3-25-2025
# Code Linted with Flake8, Spellchecked with Code Spell Checker, and general Cleanup and formatting with ChatGPT

import multiprocessing
import subprocess
import sys
import os


def install_package(package_name, pip_name=None):
    """
    Installs a package using pip. Optionally, pip_name can be provided if the pip
    package name differs from the module name.
    """
    pip_name = pip_name or package_name
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        print(f"Successfully installed {package_name} (pip package: {pip_name}).\n")
    except subprocess.CalledProcessError:
        print(f"Error installing {package_name}. Please check the package name or your environment.\n")


def install_dependencies():
    # List of dependencies that are available on PyPI
    # Format: (module name, pip package name)
    packages_to_install = [
        ("streamlit", "streamlit"),
        ("folium", "folium"),
        ("streamlit_folium", "streamlit-folium"),
        ("pandas", "pandas"),
        ("openpyxl", "openpyxl"),
    ]

    for module_name, pip_name in packages_to_install:
        install_package(module_name, pip_name)


def main():
    # First, install dependencies
    install_dependencies()

    # Import streamlit after installing it
    try:
        import streamlit.web.bootstrap as bootstrap
    except ImportError:
        print("Error: streamlit module not found after installation. Exiting.")
        sys.exit(1)

    # Determine the parent folder
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Change the current working directory to the parent folder.
    os.chdir(base_dir)

    # Build the absolute path to MAIN.py, which is in the same directory.
    app_path = os.path.join(base_dir, "MAIN.py")

    # Set sys.argv to mimic running: streamlit run MAIN.py --server.port 8501
    sys.argv = ["streamlit", "run", app_path, "--server.port", "8501"]

    # Launch the Streamlit app.
    bootstrap.run(app_path, False, sys.argv, {})


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
