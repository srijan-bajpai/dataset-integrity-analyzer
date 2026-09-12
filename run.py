import os
import sys
import subprocess

def main():
    # Set PYTHONPATH to include the current directory so 'dia' module is found
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    
    # Run Streamlit
    print("Starting Dataset Integrity Analyzer...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], env=env)

if __name__ == "__main__":
    main()
