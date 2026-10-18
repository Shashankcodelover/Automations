# 🤖 24/7 Auto-Publishing using GitHub Actions (100% Free & No Breaks!)

This guide explains how to set up **GitHub Actions** in the cloud to run your YouTube Auto-Publisher 24/7 entirely for free, with zero database setup and **without needing n8n**.

Because GitHub runs your code on its massive enterprise servers, this setup **never sleeps, never goes down, and never breaks**!

---

## 🛠️ Step 1: Run the Google Authentication Script (Only ONCE)

We need to generate a secure file called `token.json` that gives our Python script access to Google Drive and YouTube upload.

1. Open your terminal/command prompt on your local computer.
2. Install the necessary Google libraries by running:
   ```bash
   pip install google-auth-oauthlib google-api-python-client google-auth-httplib2
   ```
3. Run the generator script in your project folder:
   ```bash
   python get_google_token.py
   ```
4. A web browser tab will open automatically. Log in with your **AI veo3 Gmail Account** (the one for YouTube Channel B).
5. Click **Advanced** ➔ **Go to My App (unsafe)** ➔ click **Allow / Continue** to authorize the app.
6. Look back at your terminal. You will see a success message!
7. In your folder, a file named **`token.json`** has now been created. Open it with Notepad, select all the text, and copy it.

---

## ☁️ Step 2: Create a Private GitHub Repository

We will put our script on GitHub so it can run on their servers.

1. Go to **[https://github.com/](https://github.com/)** and log in (or create a free account).
2. Click the **`+`** icon in the top-right corner and select **New repository** (or go to `https://github.com/new`).
3. Set these settings:
   - **Repository name:** `youtube-veo3-uploader`
   - **Visibility:** Set to **Private** 🔒 (This is critical to keep your code and files secure!)
   - **Initialize this repository with:** Check **Add a README file**.
4. Click **Create repository** at the bottom.

---

## ⚙️ Step 3: Add Your Secrets to GitHub

We must save your keys securely so the background script can use them.

1. Inside your new GitHub repository, click on the **Settings** tab at the top.
2. In the left sidebar, click **Secrets and variables** ➔ **Actions**.
3. Under the **Repository secrets** section, click **New repository secret** to add these **4 secrets** one by one:

| Secret Name | What to Paste in the Value |
| :--- | :--- |
| **`GOOGLE_TOKEN_JSON`** | *Paste all the text from the `token.json` file you generated in Step 1.* |
| **`GEMINI_API_KEY`** | `your_gemini_api_key_here` |
| **`TELEGRAM_BOT_TOKEN`** | `your_telegram_bot_token_here` |
| **`TELEGRAM_CHAT_ID`** | `your_telegram_chat_id_here` |

---

## 📂 Step 4: Upload the Python Script

1. In your GitHub repository, click the **Code** tab at the top.
2. Click **Add file** ➔ **Create new file**.
3. **Name your file:** `cloud_publisher.py`
4. **Content:** Copy and paste the entire contents of the `cloud_publisher.py` file from your computer folder.
5. Click **Commit changes...** at the bottom, and click **Commit changes** to save.

---

## ⏰ Step 5: Add the Automatic 24/7 Timer (The Workflow File)

This file tells GitHub to run your uploader on a schedule.

1. Click **Add file** ➔ **Create new file**.
2. **Name your file:** `.github/workflows/autopublish.yml` (make sure to include the dots and slashes!).
3. **Content:** Copy and paste this exact block:

```yaml
name: YouTube Auto-Publish

on:
  repository_dispatch:
    types: [trigger-publish]  # Allows triggering instantly at the exact second via Cron-Job.org!
  workflow_dispatch:
    # Allows you to click a button to run the upload manually anytime you want!

jobs:
  publish:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install FFmpeg
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg

    - name: Install Python Dependencies
      run: |
        pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib yt-dlp

    - name: Run Auto-Publisher
      env:
        GOOGLE_TOKEN_JSON: ${{ secrets.GOOGLE_TOKEN_JSON }}
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      run: python cloud_publisher.py
```
4. Click **Commit changes...** ➔ **Commit changes**.

---

## ⚡ Step 6: Setup Cron-Job.org for Perfect 6:00 PM Timings (No Delays!)

To bypass GitHub's unpredictable scheduler delays, we will set up **Cron-Job.org** (100% Free) to trigger GitHub instantly at exactly 6:00 PM IST.

### 1. Generate a GitHub Personal Access Token (PAT)
This token lets Cron-Job.org securely call your GitHub repository to trigger the uploader.
1. On GitHub, click your profile picture (top-right) ➔ **Settings**.
2. Scroll to the very bottom of the left sidebar and click **Developer settings**.
3. Click **Personal access tokens** ➔ select **Fine-grained tokens**.
4. Click **Generate new token** (sign in if asked).
5. Set these settings:
   - **Token name:** `Cron Job Trigger`
   - **Expiration:** Choose **Custom** and set it to a date far in the future (e.g. 1 year).
   - **Repository access:** Choose **Only select repositories** ➔ select your **`youtube-veo3-uploader`** repository.
   - **Permissions:** Click **Repository permissions** ➔ find **Actions** ➔ change access from No Access to **Read and Write**.
6. Scroll to the bottom and click **Generate token**.
7. **Copy the token immediately!** (You won't be able to see it again).

### 2. Set Up the Trigger on Cron-Job.org
1. Go to **[https://cron-job.org/](https://cron-job.org/)** and sign up for a free account.
2. In your dashboard, click **Create Cron Job** (top-right).
3. Set these settings:
   - **Title:** `Trigger YouTube Publish`
   - **URL:** Paste this link (replace `YOUR_GITHUB_USERNAME` with your actual username):
     👉 `https://api.github.com/repos/YOUR_GITHUB_USERNAME/youtube-veo3-uploader/dispatches`
   - **Execution schedule:** Choose **User-defined** ➔ set it to run **Daily** at **18:00** (6:00 PM) and select **Asia/Kolkata** (Indian Time) in the timezone selector!
   - **Request method:** Change from `GET` to **`POST`**.
   - **Request headers:** Click **Add header** to add **3 headers**:
     * Header 1:
       - Key: `Authorization`
       - Value: `Bearer YOUR_GITHUB_PERSONAL_ACCESS_TOKEN` *(Replace with the token you copied in Step 1!)*
     * Header 2:
       - Key: `Accept`
       - Value: `application/vnd.github+json`
     * Header 3:
       - Key: `User-Agent`
       - Value: `cron-job-trigger`
   - **Request body:** Type this exact JSON block:
     `{ "event_type": "trigger-publish" }`
4. Click **Create** at the bottom.

---

## 🎵 How to Customize Your Background Music (ELI12)

If you want **total control** over the music that plays on your cat videos:
1. Go to your GitHub repository dashboard.
2. Click **Add file** ➔ **Create new file**.
3. Name your file: `music/.keep` (this creates a folder named `music` in your repository).
4. Download your favorite cute, funny, or emotional royalty-free MP3 tracks (for example, from the **YouTube Audio Library** or **Pixabay Music**).
5. Upload these `.mp3` files into the `music/` folder in your GitHub repository.
6. The script will **automatically detect your custom folder** and pick a random song from it for each video, instead of using the default internet fallback music!

---

## 🚀 How to Run a 10-Minute Test

You don't need to wait for 6:05 PM to test it! We enabled a manual "Run" button for you.

1. In your GitHub repository, click on the **Actions** tab at the top.
2. In the left sidebar, click on **YouTube Auto-Publish**.
3. You will see a light-blue bar on the right side with a dropdown button called **Run workflow** ➔ Click it and select **Run workflow**.
4. In less than 15 seconds, a job will start running. Click on it to see the live console logs!
5. It will automatically download the video from your Drive, shift the audio speed, overlay music, fetch the tags from Gemini, upload it to YouTube, and alert you on Telegram!

Once this test succeeds, **you are completely done!** You can shut down your computer. GitHub will handle all uploads on schedule without fail!
