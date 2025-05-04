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

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

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

    if not verse:
        parts = text.split("\n", 1)
        verse = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""

    return verse, commentary

# ── Image generation (DALL·E 3) ────────────────────────────────────────────────
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

def generate_image(scene: str, scripture: str, size: str = "1024x1024") -> str:
    """
    Generate a hopeful watercolor-style image that visually reflects the user's situation
    and the scripture message, without showing text or people.
    """
    prompt = (
        f"A gentle and emotionally uplifting watercolor landscape, inspired by the feeling of: '{scene}', "
        f"and the message: '{scripture}'. The scene should use nature as a metaphor to reflect hope, peace, and renewal. "
        f"Use a soft and serene color palette like {random.choice(PALETTES)}, with natural light conditions such as "
        f"{random.choice(WEATHERS)}. Style: loose wet-on-wet brushwork, subtle gradients, flowing organic shapes. "
        f"Avoid any people, text, buildings, or man-made objects. "
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


# ── Download and watermark image ───────────────────────────────────────────────
def download_and_watermark(src: str) -> str:
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    raw_path = os.path.join(static_dir, "raw.png")

    if src.startswith("http"):
        r = requests.get(src)
        r.raise_for_status()
        data = r.content
    else:
        data = base64.b64decode(src.split(",", 1)[1])

    with open(raw_path, "wb") as f:
        f.write(data)

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

# ── Flask route ────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        scene = request.form.get("scene", "").strip()
        try:
            verse, commentary = generate_scripture(scene)

            # Split verse into main text and reference using em dash
            if "—" in verse:
                verse_text, verse_reference = map(str.strip, verse.split("—", 1))
            else:
                verse_text = verse
                verse_reference = ""

            src = generate_image(scene)
            image_url = download_and_watermark(src)

            return render_template(
                "result.html",
                verse_text=verse_text,
                verse_reference=verse_reference,
                commentary=commentary,
                image_url=image_url,
                imgur_client_id=IMGUR_CLIENT_ID,
            )
        except Exception as e:
            logger.error("Error generating ScriptureScape", exc_info=True)
            flash(str(e), "danger")
            return redirect(url_for("index"))
    return render_template("index.html")

# ── Run Dev Server ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
