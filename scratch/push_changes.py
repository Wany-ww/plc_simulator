import toml
import subprocess
import os

def push_to_github():
    try:
        secrets = toml.load("secrets.toml")
        token = secrets.get("GITHUN_TOKEN") or secrets.get("GITHUB_TOKEN")
        repo = secrets.get("REPO_NAME")
        
        if not token or not repo:
            print("Missing token or repo in secrets.toml")
            return

        # Use token in URL
        remote_url = f"https://{token}@github.com/{repo}.git"
        
        # Set remote URL temporarily or just push to it
        print(f"Pushing to {repo}...")
        result = subprocess.run(["git", "push", remote_url, "main"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Push successful!")
            print(result.stdout)
        else:
            print("Push failed!")
            # Hide token from error message if possible
            error = result.stderr.replace(token, "********")
            print(error)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    push_to_github()
