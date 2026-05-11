import requests
import json
import toml

def create_issue():
    try:
        secrets = toml.load("secrets.toml")
        token = secrets.get("GITHUN_TOKEN") or secrets.get("GITHUB_TOKEN")
        repo = secrets.get("REPO_NAME")
        
        if not token or not repo:
            print("Missing token or repo in secrets.toml")
            return

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        issue_data = {
            "title": "Add support for more PLC series (iQ-F, L, FX) and 4E frame",
            "body": """The user wants to expand the supported PLC series and implement 4E frame support.

### Tasks:
- [ ] Update UI to include more series in the dropdown (iQ-F, L, FX, etc.)
- [ ] Implement 4E frame support in `mc_protocol.py`
- [ ] Fix `station_no` index bug in `mc_protocol.py`
- [ ] Update `PlcSimulator` to select protocol based on series
- [ ] Update documentation (Done)

Labels: enhancement, documentation""",
            "labels": ["enhancement", "documentation"]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(issue_data))
        
        if response.status_code == 201:
            print(f"Issue created successfully: {response.json().get('html_url')}")
        else:
            print(f"Failed to create issue: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_issue()
