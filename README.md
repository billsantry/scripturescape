# ScriptureScape

**ScriptureScape** is a lightweight Flask application that turns your real-life challenges into sources of hope by:

1. **Generating a context-appropriate Bible verse** (with brief uplifting commentary).  
2. **Producing a 3-frame watercolor-style animated GIF** that visually reinforces God’s provision.

All runs locally in your browser—no login required—though you can optionally upload results to Imgur.

---

## 🎯 Features

- **Natural-language input**  
  Simply describe your current situation, challenge or prayer request.  
- **AI-powered scripture selection**  
  GPT-4-powered “Bible scholar” chooses a less-common verse and supplies 2–3 sentences of encouragement.  
- **Watercolor imagery**  
  DALL·E 3 creates three pastoral, hand-painted–feel scenes based on your prompt.  
- **Animated GIF output**  
  The three frames loop indefinitely (3 seconds each), ready for sharing or reflection.  
- **One-click Imgur upload** (optional)  
  Paste your own IMGUR_CLIENT_ID into `.env` to host results on Imgur.

---

## 🚀 Quickstart

```bash
# 1. Clone & enter project directory
git clone https://github.com/billsantry/scripturescape.git
cd scripturescape

# 2. Create & activate a Python venv
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy & edit your environment variables
cp config.env.txt.example config.env.txt
# ← open config.env.txt and add:
#    OPENAI_API_KEY=sk-...
#    FLASK_SECRET_KEY=a-random-secret
#    (optional) IMGUR_CLIENT_ID=your-imgur-client-id

# 5. Run the development server
export FLASK_APP=app.py
export FLASK_ENV=development
flask run

# 6. Open in browser
#    http://127.0.0.1:5000
