import subprocess
import time
import os
from pathlib import Path

# Optional: activate virtualenv if needed
# VENV_ACTIVATE = Path("./.venv/Scripts/activate")
# os.system(f"call {VENV_ACTIVATE}")

# Paths to scripts
scripts = {
    "simulator": "user_report_simulator.py",
    "consumer": "kafka_to_mongo_consumer.py",
    "spark": "spark_stream_processor.py"
}

processes = {}

try:
    print("🚀 Launching AlertCircle system...\n")

    for name, script in scripts.items():
        print(f"🔹 Starting {name}...")
        processes[name] = subprocess.Popen(
            ["python", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        time.sleep(1)  # small delay between launches

    print("\n✅ All components started. Press Ctrl+C to stop.\n")

    # Stream the output of each process
    while True:
        for name, process in processes.items():
            output = process.stdout.readline()
            if output:
                print(f"[{name.upper()}] {output.strip()}")

except KeyboardInterrupt:
    print("\n🛑 Stopping all processes...")
    for name, process in processes.items():
        process.terminate()
        print(f"❌ {name} stopped.")
    print("✅ System shutdown complete.")
