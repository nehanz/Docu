# Docu
Docu is a Python tool that logs terminal commands and outputs, lets you add comments, and can mask sensitive data with docu mask. Its AI assistant can summarize sessions, explain commands, and help debug, while saving everything in organized, custom directories for easy access.


## Features

* 📝 Logs commands and outputs automatically
* 💬 Add comments or notes to sessions
* 🕵️ Mask sensitive data when needed (`docu mask`)
* 🤖 AI assistant for summaries, explanations, and debugging
* 📁 Saves sessions in organized, custom directories

---

## Setup

1. **Clone the repository:**

```bash
git clone https://github.com/NehanZ/Docu.git
cd Docu
```

2. **Set up API credentials:**
   This tool uses Gemini AI. Create a `.env` file in the project root with your API key and URL:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_API_URL=your_api_url_here
```

3. **Change permissions and install globally (optional):**

```bash
chmod +x docu
sudo mv docu /usr/local/bin/
```

4. **Run the tool:**

```bash
docu start
```

---

## Usage

* Start a session: `docu start --name session_name --save saving dir`
* Add a comment: `docu --comment "your note"`
* Mask sensitive outputs: `docu mask` 
* AI-assisted summaries: `docu askai`

---

## Notes

* Make sure `.env` is configured before running, otherwise AI features won’t work.
* All logs are saved under `~/Documents/docu/` by default.

