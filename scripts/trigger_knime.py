import subprocess
import time

def run_knime_bypass():
    print("🚀 Starting KNIME Workflow in Bypass UI Mode...")
    
    # 1. Apne KNIME ka exact path
    knime_path = r"C:\Users\HP\AppData\Local\Programs\KNIME\knime.exe"
    
    # 2. Apne workflow folder ka path
    workflow_path = r"C:\Users\HP\Downloads\job_market_project\Job_Market_Final_Pipeline" # Apne mutabiq verify karlein
    
    # 3. Direct execution command (bina batch application extension ke)
    command = [
        knime_path,
        "-nosplash",
        "-nosave",
        f"-workflowDir={workflow_path}",
        "-reset",
        "-consoleLog"
    ]
    
    try:
        # Hamein background me process chalana hai bina wait kiye block hone ka
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print("⏳ Pipeline running in background. Waiting 15 seconds for data writing...")
        time.sleep(15) # KNIME ko data save karne ke liye thoda time de rahe hain
        
        print("✅ KNIME Triggered successfully via Bypass! Check your data/processed folder.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_knime_bypass();