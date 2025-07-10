import os
import re
import zipfile
import requests
from dotenv import load_dotenv

load_dotenv()

def detect_language(prompt):
    if "html" in prompt.lower():
        return "html"
    elif "react" in prompt.lower():
        return "react"
    return "html"

def fetch_image_url(query, api_key):
    if not api_key:
        print("Missing Pexels API Key. Using fallback image.")
        return "https://picsum.photos/800/400"
    try:
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
        headers = {"Authorization": api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                return data["photos"][0]["src"]["large"]
    except Exception as e:
        print("🔥 Pexels API Error:", e)
    return "https://picsum.photos/800/400"

def extract_component_blocks(response):
    blocks = {"html": [], "css": [], "js": [], "jsx": [], "others": []}
    matches = re.findall(r"```(\w+)?\s*([\s\S]*?)```", response)

    if matches:
        for lang, code in matches:
            lang = (lang or "html").lower().strip()
            if lang == "javascript":
                lang = "js"
            code = re.sub(r"^`{1,3}\s*\w*", "", code)
            code = re.sub(r"`{1,3}$", "", code).strip()
            blocks.get(lang, blocks["others"]).append(code)
    else:
        cleaned = re.sub(r"^`{1,3}\s*\w*", "", response)
        cleaned = re.sub(r"`{1,3}$", "", cleaned).strip()
        blocks["html"].append(cleaned)

    return blocks

def build_page(title, body, css="", js="", nav_links="", image_url=""):
    nav = f"<nav>{nav_links}</nav>" if nav_links else ""

    if image_url and '<section id="hero"' in body:
        body = re.sub(
            r'(<section\s+[^>]*id=["\']hero["\'][^>]*)(>)',
            rf'\1 style="background-image: url({image_url}); background-size: cover; background-position: center;"\2',
            body,
            flags=re.IGNORECASE
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  {nav}
  {body}
  <script src="script.js"></script>
</body>
</html>
"""

def save_code_to_files(response, prompt):
    language = detect_language(prompt)
    blocks = extract_component_blocks(response)
    os.makedirs("outputs", exist_ok=True)

    html_code = "\n\n".join(blocks["html"])
    css_code = "\n\n".join(blocks["css"])
    js_code = "\n\n".join(blocks["js"])
    jsx_code = "\n\n".join(blocks["jsx"])
    output_paths = []

    nav_links = ""
    if "home" in prompt.lower() or True:
        nav_links += '<a href="index.html">Home</a> '
    if "about" in prompt.lower():
        nav_links += '<a href="about.html">About</a> '
    if "contact" in prompt.lower():
        nav_links += '<a href="contact.html">Contact</a> '

    access_key = os.environ.get("PEXELS_KEY")
    image_query = prompt or "modern website"
    image_url = fetch_image_url(image_query, access_key)

    if language == "react":
        with open("outputs/App.jsx", "w", encoding="utf-8") as f:
            f.write(jsx_code or js_code)
        output_paths.append("outputs/App.jsx")
    else:

        index_html = build_page("Home", html_code, css_code, js_code, nav_links, image_url)
        with open("outputs/index.html", "w", encoding="utf-8") as f:
            f.write(index_html)
        with open("outputs/style.css", "w", encoding="utf-8") as f:
            f.write(css_code)
        with open("outputs/script.js", "w", encoding="utf-8") as f:
            f.write(js_code)

        output_paths += [
            "outputs/index.html",
            "outputs/style.css",
            "outputs/script.js"
        ]

        if "about" in prompt.lower():
            about_html = build_page(
                "About",
                "<h1>About Us</h1><p>This is the about page.</p>",
                css_code,
                js_code,
                nav_links,
                image_url
            )
            with open("outputs/about.html", "w", encoding="utf-8") as f:
                f.write(about_html)
            output_paths.append("outputs/about.html")

        if "contact" in prompt.lower():
            contact_html = build_page(
                "Contact",
                "<h1>Contact Us</h1><p>Email: contact@example.com</p>",
                css_code,
                js_code,
                nav_links,
                image_url
            )
            with open("outputs/contact.html", "w", encoding="utf-8") as f:
                f.write(contact_html)
            output_paths.append("outputs/contact.html")

    return output_paths, language

def create_zip(file_paths, zip_name="website_package.zip"):
    zip_path = os.path.join("outputs", zip_name)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file in file_paths:
            zipf.write(file, arcname=os.path.basename(file))
    return zip_path

def split_code_blocks(response):
    html_code, css_code, js_code = "", "", ""
    matches = re.findall(r"```(\w+)?\s*([\s\S]*?)```", response)

    if not matches:
        html_code = response.strip()
    else:
        for lang, code in matches:
            lang = (lang or "html").lower()
            code = code.strip()
            if lang == "html":
                html_code += code + "\n\n"
            elif lang == "css":
                css_code += code + "\n\n"
            elif lang in ("js", "javascript"):
                js_code += code + "\n\n"

    return html_code.strip(), css_code.strip(), js_code.strip()
