import os
import logging
import base64
import json
import random
from dotenv import load_dotenv
import requests
import openai
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image, ImageDraw, ImageFont

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
                    "You are an insightful Bible scholar. Given a challenging situation, "
                    "choose a less-common verse that brings hope. Return a JSON object "
                    "with keys 'scripture_text' (full verse+ref) and 'commentary' (2–3 sentences)."
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
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

    # Attempt JSON parse
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            snippet = text[start:end+1]
            try:
                data = json.loads(snippet)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

    verse = data.get("scripture_text", "").strip()
    commentary = data.get("commentary", "").strip()

    # Fallback: naive split
    if not verse:
        parts = text.split("\n", 1)
        verse = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""

    return verse, commentary

# ── Image generation (DALL·E 3, watercolor pastoral) ──────────────────────────
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
        f"A flowing, painterly watercolor landscape of '{scene}'—"
        f"{random.choice(WEATHERS)}, {random.choice(PALETTES)}, "
        f"depicted from a {random.choice(VIEWPOINTS)}. "
        "Early-morning light filtering through haze, foreground blades of grass "
        "in gentle blur, crisp mid-ground focal point, reflective water "
        "catching the sky. Loose wet-on-wet strokes with subtle granulation, "
        "tranquil atmosphere. Avoid people, buildings, and man-made objects. "
        f"{NEGATIVE}"
    )

    resp = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size=size)
    item = resp.data[0]
    url = getattr(item, "url", None) or item.get("url")
    if url and url.startswith("http"):
        return url
    b64 = getattr(item, "b64_json", None) or item.get("b64_json")
    if b64:
        return f"data:image/png;base64,{b64}"
    raise RuntimeError("No usable image data returned by OpenAI.")

# ── Download, watermark, and serve image ──────────────────────────────────────
def download_and_watermark(src: str) -> str:
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    raw_path = os.path.join(static_dir, "raw.png")

    # Download or decode
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

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    final_path = os.path.join(static_dir, "image.png")
    combined.save(final_path, "PNG")
    return url_for("static", filename="image.png")

# ── Flask routes ──────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        scene = request.form.get("scene", "").strip()
        try:
            verse, commentary = generate_scripture(scene)
            src = generate_image(scene)
            image_url = download_and_watermark(src)
            return render_template(
                "result.html",
                verse=verse,
                commentary=commentary,
                image_url=image_url,
                imgur_client_id=IMGUR_CLIENT_ID,
            )
        except Exception as e:
            logger.error("Error generating ScriptureScape", exc_info=True)
            flash(str(e), "danger")
            return redirect(url_for("index"))
    return render_template("index.html")

# ── Run local dev server ──────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
