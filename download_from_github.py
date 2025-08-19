import requests

def get_releases_from_github(owner: str, repo: str) -> None:
    url = f"https://api.github.com/repos/ {owner}/{repo}/releases"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PythonScript/1.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        releases = response.json()
        for release in releases:
            print(f"Tag: {release['tag_name']}, Name: {release['name']}, Published at: {release['published_at']}")
    else:
        print("Failed to fetch releases:", response.status_code, response.text)
