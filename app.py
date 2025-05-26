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

# ── Setup ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
load_dotenv(os.path.join(BASE_DIR, "config.env.txt"))

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

# ── Scripture generation (GPT-4o) ────────────────────────────────────

def generate_scripture(prompt: str) -> tuple[str, str]:
    if not prompt:
        raise ValueError("Please describe your situation to receive a verse.")

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a thoughtful and creative Bible scholar. "
                    "Given a person's emotional or situational challenge, "
                    "select a scriptural verse that is appropriate but unexpected — "
                    "something less commonly quoted, unless a popular verse offers unique relevance. "
                    "Avoid repetition of the same verses across similar prompts. "
                    "Avoid embellishing or adding any text outside the verse itself. "
                    "Your goal is to offer surprising comfort rooted in biblical truth.\n\n"
                    "Return only a JSON object with the following keys:\n"
                    "- 'scripture_text': the full verse and reference, with nothing added.\n"
                    "- 'commentary': 2–3 sentences that connect the verse to the user's situation.\n\n"
                    "Never include introductory phrases, markdown formatting, or extra symbols."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        max_tokens=250,
    )

    text = resp.choices[0].message.content.strip()

    # Optional debug logging
    # print("Raw model response:\n", text)

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

    # 🔒 Additional fallback in case of malformed response
    if not verse or verse == "{" or verse.startswith("{"):
        print("⚠️ Invalid or missing scripture_text — using fallback.")
        parts = text.split("\n", 1)
        verse = parts[0].strip()
        commentary = parts[1].strip() if len(parts) > 1 else ""

        # Still invalid? Show placeholder
        if not verse or verse == "{" or len(verse) < 10:
            verse = "Scripture not available right now. Please try again."
            commentary = ""

    return verse, commentary


# ── Image generation (DALL·E 3) ────────────────────────────────────────────────

PALETTES = [
    "warm pastel washes",
    "cool dawn blues",
    "emerald spring hues",
    "autumnal ambers",
    "twilight lavenders",
]

WEATHERS = [
    "sun-kissed",
    "misty",
    "golden-hour",
    "overcast",
    "after-rain",
    "early morning",
]

VIEWPOINTS = [
    "bird’s-eye view",
    "low-angled vantage",
    "mid-field perspective",
    "close-up foreground focus",
    "wide panoramic sweep",
]

NEGATIVE = (
    "Do not include people, humans, faces, silhouettes, shadows, figures, crowds, or human forms. "
    "Do not include any form of text, writing, letters, numbers, symbols, or typographic marks. "
    "No readable content, no inscriptions, no watermarks, no logos, no UI elements. "
    "This is a text-free image. The artwork must not contain any language or writing in any form."
)

def generate_image(scene: str, scripture: str, size: str = "1024x1024") -> str:
    """
    Generate a hopeful watercolor-style image that visually reflects the user's situation
    and the scripture message, without showing text or people.
    """

    prompt = (
        f"A serene, emotionally uplifting watercolor painting inspired by the feeling of: '{scene}', "
        f"and the scripture: '{scripture}'. Use nature to symbolically reflect hope, peace, and renewal. "
        f"Favor a poetic composition with soft brushstrokes, luminous light, and harmonious colors — "
        f"perhaps a tranquil landscape, a path through morning mist, or a quiet place touched by grace. "
        f"Style: flowing wet-on-wet technique, gentle gradients, natural textures, and impressionistic detail. "
        f"{NEGATIVE}"
    )

    # ✨ Reinforce visual-only output
    prompt += " Clarity is visual, not textual. No written or readable elements should appear."

    resp = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size=size)
    item = resp.data[0]
    url = getattr(item, "url", None) or item.get("url")
    if url and url.startswith("http"):
        return url
    b64 = getattr(item, "b64_json", None) or item.get("b64_json")
    if b64:
        return f"data:image/png;base64,{b64}"
    raise RuntimeError("No usable image data returned by OpenAI.")


# ── Download and watermark image ──────────────────────────────

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

# ── Flask route ────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        scene = request.form.get("scene", "").strip()
        try:
            verse, commentary = generate_scripture(scene)

            if "—" in verse:
                verse_text, verse_reference = map(str.strip, verse.split("—", 1))
            else:
                verse_text = verse
                verse_reference = ""

            src = generate_image(scene, verse_text)
            image_url = download_and_watermark(src)

            return render_template(
                "result.html",
                verse_text=verse_text,
                verse_reference=verse_reference,
                commentary=commentary,
                image_url=image_url,
                imgur_client_id=IMGUR_CLIENT_ID,
                request_url=request.url
            )
        except Exception as e:
            logger.error("Error generating ScriptureScape", exc_info=True)
            flash(str(e), "danger")
            return redirect(url_for("index"))
    return render_template("index.html")

# ── Run Dev Server ─────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
