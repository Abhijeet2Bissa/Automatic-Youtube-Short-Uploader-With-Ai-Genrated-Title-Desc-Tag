# Automatic YouTube Shorts Uploader

An automated YouTube Shorts uploader built with **Python, Google Gemini AI, YouTube Data API, and FFmpeg**.

The bot automatically selects a video, analyzes the entire video with AI, generates YouTube metadata, converts horizontal videos into vertical Shorts format, uploads the video, and archives it after a successful upload.

---

# ✨ Features

- 🎲 **Random Video Selection**
  - Automatically selects a random video from the `shorts/` folder.

- 🤖 **AI-Generated Metadata**
  - Uses Google Gemini to watch and analyze the entire video.
  - Automatically generates:
    - Catchy title
    - Funny description
    - Relevant hashtags
    - 20–30 YouTube tags

- 📱 **Automatic Horizontal → Vertical Conversion**
  - Detects horizontal videos automatically.
  - Converts them to **9:16 (1080×1920)**.
  - Adds a blurred version of the video as the background.
  - Keeps the original video centered and visible.
  - Vertical videos are left unchanged.

- 🔐 **YouTube Channel Verification**
  - Verifies the authenticated YouTube channel against the configured channel handle.
  - Prevents accidentally uploading to the wrong channel.

- 📤 **Automatic YouTube Upload**
  - Uploads the processed video automatically.
  - Video visibility can be configured in the code.

- 🗑️ **Automatic File Cleanup**
  - After a successful upload, the original source video is deleted.
  - The uploaded/processed version is copied to `uploaded/`.

- 🛡️ **Failure Protection**
  - If Gemini fails, YouTube authentication fails, channel verification fails, or the upload fails, the original video is **not deleted**.

- ⚡ **Fully Automatic**
  - Once started, the bot performs the entire workflow automatically and exits after completion.

---

# 🛠️ Requirements

Before starting, install:

- Python 3.10+
- FFmpeg
- A Google Cloud project
- Gemini API key
- YouTube Data API enabled
- YouTube OAuth Desktop credentials

---

# 🚀 Setup

## 1. Clone the Repository

```bash
git clone https://github.com/Abhijeet2Bissa/Automatic-Youtube-Short-Uploader-With-Ai-Genrated-Title-Desc-Tag.git

cd Automatic-Youtube-Short-Uploader-With-Ai-Genrated-Title-Desc-Tag 
```

## 2. Install Python Dependencies

* Open a terminal inside the project folder and run:

```bash
pip install -r requirements.txt
```

## 3. Install FFmpeg

FFmpeg is required for converting horizontal videos into vertical 9:16 videos.

### Windows

You can install it with:

```powershell
winget install Gyan.FFmpeg
```

Verify the installation:

```powershell
ffmpeg -version
```

<br>
<br>


# 🔑 Gemini API Setup

## 4. Create a Gemini API Key

Go to:

https://aistudio.google.com/

Create an API key.

Then in `.env` file in the project folder:

Edit This Field With Your API KEY

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

<br>
<br>


# ▶️ YouTube API Setup

## 5. Create a Google Cloud Project

Go to:

https://console.cloud.google.com/

Create a project for the uploader.

<br>

## 6. Enable YouTube Data API

Inside Google Cloud:

1. Open **APIs & Services**
2. Open **Library**
3. Search for **YouTube Data API v3**
4. Click **Enable**

<br>
<br>


## 7. Configure OAuth

Open:

**Google Auth Platform → Audience**

Add the Google account that owns the YouTube channel you want to use as a **Test User**.

Then create an OAuth client:

1. Go to **Google Auth Platform → Clients**
2. Create an **OAuth Client**
3. Select **Desktop app**
4. Download the credentials

Rename the downloaded file to:

```text
client_secret.json
```

And copy it to your **PROJECT FOLDER**

<br>

# 📁 Project Structure

Your project should look like:

```text
Automatic-YouTube-Shorts-Uploader/
│
├── bot.py
├── requirements.txt
├── .env
├── client_secret.json
│
├── shorts/
│   └── Put your videos here
│
├── uploaded/
│   └── Successfully uploaded videos
│
└── processed/
    └── Temporary converted videos
```
<br>
<br>

# 🎬 Add Your Shorts

Put your videos inside:

```text
shorts/
```

The bot supports common formats such as:
```text
.mp4
.mov
.avi
.mkv
.webm
```

<br>
<br>

# ⚙️ Configuration

Change settings at the top of the env.

```python
TARGET_HANDLE = <YOUR_YOUTUBE_USERNAME>
```

For example:

```python
TARGET_HANDLE = @editosm4
```
Change this to the YouTube channel you want the bot to verify.

#### OPTIONAL :-

You can also change the folders in your python code:

```python
SHORTS_FOLDER = Path("shorts")
UPLOADED_FOLDER = Path("uploaded")
```

<br>
<br>

# ▶️ Run the Bot

Open a terminal in the project folder:

```bash
python bot.py
```
##### On the first run, Google will open a browser window for YouTube authorization.

##### After authorization, the bot will save:

**youtube_token.json**

##### so you normally won't need to log in again.



<br>
<br>
<br>
<br>

# 🔄 How It Works

```text
📁 shorts/
     ↓
🎲 Select random video
     ↓
📐 Check orientation
     ↓
↔️ Horizontal?
   ├── YES → 🌀 Convert to 9:16
   └── NO  → Continue
     ↓
🤖 Gemini watches entire video
     ↓
📝 Generate title
📝 Generate description
🏷️ Generate tags
     ↓
🔐 Verify YouTube channel
     ↓
📤 Upload to YouTube
     ↓
✅ Upload successful?
   ├── NO  → 🛡️ Keep original
   └── YES → 📦 Save uploaded version
              ↓
           🗑️ Delete original
              ↓
           👋 Exit
```

<br>
<br>
<br>
<br>

# SUPPPORT

### 🫰YOU CAN SUPPORT US BY REPORTING ISSUE AND SOLVING THEM ALSO CONTACT ME IF YOU WANT TO SPONSER OR HELP US MAKE THIS PROJECT MORE USABLE  

##### CONTACT - codingtecher@gmail.com

##### DISCORD - @abhijeetbissa_55697