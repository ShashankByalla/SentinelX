# run_test_playbooks.py
import yaml
import subprocess
import requests

# Set TEST_MODE=True for testing without actually restarting containers
TEST_MODE = True

playbooks = [
    "pb-001-restart-app.yaml",
    "pb-003-high-cpu.yaml",
    "pb-021-db-timeout.yaml"
]

for pb_file in playbooks:
    path = f"playbooks/{pb_file}"
    print(f"\n=== Running {pb_file} ===")
    
    with open(path) as f:
        pb = yaml.safe_load(f)

    # Run actions
    for action in pb.get("actions", []):
        cmd_type = action.get("type")
        
        if cmd_type == "shell":
            command = action.get("command")
            if command:
                if TEST_MODE:
                    print("TEST_MODE:", command.replace("docker restart", "echo Simulating"))
                    subprocess.run(f'echo "Simulating: {command}"', shell=True)
                else:
                    print("Executing:", command)
                    subprocess.run(command, shell=True)
        
        elif cmd_type == "http_post":
            url = action.get("url")
            if url:
                if TEST_MODE:
                    print(f"TEST_MODE: Simulating POST request to {url}")
                else:
                    try:
                        response = requests.post(url)
                        print(f"POST {url} → {response.status_code}")
                    except Exception as e:
                        print(f"Error POST {url}: {e}")

    # Run verification
    for verify in pb.get("verify", []):
        url = verify.get("url")
        expect_status = verify.get("expect_status", 200)
        try:
            response = requests.get(url)
            status = response.status_code
            print(f"Verifying {url}: got {status}, expected {expect_status}")
        except Exception as e:
            print(f"Verification failed for {url}: {e}")
