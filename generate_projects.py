import os
import requests
import json
import re
import base64
import time
from urllib.parse import urljoin, urlparse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
PINNED_REPOS = [
    { "name": "hellwal", "url": "https://github.com/danihek/hellwal" },
    { "name": "oni-keyboard", "url": "https://github.com/danihek/oni-keyboard" },
    { "name": "HellWM", "url": "https://github.com/HellSoftware/HellWM" },
    { "name": "HellCast", "url": "https://github.com/danihek/HellCast" },
    { "name": "dotfiles", "url": "https://github.com/danihek/dotfiles" },
    { "name": "arch-dotfiles", "url": "https://github.com/danihek/arch-dotfiles" },
    { "name": "nixos-config", "url": "https://github.com/danihek/nixos-config" },
    { "name": "hellwal-vim", "url": "https://github.com/danihek/hellwal-vim" },
    { "name": "SnakeNN", "url": "https://github.com/danihek/SnakeNN" },
    { "name": "c-wasm", "url": "https://github.com/danihek/c-wasm" },
    { "name": "obsidian-hellwal", "url": "https://github.com/danihek/obsidian-hellwal" },
    { "name": "zathura-hellwal", "url": "https://github.com/danihek/zathura-hellwal" },
    { "name": "VisSorting", "url": "https://github.com/danihek/VisSorting" },
    { "name": "hellcard", "url": "https://github.com/danihek/hellcard" },
    { "name": "Themecord", "url": "https://github.com/danihek/Themecord" },
]
CUSTOM_IMAGE_CROPPING = {  }
GITHUB_USERNAME = "danihek"
GITHUB_TOKEN = os.getenv('GH_TOKEN')
REPOS_TO_EXCLUDE = {"danihek.xyz", "danihek"}
OUTPUT_DIR = "Projects"
STATS_DIR = os.path.join(OUTPUT_DIR, "stats")
OUTPUT_HTML_PATH = os.path.join(OUTPUT_DIR, "index.html")
TEMPLATE_FILE = "template.html"

# --- PLOTTING STYLE ---
plt.rcParams['font.family'] = 'monospace'
RETRO_COLORS = ['#B83B5E', '#4A4A4A', '#F0A202', '#587B7F', '#D9A1A1', '#2C2C2C']

# --- ROBUST REQUEST HELPER ---
def make_request_with_retries(url, headers=None, retries=1, backoff_factor=1):
    for i in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {i + 1}/{retries}): {e}")
            if i < retries - 1:
                delay = backoff_factor * (2 ** i)
                time.sleep(delay)
    return None

# --- GITHUB API HELPERS ---
def get_api_headers():
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN: headers['Authorization'] = f"token {GITHUB_TOKEN}"
    return headers

def fetch_github_repos():
    print(f"Fetching repos for {GITHUB_USERNAME}...")
    api_url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100"
    response = make_request_with_retries(api_url, headers=get_api_headers())
    if response:
        repos = response.json()
        print(f"Found {len(repos)} repositories.")
        return repos
    return None

# --- NEW, REFACTORED IMAGE FETCHER ---

def _process_image_url(url, repo_data):
    """Internal helper to process a single image URL and return a final, usable source."""
    # Case 1: Private GitHub image. Download and embed as Base64.
    if "private-user-images.githubusercontent.com" in url:
        print(f"    - Processing as private image. Downloading...")
        img_response = make_request_with_retries(url)
        if not img_response: return None
        
        # Reliably get the extension from the URL path
        path = urlparse(url).path
        ext_match = re.search(r'\.(png|jpg|jpeg|gif|svg)$', path, re.IGNORECASE)
        ext = ext_match.group(1) if ext_match else 'png' # Default to png
        mime_type = f"image/{'svg+xml' if ext == 'svg' else ext}"
        
        b64_img_data = base64.b64encode(img_response.content).decode('utf-8')
        return f"data:{mime_type};base64,{b64_img_data}"

    # Case 2: GitHub "blob" link. Convert to raw link.
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    # Case 3: Relative URL. Make it absolute.
    if not url.startswith(('http://', 'https://')):
        base_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{repo_data['name']}/{repo_data['default_branch']}/"
        return urljoin(base_url, url)

    # Case 4: It's a standard, direct URL. Use as is.
    return url

def fetch_readme_and_image(repo_data):
    """
    Finds and processes the first valid image from a repository's README.
    It finds all potential image URLs and tries each one until successful.
    """
    readme_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_data['name']}/readme"
    response = make_request_with_retries(readme_url, headers=get_api_headers())
    if not response:
        print(f"    - Could not fetch README for {repo_data['name']}.")
        return None

    try:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        # A single, powerful regex to find URLs in markdown tags OR as raw links
        url_pattern = r'!\[.*?\]\((.*?)\)|(https?://[^\s)]*?\.(?:png|jpg|jpeg|gif|svg)[^\s)]*)'
        
        # re.findall returns a list of tuples, e.g., [('url1', ''), ('', 'url2')].
        # This list comprehension flattens it into a clean list: ['url1', 'url2']
        potential_urls = [g1 or g2 for g1, g2 in re.findall(url_pattern, content)]

        if not potential_urls:
            return None

        # Try each found URL until one works
        for i, url in enumerate(potential_urls):
            print(f"    - Attempting to process image {i+1}/{len(potential_urls)}: {url.split('?')[0]}...")
            processed_url = _process_image_url(url.strip(), repo_data)
            if processed_url:
                print(f"    - Success! Using image for {repo_data['name']}.")
                return processed_url
            else:
                print(f"    - Failed to process image.")

    except Exception as e:
        print(f"    - Error processing README for {repo_data['name']}: {e}")
    
    return None

def generate_language_chart(languages, repo_name):
    if not languages: return None
    labels, sizes = list(languages.keys()), list(languages.values())
    fig, ax = plt.subplots(figsize=(6, 3), dpi=150, subplot_kw=dict(aspect="equal"))
    wedges, _, autotexts = ax.pie(sizes, autopct='%1.1f%%', startangle=90, colors=RETRO_COLORS, pctdistance=0.85, textprops={'color':"w"})
    plt.setp(autotexts, size=8, weight="bold")
    fig.gca().add_artist(plt.Circle((0,0),0.70,fc='#F8F5F1'))
    ax.legend(wedges, labels, title="Languages", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize='small')
    chart_path = os.path.join(STATS_DIR, f"{repo_name}.png")
    plt.savefig(chart_path, transparent=True, bbox_inches='tight')
    plt.close(fig)
    return chart_path

def process_repo(repo, is_pinned=False, override_crop=None, override_url=None):
    print(f"  - Processing repo: {repo['name']}")
    languages_response = make_request_with_retries(repo['languages_url'], headers=get_api_headers())
    languages = languages_response.json() if languages_response else {}
    crop_class = override_crop or CUSTOM_IMAGE_CROPPING.get(repo['name'], 'crop-top')
    return {
        'name': repo['name'], 'description': repo['description'] or "No description provided.",
        'url': override_url or repo['html_url'], 'stars': repo['stargazers_count'],
        'forks': repo['forks_count'],
        'last_updated': datetime.strptime(repo['pushed_at'], "%Y-%m-%dT%H:%M:%SZ").strftime("%b %Y"),
        'topics': repo.get('topics', []), 'open_issues': repo['open_issues_count'],
        'chart_path': generate_language_chart(languages, repo['name']),
        'readme_image_url': fetch_readme_and_image(repo),
        'crop_class': crop_class, 'is_pinned': is_pinned
    }

# --- MAIN EXECUTION ---
def main():
    os.makedirs(STATS_DIR, exist_ok=True)
    all_repos = fetch_github_repos()
    if not all_repos: return

    repos_dict = {repo['name']: repo for repo in all_repos}
    projects_data = []
    processed_repos = set()

    print("\nProcessing pinned projects...")
    for pinned_item in PINNED_REPOS:
        repo_name = pinned_item["name"]
        if repo_name in repos_dict and repo_name not in processed_repos:
            project = process_repo(
                repos_dict[repo_name], is_pinned=True,
                override_crop=pinned_item.get("crop"),
                override_url=pinned_item.get("url")
            )
            projects_data.append(project)
            processed_repos.add(repo_name)

    print("\nProcessing remaining projects...")
    remaining_repos_data = [
        r for name, r in repos_dict.items()
        if name not in processed_repos and not r['fork'] and name not in REPOS_TO_EXCLUDE
    ]
    remaining_repos_data.sort(key=lambda r: r['stargazers_count'], reverse=True)

    for repo in remaining_repos_data:
        projects_data.append(process_repo(repo))

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(TEMPLATE_FILE)
    html_content = template.render(
        projects=projects_data,
        generation_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    with open(OUTPUT_HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\nSuccessfully generated page with {len(projects_data)} projects at {OUTPUT_HTML_PATH}")

if __name__ == "__main__":
    main()
