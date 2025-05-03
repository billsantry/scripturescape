import os
import logging
import base64
import json
<<<<<<< HEAD
import random            # <-- NEW
from dotenv import load_dotenv

=======
from dotenv import load_dotenv
>>>>>>> Initial commit of ScriptureScape
import requests
import openai
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image, ImageDraw, ImageFont

<<<<<<< HEAD
# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, "config.env.txt"))

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

# ── Scripture generation (GPT-4o) ──────────────────────────────────────────────
def generate_scripture(prompt: str) -> tuple[str, str]:
    """
    Given a short description of the user’s challenge, return
    (full_verse_with_reference, 2–3-sentence_commentary).
    """
    if not prompt:
        raise ValueError("Please describe your situation to receive a verse.")

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an insightful Bible scholar. Given a challenging "
                    "situation, choose a less-common verse that brings hope. "
                    "Return a JSON object with keys "
                    "'scripture_text' and 'commentary'."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=200,
    )
    text = resp.choices[0].message.content.strip()

    # Strip optional ```json code fences
    if text.startswith("```") and text.endswith("```"):
        text = "\n".join(text.splitlines()[1:-1]).strip()

    # Attempt JSON parse
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: grab first {...}
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start : end + 1]) if start != -1 and end != -1 else {}

    verse      = data.get("scripture_text", "").strip()
    commentary = data.get("commentary", "").strip()

    # If parsing failed, use naive split
    if not verse:
        parts = text.split("\n", 1)
        verse      = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""

    return verse, commentary

# ── Image generation (DALL·E 3, watercolor pastoral) ──────────────────────────
# 🍃  Adjective pools for controlled randomness
PALETTES = [
    "warm pastel washes",
    "cool dawn blues",
    "emerald spring hues",
    "autumnal ambers",
    "twilight lavenders",
]
WEATHERS = ["sun-kissed", "misty", "golden-hour", "overcast", "after-rain"]
VIEWPOINTS = [
    "bird’s-eye view",
    "low-angled vantage",
    "mid-field perspective",
    "close-up foreground focus",
    "wide panoramic sweep",
]

# 🍃  Negative prompt fragment that bans every form of lettering
NEGATIVE = (
    "No text, lettering, calligraphy, handwriting, signage, symbols, captions, "
    "logos, watermarks, UI, or any typographic element."
)

def generate_image(scene: str, size: str = "1024x1024") -> str:
    """
    Return a DALL·E 3 watercolor landscape URL (or base64 URI) for `scene`,
    varying palette, weather, and viewpoint each call while guaranteeing
    zero typography.
    """
    prompt = (
        f"A flowing, painterly watercolor landscape of {scene} — "
        f"{random.choice(WEATHERS)}, {random.choice(PALETTES)}, "
        f"depicted from a {random.choice(VIEWPOINTS)}. "
        "Early-morning light filtering through haze, foreground blades of grass "
        "in gentle blur, crisp mid-ground focal point, reflective water "
        "catching the sky. Loose wet-on-wet strokes with subtle granulation, "
        "tranquil atmosphere. Avoid people, buildings, and man-made objects. "
        f"{NEGATIVE}"
    )

    response = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size=size)
    item = response.data[0]

    # Prefer HTTPS URL; fallback to b64
    url = getattr(item, "url", None) or item.get("url")
    if url and url.startswith("http"):
        return url
    b64 = getattr(item, "b64_json", None) or item.get("b64_json")
    if b64:
        return f"data:image/png;base64,{b64}"

    raise RuntimeError("No usable image data returned by OpenAI.")

# ── Download, watermark, and serve image ──────────────────────────────────────
=======
# Setup
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, "config.env.txt"))
app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

# Scripture generation
def generate_scripture(prompt: str) -> tuple[str, str]:
    if not prompt:
        raise ValueError("Please describe your situation to receive a verse.")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "You are an insightful Bible scholar. Given a challenging situation, choose a less-common verse that brings hope. "
                "Return a JSON object with keys 'scripture_text' (full verse+ref) and 'commentary' (2–3 sentences)."
            )},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=200
    )
    content = resp.choices[0].message.content.strip()
    # Strip markdown fences if present
    if content.startswith("```") and content.endswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```") and lines[-1].startswith("```"):
            content = "\n".join(lines[1:-1])
    try:
        data = json.loads(content)
        return data["scripture_text"], data["commentary"]
    except json.JSONDecodeError:
        parts = content.split("\n", 1)
        verse = parts[0]
        comment = parts[1] if len(parts) > 1 else ""
        return verse, comment

# Image generation (DALL·E 3, pastoral flowing style)
def generate_image(scene: str) -> str:
    prompt = (
        f"A flowing, painterly watercolor landscape of '{scene}'—"
        "gentle pastoral scenes with soft rolling hills and a light mist gradually lifting as golden sunlight displaces remaining shadows, "
        "subtle, hand-brushed textures and warm pastel washes. "
        "Avoid distant vague figures or haunting silhouettes; focus on tranquil scenes of nature."
    )
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    item = resp.data[0]
    url = getattr(item, 'url', None) or item.get('url')
    if url and url.startswith("http"):
        return url
    b64 = getattr(item, 'b64_json', None) or item.get('b64_json')
    if b64:
        return f"data:image/png;base64,{b64}"
    raise RuntimeError("No usable image data")

# Download, watermark, and return URL
>>>>>>> Initial commit of ScriptureScape
def download_and_watermark(src: str) -> str:
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    raw_path = os.path.join(static_dir, "raw.png")

<<<<<<< HEAD
    # Download or decode
    data = (
        requests.get(src).content
        if src.startswith("http")
        else base64.b64decode(src.split(",", 1)[1])
    )
    with open(raw_path, "wb") as f:
        f.write(data)

    # Watermark
    img = Image.open(raw_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "arial.ttf"), 20)
    except IOError:
        font = ImageFont.load_default()

    text = "ScriptureScape ©Bill Santry"
    bbox = draw.textbbox((0, 0), text, font=font)
    x = img.width - (bbox[2] - bbox[0]) - 10
    y = img.height - (bbox[3] - bbox[1]) - 10
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
=======
    # Download the image
    if src.startswith("http"):
        r = requests.get(src)
        r.raise_for_status()
        data = r.content
    else:
        data = base64.b64decode(src.split(",", 1)[1])
    with open(raw_path, "wb") as f:
        f.write(data)

    # Add watermark
    img = Image.open(raw_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(os.path.join(BASE_DIR, "fonts", "arial.ttf"), size=20)
    except IOError:
        font = ImageFont.load_default()
    text = "ScriptureScape ©Bill Santry"
    bbox = draw.textbbox((0,0), text, font=font)
    x = img.width - (bbox[2] - bbox[0]) - 10
    y = img.height - (bbox[3] - bbox[1]) - 10
    draw.text((x, y), text, font=font, fill=(255,255,255,128))
>>>>>>> Initial commit of ScriptureScape

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    final_path = os.path.join(static_dir, "image.png")
    combined.save(final_path, "PNG")
    return url_for("static", filename="image.png")

<<<<<<< HEAD
# ── Flask routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
=======
@app.route("/", methods=["GET","POST"])
>>>>>>> Initial commit of ScriptureScape
def index():
    if request.method == "POST":
        scene = request.form.get("scene", "").strip()
        try:
            verse, commentary = generate_scripture(scene)
            src = generate_image(scene)
            image_url = download_and_watermark(src)
<<<<<<< HEAD
            return render_template(
                "result.html",
                verse=verse,
                commentary=commentary,
                image_url=image_url,
                imgur_client_id=IMGUR_CLIENT_ID,
            )
=======
            return render_template("result.html", verse=verse, commentary=commentary, image_url=image_url, imgur_client_id=IMGUR_CLIENT_ID)
>>>>>>> Initial commit of ScriptureScape
        except Exception as e:
            logger.error("Error generating ScriptureScape", exc_info=True)
            flash(str(e), "danger")
            return redirect(url_for("index"))
<<<<<<< HEAD

    return render_template("index.html")

# ── Run local dev server ──────────────────────────────────────────────────────
=======
    return render_template("index.html")

>>>>>>> Initial commit of ScriptureScape
if __name__ == "__main__":
    app.run(debug=True)
