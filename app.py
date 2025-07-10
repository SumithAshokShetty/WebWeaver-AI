import streamlit as st
import os
import json
import base64
from agent import run_agent
from utils import save_code_to_files, create_zip, extract_component_blocks
from history import save_chat_to_history
from agent import domain as detect_domain  

if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.get("started"):
    st.set_page_config(
        page_title="WebWeaver AI",
        page_icon="webweaver Welcome logo.png",  
        layout="wide"
    )

    st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
            margin: 0;
            padding: 0;
        }

        .welcome-wrapper {
            padding-top: 12vh;
            padding-bottom: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            width: 100%;
            animation: fadeIn 1s ease-in-out;
        }

        .welcome-title {
            font-size: 5rem;
            font-weight: 800;
            color: black grey;
            margin-bottom: 0.3rem;
        }

        .typing-subtitle {
            font-size: 2.3rem;
            color: black grey;
            border-right: 2px solid black;
            white-space: nowrap;
            overflow: hidden;
            width: 0;
            animation:
                typing 3s steps(40, end) forwards,
                blink-caret 0.75s step-end infinite;
            margin-bottom: 2rem;
        }

        @keyframes typing {
            from { width: 0 }
            to { width: 60% }
        }

        @keyframes blink-caret {
            from, to { border-color: transparent }
            50% { border-color: black grey}
        }

        /* Light mode button */
        .stButton > button {
            font-size: 2.2rem;
            padding: 0.7rem 2.2rem;
            border-radius: 10px;
            background-color: white;
            color: black;
            border: 2px solid black;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        /* Dark mode overrides */
        @media (prefers-color-scheme: dark) {
            .welcome-title, .typing-subtitle {
                color: white;
                border-right: 2px solid white;
            }

            .stButton > button {
                background-color: black;
                color: white;
                border: 2px solid white;
            }
        }

        .stButton > button:hover {
            transform: scale(1.03);
            opacity: 0.9;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="welcome-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="welcome-title">Welcome to WebWeaver AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="typing-subtitle">Turn your ideas into stunning websites instantly</div>', unsafe_allow_html=True)

    if st.button("Get Started"):
        st.session_state.started = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


def list_chats():
    history_file = "history/chat_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        return {str(i): f"{item['prompt'][:30]}..." for i, item in enumerate(history)}
    return {}

def delete_chat(chat_id):
    history_file = "history/chat_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)
        if 0 <= int(chat_id) < len(history):
            del history[int(chat_id)]
            with open(history_file, "w") as f:
                json.dump(history, f, indent=4)

st.sidebar.title("WebWeaver AI")

if st.sidebar.button("➕ New Chat"):

    keep_keys = {"started"}
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            del st.session_state[key]

    if os.path.exists("outputs/index.html"):
        os.remove("outputs/index.html")

    st.session_state["new_chat_started"] = True
    st.rerun()

st.sidebar.header("🗂️ Your Chats")
chat_list = list_chats()
st.sidebar.markdown("---")
for chat_id, label in chat_list.items():
    cols = st.sidebar.columns([0.8, 0.2])
    with cols[0]:
        if st.button(label, key=chat_id):
            st.session_state["selected_chat_id"] = int(chat_id)
            st.session_state["load_chat"] = True
    with cols[1]:
        if st.button("🗑️", key=f"delete_{chat_id}"):
            delete_chat(chat_id)
            st.rerun()


chat_history = []
history_file = "history/chat_history.json"
if os.path.exists(history_file):
    with open(history_file, "r") as f:
        chat_history = json.load(f)

if st.session_state.get("load_chat") and "selected_chat_id" in st.session_state:
    i = st.session_state["selected_chat_id"]
    selected_chat = chat_history[i]

    st.markdown("## Previously Selected Chat")
    st.markdown(f"**Prompt:** {selected_chat['prompt']}")

    code_blocks = extract_component_blocks(selected_chat["response"])

    st.markdown("### 🧱 HTML")
    st.code("\n\n".join(code_blocks.get("html", [])), language="html")
    st.markdown("### 🎨 CSS")
    st.code("\n\n".join(code_blocks.get("css", [])), language="css")
    st.markdown("### ⚙️ JavaScript")
    st.code("\n\n".join(code_blocks.get("js", [])), language="javascript")

    html_code = "\n".join(code_blocks.get("html", [])).replace("```html", "").replace("```", "")
    css_code = "\n".join(code_blocks.get("css", []))
    js_code = "\n".join(code_blocks.get("js", []))

    
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Web Preview</title>
  <style>{css_code}</style>
</head>
<body>
{html_code}

<script>
// Run only if not in iframe (i.e., opened in new tab)
  if (window.top === window.self) {{
    if (!window.location.hash.includes("#reloaded")) {{
      window.location.href = window.location.href + "#reloaded";
      window.location.reload();
    }}
  }}
</script>

<script>{js_code}</script>
</body>
</html>
"""

    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    with open("outputs/index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

    st.markdown("### 🔍 Live Preview")
    try:
        with open("outputs/index.html", "r", encoding="utf-8") as f:
            html_output = f.read()
        b64_html = base64.b64encode(html_output.encode()).decode()
        href = f'data:text/html;base64,{b64_html}'
        st.markdown(f'<a href="{href}" target="_blank">🌐 Open Website in New Tab</a>', unsafe_allow_html=True)
        st.components.v1.html(html_output, height=800, scrolling=True)
        st.info("Note: Navigation links may not work in preview. Download for full functionality.")
    except Exception as e:
        st.error(f"Preview failed: {e}")

    st.session_state["load_chat"] = False


st.title("Welcome to WebWeaver AI")

if st.session_state.get("new_chat_started"):
    st.session_state["user_prompt"] = ""
    st.session_state["header"] = ""
    st.session_state["hero"] = ""
    st.session_state["footer"] = ""
    st.session_state["theme"] = "Light"
    del st.session_state["new_chat_started"]

user_prompt = st.text_area("Enter a detailed Prompt to Build Website", height=150, key="user_prompt")


domain_placeholders = {
    "restaurant": {
        "header": "🔹 Brand or site name (e.g. Fresh Bites | Premium Food Delivery)",
        "hero": "🔹 Main message (e.g. Delicious meals delivered fresh to your door — Order now!)",
        "footer": "🔹 Contact info (e.g. © 2025 Fresh Bites | info@freshbites.com)"
    },
    "portfolio": {
        "header": "🔹 Your name or role (e.g. Jane Doe | Full Stack Developer)",
        "hero": "🔹 Personal intro (e.g. Building elegant, scalable web apps.)",
        "footer": "🔹 Email/social (e.g. jane@example.com | © 2025 Jane Doe)"
    },
    "ecommerce": {
        "header": "🔹 Shop name (e.g. UrbanStyle | Fashion for Everyone)",
        "hero": "🔹 Sales headline (e.g. Up to 50% off on all summer wear!)",
        "footer": "🔹 Support info (e.g. help@urbanstyle.com | Refund Policy)"
    },
    "agency": {
        "header": "🔹 Agency name (e.g. Pixel Perfect | Creative Studio)",
        "hero": "🔹 Value proposition (e.g. We craft beautiful, user-first digital solutions.)",
        "footer": "🔹 Legal/contact (e.g. © 2025 Pixel Perfect | contact@agency.com)"
    },
    "blog": {
        "header": "🔹 Blog name (e.g. MindSparks | Thoughts & Stories)",
        "hero": "🔹 Tagline (e.g. Sharing insights on tech, life, and more.)",
        "footer": "🔹 Author info (e.g. © 2025 MindSparks by Alex Smith)"
    },
    "generic": {
        "header": "🔹 Website name (e.g. WebNova | Modern Solutions)",
        "hero": "🔹 Hero tagline (e.g. Unlock powerful digital tools in one click)",
        "footer": "🔹 Footer info (e.g. contact@webnova.com | © 2025 WebNova)"
    }
}

domain_type = detect_domain.run(user_prompt).lower() if user_prompt else "generic"
placeholders = domain_placeholders.get(domain_type, domain_placeholders["generic"])


st.markdown("### 🎨 Theme + Content Customization")
theme = st.selectbox("Select Theme", ["Light", "Dark", "Modern Blue", "Minimal"], key="theme")

header = st.text_input("Header Text", placeholder=placeholders["header"], key="header")
hero = st.text_area("Hero Text", placeholder=placeholders["hero"], key="hero")
footer = st.text_input("Footer Text", placeholder=placeholders["footer"], key="footer")

custom_values = {
    "header": header,
    "hero": hero,
    "footer": footer,
    "theme": theme
}


if st.button("🚀 Generate Website"):
    with st.spinner("Building the website..."):
        try:
            response = run_agent(user_prompt, custom_values)
        except Exception as e:
            st.error("Error while generating website")
            st.error(str(e))
        else:
            output_paths, language = save_code_to_files(response, user_prompt)
            st.session_state["response"] = response
            st.session_state["output_paths"] = output_paths
            st.session_state["language"] = language
            save_chat_to_history(user_prompt, response)
            st.success("🎉 Your website has been generated!")

if "response" in st.session_state:
    st.markdown("## 🔍 Preview")
    view_mode = st.radio("View:", ["Live Preview", "Code"], horizontal=True)

    code_blocks = extract_component_blocks(st.session_state["response"])

    if view_mode == "Code":
        if code_blocks.get("html"):
            st.markdown("#### 🧱 HTML")
            st.code("\n\n".join(code_blocks["html"]), language="html")
        if code_blocks.get("css"):
            st.markdown("#### 🎨 CSS")
            st.code("\n\n".join(code_blocks["css"]), language="css")
        if code_blocks.get("js"):
            st.markdown("#### ⚙️ JavaScript")
            st.code("\n\n".join(code_blocks["js"]), language="javascript")
    else:
        html_code = "\n".join(code_blocks.get("html", [])).replace("```html", "").replace("```", "")
        css_code = "\n".join(code_blocks.get("css", []))
        js_code = "\n".join(code_blocks.get("js", []))

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Web Preview</title>
  <style>{css_code}</style>
</head>
<body>
{html_code}
<script>{js_code}</script>
</body>
</html>
"""

        with open("outputs/index.html", "w", encoding="utf-8") as f:
            f.write(full_html)

        b64_html = base64.b64encode(full_html.encode()).decode()
        href = f'data:text/html;base64,{b64_html}'
        st.markdown(f'''
    <a href="{href}" target="_blank" style="
        display: inline-block;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        color: white;
        background-color: #4CAF50;
        border: none;
        border-radius: 8px;
        text-decoration: none;
        transition: background-color 0.3s ease;
    " onmouseover="this.style.backgroundColor='#45a049'" 
      onmouseout="this.style.backgroundColor='#4CAF50'">
        Open in New Tab
    </a>
    <span style="font-size: 18px; color: red;">  (Please reload the page once after it opens)</span>
''', unsafe_allow_html=True)
        st.components.v1.html(full_html, height=800, scrolling=True)
        st.info("Note: Preview may not support full navigation. Download ZIP for full experience.")

    zip_path = create_zip(st.session_state["output_paths"])
    with open(zip_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Website ZIP",
            data=f,
            file_name="website_package.zip",
            mime="application/zip"
        )
