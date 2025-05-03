<<<<<<< HEAD
# 📜 ScriptureScape

![Built with OpenAI](https://img.shields.io/badge/Built%20with-OpenAI-blueviolet)

A Flask app that generates an uplifting scripture + commentary paired with a comforting, watercolor-style image to inspire hope. Powered by the OpenAI API.

---


## ✨ Features

- **✍️ Input:** Describe your current situational challenge in plain language.  
- **🎨 Output:**  
  - 📖 A relevant Bible verse   
  - 💬 A 2–3 sentence uplifting commentary  
  - 🖼️ A peaceful watercolor-style poster   
- **🚀 Built-in Actions:**  
  - 📥 Download the generated image  
  - 📧 Email it directly  
  - 📱 Post to social media with one click  
- **☁️ Optional:** One-click Imgur upload (requires `IMGUR_CLIENT_ID`)

---

## 🎞️ Animated Walkthrough — ScriptureScape in Action

Below is a quick, silent GIF (≈10 s) that illustrates the full flow:

1. **Enter a challenge** – e.g. *“I just lost my job and the bills are piling up.”*
2. **Instant comfort** – ScriptureScape selects an encouraging verse, adds a brief commentary, and paints a tranquil watercolor landscape.
3. **Built‑in actions** – One‑click **Download**, **Email**, and **Share** buttons appear on the results screen.

<p align="center">
  <img src="docs/scripturescape-demo.gif" alt="ScriptureScape animated demo" width="640">
</p>

---

## 🛠️ Setup

1. **📥 Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/scripturescape.git
   cd scripturescape
=======
# ScriptureScape

A Flask app that generates uplifting Bible verses and watercolor-style images,
then produces an animated GIF to inspire hope.

## Features

- Input: Describe your current challenge.
- Output: A relevant Bible verse + commentary, plus a 3-frame animated GIF.
- Optional one-click Imgur upload (requires IMGUR_CLIENT_ID).

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/yourusername/scripturescape.git
   cd scripturescape
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example env file and fill in your keys:
   ```bash
   cp config.env.txt.example config.env.txt
   ```

5. Run the app:
   ```bash
   flask run
   ```

6. Open http://127.0.0.1:5000 in your browser.

## Packaging & Deployment

```bash
git init
git add .
git commit -m "Initial commit"
# Add your GitHub remote:
git remote add origin git@github.com:yourusername/scripturescape.git
git push -u origin main
```
>>>>>>> Initial commit of ScriptureScape
