import os
import logging
import base64
import json
from dotenv import load_dotenv
import requests
import openai
from flask import Flask, render_template, request, url_for, flash, redirect
from PIL import Image, ImageDraw, ImageFont

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
def download_and_watermark(src: str) -> str:
    static_dir = os.path.join(BASE_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    raw_path = os.path.join(static_dir, "raw.png")

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

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    final_path = os.path.join(static_dir, "image.png")
    combined.save(final_path, "PNG")
    return url_for("static", filename="image.png")

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        scene = request.form.get("scene", "").strip()
        try:
            verse, commentary = generate_scripture(scene)
            src = generate_image(scene)
            image_url = download_and_watermark(src)
            return render_template("result.html", verse=verse, commentary=commentary, image_url=image_url, imgur_client_id=IMGUR_CLIENT_ID)
        except Exception as e:
            logger.error("Error generating ScriptureScape", exc_info=True)
            flash(str(e), "danger")
            return redirect(url_for("index"))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
