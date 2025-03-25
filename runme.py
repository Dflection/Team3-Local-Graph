import os
import sys
import multiprocessing
import streamlit.web.bootstrap

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    # Determine the folder where this script is located.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change the current working directory to the script folder.
    os.chdir(base_dir)
    
    # Build the absolute path to MAIN.py, which is in the same directory.
    app_path = os.path.join(base_dir, "MAIN.py")
    
    # Set sys.argv to mimic running: streamlit run MAIN.py --server.port 8501
    sys.argv = ["streamlit", "run", app_path, "--server.port", "8501"]
    
    # Launch the Streamlit app.
    streamlit.web.bootstrap.run(app_path, False, sys.argv, {})

