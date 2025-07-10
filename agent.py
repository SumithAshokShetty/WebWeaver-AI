import os
import requests
from langchain.agents import initialize_agent, AgentType, tool
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

@tool
def domain(prompt: str) -> str:
    """Identify the website category from prompt: e.g., restaurant, blog, ecommerce."""
    prompt = prompt.lower()
    if "restaurant" in prompt or "cafe" in prompt:
        return "restaurant"
    elif "portfolio" in prompt:
        return "portfolio"
    elif "blog" in prompt:
        return "blog"
    elif "ecommerce" in prompt or "shop" in prompt:
        return "ecommerce"
    elif "agency" in prompt:
        return "agency"
    else:
        return "generic"

@tool
def analyse_websites(domain: str) -> str:
    """Analyze top websites in a given domain using Firecrawl and return design/content inspiration."""
    try:
        FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
        if not FIRECRAWL_API_KEY:
            return "Firecrawl API key not found."

        headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }

        domain_sites = {
            "restaurant": ["https://sweetgreen.com", "https://chipotle.com"],
            "portfolio": ["https://brittanychiang.com"],
            "ecommerce": ["https://zara.com"],
            "agency": ["https://ustwo.com"]
        }

        urls = domain_sites.get(domain.lower(), [])
        if not urls:
            return "ℹ️ No reference websites found for this domain."

        results = []
        for url in urls:
            try:
                res = requests.post("https://api.firecrawl.dev/v1/crawl", headers=headers, json={"url": url})
                data = res.json()
                summary = data.get("summary", "")
                keywords = data.get("keywords", [])
                results.append(f"{url}\n📝 {summary}\n🔑 Keywords: {keywords}")
            except Exception as inner:
                results.append(f"⚠️ Failed to analyze {url}: {inner}")

        return "\n\n".join(results)
    except Exception as e:
        return f"Firecrawl tool error: {e}"

@tool
def generate_seo_tags(title: str) -> str:
    """Generate basic SEO meta tags based on a title."""
    return f"""
<title>{title}</title>
<meta name="description" content="{title} - modern responsive website.">
<meta name="keywords" content="{title.lower()}, website, modern, responsive">
<meta name="author" content="AI Website Builder Agent">
"""

gemini_key = os.environ.get("GEMINI_API_KEY")
if not gemini_key:
    raise EnvironmentError("Gemini API key not found in environment variables.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=gemini_key,
    temperature=0.7
)

tools = [domain, analyse_websites, generate_seo_tags]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

def run_agent(user_prompt: str, custom_values: dict) -> str:
    try:
        full_prompt = f"""
You are a website building AI.

Your task is to generate a complete, clean, and modern website using HTML, CSS, and JavaScript for the following input:

Theme: {custom_values['theme']}
Header Text: {custom_values['header']}
Hero Section Text: {custom_values['hero']}
Footer Text: {custom_values['footer']}
User Prompt: {user_prompt}

Steps to follow:
1. Use the `domain` tool to identify the website category.
2. Use `analyse_websites` to get design/content inspiration.
3. Use `generate_seo_tags` to create meta tags.
4. Generate a modern website with 3 fully connected files: HTML, CSS, and JavaScript.
5. Ensure the navbar links (e.g., Home, About, Contact) work using smooth JS transitions.
6. Include at least 1 interactive JavaScript feature: e.g., dark mode, scroll animation, or form validation.

Your response must include 3 code blocks ONLY in this exact format:

```html
<!-- Full HTML including <head>, SEO tags, and complete <body> -->
/* Full CSS for layout, theme, responsiveness */
// JavaScript must be included
❌ Do NOT skip any of the 3 sections.
❌ Do NOT include markdown, explanations, or additional comments outside the code blocks.
"""
        return agent.run(full_prompt)
    except Exception as e:
        return f"Agent failed to generate website: {str(e)}"


