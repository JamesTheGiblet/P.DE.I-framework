import json
import os
import urllib.request
import urllib.error

# Configuration Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(BASE_DIR, 'pdei_core', 'learning_manifest.json')

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Manifest not found at {path}")
        return None

def fetch_github_repos(username, token=None):
    """
    Fetches all public repositories for a user using GitHub API.
    Uses urllib to avoid external dependencies like 'requests'.
    """
    repos = []
    page = 1
    
    print(f"📡 Connecting to GitHub API for user: {username}...")
    
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "PDEI-Framework-Sync")
        
        if token:
            req.add_header("Authorization", f"token {token}")
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
                if not data:
                    break # No more pages
                
                for repo in data:
                    # Skip forks if you only want your original code
                    if not repo.get('fork', False):
                        entry = {
                            "alias": repo['name'],
                            "url": repo['ssh_url'], # Uses SSH format (git@github.com...)
                            "branch": repo['default_branch'],
                            "focus": ["coding_patterns", "commit_message_style"]
                        }
                        repos.append(entry)
                
                print(f"   - Page {page}: Found {len(data)} repositories...")
                page += 1
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("❌ Error: API Rate Limit Exceeded. Try setting GITHUB_TOKEN env var.")
            elif e.code == 404:
                print(f"❌ Error: User '{username}' not found.")
            else:
                print(f"❌ Error: {e}")
            return []
            
    return repos

def update_manifest(new_repos):
    manifest = load_json(MANIFEST_PATH)
    if not manifest: return

    old_count = len(manifest.get('learning_targets', {}).get('repositories', []))
    
    # Update only the repositories list, keep local_folders intact
    manifest['learning_targets']['repositories'] = new_repos
    
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"✅ Manifest Updated: Replaced {old_count} repos with {len(new_repos)} new sources.")

if __name__ == "__main__":
    user = input("Enter GitHub Username: ").strip()
    token = os.environ.get("GITHUB_TOKEN") # Optional: Set this env var for private repos
    
    found_repos = fetch_github_repos(user, token)
    
    if found_repos:
        update_manifest(found_repos)
    else:
        print("⚠️  No repositories found or sync failed.")