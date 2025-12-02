# LinkedIn Lead Generation Bot 🚀

A robust, Python-based automation tool designed to scrape "Vendor Empanelment" and staffing leads directly from LinkedIn.

Built with **Playwright**, this bot automates the process of searching for recent posts, filtering for relevant leads, and extracting contact details (Emails & Phone Numbers) into a CSV file. It features a **"Hybrid Authentication"** mode that uses your local Chrome profile to bypass LinkedIn's login captchas and security checks safely.

## 🌟 Key Features

  
  * **🔍 Smart Filtering:** Automatically filters search results by "Posts" and "Date Posted" to find the freshest leads.
  * **📜 Infinite Scroll Handling:** robust scrolling logic to trigger lazy-loading and capture deep search results.
  * **🧠 Regex Extraction:** Built-in Regex patterns to automatically identify and extract:
      * **Emails:** (e.g., `hr@company.com`)
      * **Phone Numbers:** (Supports various formats like `+91...`, `040...`)
  * **📂 Auto-Export:** Saves structured data (Name, Post Text, Email, Phone, URL) directly to a CSV file in your `Downloads` folder with a timestamp.

## 🛠️ Tech Stack

  * **Language:** Python 3.x
  * **Core Library:** [Playwright](https://playwright.dev/python/) (Browser Automation)
  * **Standard Libraries:** `csv`, `re`, `os`, `datetime`

## ⚙️ Prerequisites

Before running the bot, ensure you have the following installed:

1.  **Python 3.7+**
2.  **Google Chrome** (The actual browser, not just Chromium)
3.  **VS Code** (Recommended IDE)

## 📦 Installation

1.  **Clone the repository**

    ```bash
    git clone https://github.com/YourUsername/linkedin-lead-bot.git
    cd linkedin-lead-bot
    ```

2.  **Create a Virtual Environment (Recommended)**

    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**

    ```bash
    pip install playwright
    python -m playwright install
    ```

## 🚀 Usage

### 1\. Close Chrome

**CRITICAL STEP:** You must close **all** open Google Chrome windows on your computer. The bot needs to "lock" your user profile to run as *you*.

  * *Tip: If it fails, run `taskkill /F /IM chrome.exe` in your terminal to force-kill hidden Chrome processes.*

### 2\. Configure the Script

Open `bot.py` and check the `SEARCH_TERM` variable if you want to search for something other than "vendor empanelment":

```python
SEARCH_TERM = "vendor empanelment"
```

### 3\. Run the Bot

Execute the script from your terminal:

```bash
python bot.py
```

### 4\. Watch the Magic

  * The bot will launch a Chrome window (logged in as you).
  * It will navigate to the LinkedIn feed.
  * It will type the search query, filter by "Posts", and scroll.
  * **Result:** Check your `Downloads` folder for a file named `linkedin_data_YYYY-MM-DD_HH-MM-SS.csv`.

## 📂 Project Structure

```text
├── bot.py               # Main "Hybrid" script (Recommended for use)
├── linkedin_login.py    # Legacy script (Login via password - prone to Captchas)
├── linkden.py           # Simple session test script
├── requirements.txt     # List of python dependencies
└── README.md            # Project documentation
```

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Automated scraping of LinkedIn may violate their Terms of Service. Use this tool responsibly and at your own risk. The author is not responsible for any account restrictions or bans.

-----

### **Next Steps for Your Repo**

1.  **Create a `.gitignore` file**: You definitely don't want to accidentally upload your CSV files or virtual environment to GitHub. Create a file named `.gitignore` and add:
    ```text
    venv/
    __pycache__/
    *.csv
    ```
2.  **Upload:** `git add .` -\> `git commit -m "Initial commit"` -\> `git push`.
