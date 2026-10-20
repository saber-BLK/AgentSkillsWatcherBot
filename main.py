import os
import requests

# Secrets (configurés plus tard sur GitHub)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def filter_with_ai(repo_name, description, readme_snippet):
    """Filtre l'utilité du repo avec un LLM gratuit via Groq"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Analyse ce projet GitHub d'outil/skill pour agent IA :
    Nom: {repo_name}
    Description: {description}
    Extrait README: {readme_snippet[:500]}

    Réponds au format suivant :
    - Note de pertinence (1 à 10)
    - Est-ce vraiment utile ou est-ce du bruit / un projet vide ?
    - Résumé en 2 phrases max de ce que ça apporte aux développeurs.
    """
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    res = requests.post(url, json=data, headers=headers)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    return "Impossible d'analyser le repo."

def check_github_trends():
    # Cherche les repos créés récemment avec des mots clés d'agents/skills
    query = "topic:claude-code OR topic:agent-skills OR topic:mcp-server"
    url = f"https://api.github.com/search/repositories?q={query}&sort=created&order=desc"
    
    response = requests.get(url, headers={"User-Agent": "PythonApp"})
    if response.status_code == 200:
        repos = response.json().get("items", [])[:3] # Vérifier les 3 plus récents
        
        for repo in repos:
            name = repo["full_name"]
            desc = repo.get("description", "Pas de description")
            link = repo["html_url"]
            
            # Analyse par l'IA
            ai_analysis = filter_with_ai(name, desc, desc)
            
            msg = (
                f"🚀 **Nouveau Skill IA Détecté !**\n\n"
                f"📌 [{name}]({link})\n"
                f"📝 _{desc}_\n\n"
                f"🤖 **Analyse IA :**\n{ai_analysis}"
            )
            send_telegram_message(msg)

if __name__ == "__main__":
    check_github_trends()