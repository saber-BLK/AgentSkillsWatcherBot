import os
import html
import requests
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text[:4000],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    res = requests.post(url, json=payload, timeout=15)
    print("Telegram:", res.status_code, res.text)  # visible dans les logs Actions
    res.raise_for_status()  # fait échouer le workflow si Telegram refuse


def get_readme(full_name):
    url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": "SkillsWatcher"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    res = requests.get(url, headers=headers, timeout=15)
    return res.text[:800] if res.status_code == 200 else ""


def filter_with_ai(repo_name, description, readme_snippet):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""Analyse ce projet GitHub d'outil/skill pour agent IA :
Nom: {repo_name}
Description: {description}
Extrait README: {readme_snippet}

Réponds en français, format :
- Note de pertinence (1 à 10)
- Utile ou bruit / projet vide ?
- Résumé en 2 phrases max."""
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
    }
    res = requests.post(url, json=data, headers=headers, timeout=30)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    print("Groq error:", res.status_code, res.text)
    return "Impossible d'analyser le repo."


def check_github_trends():
    since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"(topic:claude-code OR topic:agent-skills OR topic:mcp-server) created:>={since}"
    headers = {"User-Agent": "SkillsWatcher", "Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": 3},
        headers=headers,
        timeout=15,
    )
    print("GitHub:", response.status_code)
    response.raise_for_status()

    repos = response.json().get("items", [])
    if not repos:
        print("Aucun nouveau repo.")
        return

    for repo in repos:
        name = repo["full_name"]
        desc = repo.get("description") or "Pas de description"
        link = repo["html_url"]
        analysis = filter_with_ai(name, desc, get_readme(name))

        msg = (
            f"🚀 <b>Nouveau Skill IA détecté !</b>\n\n"
            f"📌 <a href=\"{link}\">{html.escape(name)}</a>\n"
            f"📝 <i>{html.escape(desc)}</i>\n\n"
            f"🤖 <b>Analyse IA :</b>\n{html.escape(analysis)}"
        )
        send_telegram_message(msg)


if __name__ == "__main__":
    check_github_trends()