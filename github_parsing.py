"""Парсинг GitHub

Замечание: демо-вызовы в конце перенесены под `if __name__ == "__main__"`,
иначе они выполняли бы сетевой запрос при каждом `import github_parsing`.
"""
import requests
from bs4 import BeautifulSoup
import re


def parse_github_issue(url: str) -> str:
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  response = requests.get(url, headers=headers)
  response.raise_for_status()

  soup = BeautifulSoup(response.text, "html.parser")

  issue_body = soup.find("div", id="issue-body-viewer")

  if not issue_body:
    issue_body = soup.find("div", class_="markdown-body")

  if issue_body:
    return issue_body.get_text(separator="\n", strip=True)

  return "Issue body not found."


def get_repo_raw_urls(repo_url: str, token: str = None) -> dict:
  # проверяем правильность ссылки через regex
  match = re.match(
      r"^https?://github\.com/([^/]+)/([^/]+)(?:/.*)?$", repo_url.strip("/")
  )
  if not match:
    raise ValueError("Invalid GitHub repository URL format.")

  owner, repo = match.groups()

  # Set up headers (optional token helps avoid rate limits for large/many requests)
  headers = {"Accept": "application/vnd.github+json"}
  if token:
    headers["Authorization"] = f"Bearer {token}"

  # 1. Fetch default branch name
  repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
  resp = requests.get(repo_api_url, headers=headers)
  resp.raise_for_status()
  default_branch = resp.json().get("default_branch", "main")

  # 2. Fetch the recursive git tree
  tree_api_url = (
      f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}"
      "?recursive=1"
  )
  resp = requests.get(tree_api_url, headers=headers)
  resp.raise_for_status()
  tree_data = resp.json()

  raw_urls_dict = {}

  # 3. Filter only blobs (files) and build the raw URL mapping
  for item in tree_data.get("tree", []):
    if item["type"] == "blob":
      file_path = item["path"]
      raw_urls_dict[file_path] = (
          f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}"
          f"/{file_path}"
      )

  return raw_urls_dict


def parse_code_by_url(raw_url: str) -> str:
  response = requests.get(raw_url)
  response.raise_for_status()  # Raise an error for bad HTTP responses (404, 500, etc.)

  return response.text


if __name__ == "__main__":
  # print(parse_github_issue("https://github.com/numpy/numpy/issues/33154"))
  files_dict = get_repo_raw_urls("https://github.com/numpy/numpy")
  for path, url in list(files_dict.items())[:5]:
    print(f"{path}: {url}")
