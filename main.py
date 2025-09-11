import subprocess
import sys
import os

def run_script(script_name):
    """Run another Python script and stream output live"""
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error while running {script_name}: {e}")
        sys.exit(1)

def main():
    print("Step 1: Extracting text from PDFs...")
    run_script("pdf_reader.py")

    print("\nStep 2: Converting text to CSV with AI...")
    run_script("ai.py")

    print("\nWorkflow complete! Check txt_outputs/ and csv_outputs/")

if __name__ == "__main__":
    main()
