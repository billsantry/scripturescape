# ScriptureScape

A Flask app that generates an uplifting Bible verse + commentary paired with a comforting, watercolor-style image to inspire hope.

---

## Features

- **Input:** Describe your current challenge in plain language.  
- **Output:**  
  - A relevant Bible verse (less-common, chosen for hope)  
  - A 2–3 sentence uplifting commentary  
  - A single watercolor-style image illustrating divine providence  
- **Built‑in Actions:** Download the generated image, email it directly, or post to social media with one click.  
- **Optional:** One-click Imgur upload (requires `IMGUR_CLIENT_ID`)

---

## Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/scripturescape.git
   cd scripturescape
   ```

2. **Create & activate a virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy & configure env file**  
   ```bash
   cp config.env.txt.example config.env.txt
   # then open config.env.txt and fill in:
   #   OPENAI_API_KEY=sk-…
   #   FLASK_SECRET_KEY=…
   #   IMGUR_CLIENT_ID=…   (optional)
   ```

5. **Run the app**  
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development   # optional: auto-reload & debug traces
   flask run
   ```

6. **Browse**  
   Open <http://127.0.0.1:5000> in your browser.

---

## Project Structure

```
scripturescape/                # project root
├── app.py                     # main Flask application
├── requirements.txt           # Python dependencies
├── config.env.txt.example     # sample env file (DO NOT commit your real keys)
├── static/                    # generated assets
│   └── image.png              # final watercolor image
├── templates/                 # HTML templates
│   ├── index.html             # input form
│   └── result.html            # scripture + image display
├── fonts/                     # custom fonts used for watermark
│   └── arial.ttf
└── README.md                  # this file
```

---

## Packaging & Deployment

```bash
# (Only if you didn't already init)
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:yourusername/scripturescape.git
git push -u origin main
```

---

## Pro Tips

- **Keep secrets out of Git.**  Your real `config.env.txt` should be in `.gitignore`.  
- **Pin your deps.**  If you need to freeze exact versions:  
  ```bash
  pip freeze > requirements.txt
  ```
- **Hot-reload** in development:  
  ```bash
  export FLASK_ENV=development
  ```
- **CI/CD**: Add a GitHub Actions workflow to install, lint, and (optionally) deploy.  
- **Error handling**: Make sure your font path is correct or falls back to a system font.  
- **Model choice**: If you unlock GPT-Image-1 access you can swap in `model="gpt-image-1"` for richer watercolor outputs.

---

Thank you for using ScriptureScape — may it bring you hope and encouragement!  

