# 🎯 Getting Started: Your First 30 Minutes

A practical, step-by-step guide to get your Meeting Intelligence Platform running.

---

## ⏱️ Timeline

- **Minutes 0-5**: Environment setup
- **Minutes 5-10**: Configuration
- **Minutes 10-25**: Model downloads
- **Minutes 25-30**: First meeting analysis

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed
- [ ] 8GB RAM available
- [ ] 10GB disk space free
- [ ] Internet connection (for model downloads)
- [ ] OpenAI API key OR Google Gemini key
- [ ] HuggingFace account & token

---

## 🚀 Step-by-Step Guide

### Step 1: Initial Setup (5 minutes)

```powershell
# You're already in the audio_ML directory

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Verify Python version
python --version  # Should be 3.11 or higher

# Run setup script
python scripts/setup.py
```

**Expected output:**
```
✅ Created: data/uploads
✅ Created: data/outputs
✅ Created: models/cache
✅ Created config.env from example
```

---

### Step 2: Get API Keys (5 minutes)

#### Option A: OpenAI (Recommended for Best Quality)

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)

#### Option B: Google Gemini (Free Tier Available)

1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Copy the key

#### HuggingFace (Required for Diarization)

1. Go to https://huggingface.co/settings/tokens
2. Create a token with "read" access
3. Accept the license at: https://huggingface.co/pyannote/speaker-diarization-3.1
4. Copy the token

---

### Step 3: Configure (2 minutes)

Edit `config.env` with your favorite text editor:

```env
# Essential keys - Add your actual keys here!
OPENAI_API_KEY=sk-your-actual-key-here
HUGGINGFACE_TOKEN=hf_your-actual-token-here

# OR if using Google Gemini instead
GOOGLE_API_KEY=your-google-key-here

# Optional (for experiment tracking)
WANDB_API_KEY=your-wandb-key-here
```

**Save the file!**

---

### Step 4: Install Dependencies (5 minutes)

```powershell
# Install all required packages
pip install -r requirements.txt

# This will install:
# - PyTorch & audio libraries
# - Whisper, Pyannote, SpeechBrain
# - FastAPI & Streamlit
# - LangChain & LLM clients
```

**Note**: This may take 5-10 minutes depending on your internet speed.

---

### Step 5: Download Models (15 minutes)

```powershell
# Download all AI models
python scripts/download_models.py
```

**What's downloading:**
- ✅ WhisperX (large-v2) - ~3GB
- ✅ Pyannote Diarization - ~500MB
- ✅ SpeechBrain Emotion Model - ~400MB

**Expected output:**
```
Downloading Whisper model...
✅ Whisper model downloaded successfully

Downloading diarization model...
✅ Diarization model downloaded successfully

Downloading emotion detection model...
✅ Emotion model downloaded successfully
```

**Troubleshooting:**
- If diarization fails: Check HF token and license acceptance
- If slow: Models are large, be patient!
- If error: Check your API keys in config.env

---

### Step 6: Start the Application (2 minutes)

#### Option A: Docker (Recommended)

```powershell
# Start everything with one command
docker-compose up --build

# Wait for:
# ✅ Redis: ready
# ✅ API: healthy
# ✅ Frontend: running
```

**Access**:
- Frontend: http://localhost:8501
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Option B: Manual (Two Terminals)

**Terminal 1 - API:**
```powershell
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
streamlit run src/frontend/app.py
```

---

### Step 7: Process Your First Meeting (5 minutes)

#### If you have a meeting recording:

1. Open http://localhost:8501
2. Click "Choose an audio file"
3. Select your WAV/MP3 file
4. Click "🚀 Process Meeting"
5. Watch the progress bar!

#### If you don't have a recording:

Use a sample from the internet:
```powershell
# Download a sample
# (You can use any short audio file or recording)
```

Or create a test:
```powershell
# Record a short message using your voice recorder
# Save as "test_meeting.wav"
# Upload via the web interface
```

---

## 🎉 You're Done! What to Expect

### Processing (2-5 minutes for a 10-minute meeting)

**Progress Stages:**
- ⏳ 10%: Loading audio
- ⏳ 35%: Identifying speakers
- ⏳ 50%: Transcribing speech
- ⏳ 70%: Detecting emotions
- ⏳ 90%: Analyzing with AI agents
- ✅ 100%: Complete!

### Results View

You'll see:
1. **Executive Summary**
   - Meeting duration, speakers, key metrics
   - Overall mood and tone

2. **Interactive Visualizations**
   - Speaker timeline (who spoke when)
   - Emotion timeline (mood changes)
   - Speaking time distribution

3. **Detailed Transcript**
   - Color-coded by speaker
   - With emotion labels
   - Timestamped

4. **Action Items**
   - Task assignments
   - Priorities
   - Deadlines

5. **Decisions Made**
   - What was decided
   - Who decided
   - Rationale

6. **Sentiment Analysis**
   - Per-speaker emotions
   - Meeting dynamics
   - Engagement levels

---

## 🔍 Verify Everything Works

### 1. Check API Health

```powershell
# In browser or terminal
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "message": "All systems operational"
}
```

### 2. Test the Frontend

1. Open http://localhost:8501
2. Should see: "🎙️ Meeting Intelligence Platform"
3. Sidebar should show "⚙️ Configuration"
4. Click "Check API Health" → Should see "✅ API is healthy"

### 3. Run Tests

```powershell
# Run test suite
pytest tests/ -v

# Should see all tests passing
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Module not found"

**Solution:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 2: "CUDA out of memory"

**Solution:**
Edit `config.env`:
```env
WHISPER_MODEL=medium  # Use smaller model
```

### Issue 3: "Diarization model failed"

**Solution:**
1. Go to https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree" to accept license
3. Create token with read access
4. Update `HUGGINGFACE_TOKEN` in config.env

### Issue 4: "Port already in use"

**Solution:**
```powershell
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process or use different port
uvicorn src.api.main:app --port 8001
```

### Issue 5: "API not responding"

**Solution:**
1. Check if API is running: `curl http://localhost:8000/health`
2. Check Docker logs: `docker-compose logs -f api`
3. Check config.env has all required keys

---

## 📊 Understanding Your First Results

### Good Signs ✅

- **Transcription accurate**: Check if text matches audio
- **Speakers identified**: Multiple speakers labeled (SPEAKER_00, SPEAKER_01, etc.)
- **Emotions detected**: Each segment has emotion labels
- **Actions extracted**: AI found actionable items
- **Decisions captured**: Important decisions listed

### If Results Seem Off ⚠️

1. **Poor transcription**:
   - Check audio quality (background noise?)
   - Try different Whisper model

2. **Speaker confusion**:
   - Specify number of speakers manually
   - Ensure speakers don't overlap too much

3. **Wrong emotions**:
   - Emotion detection works best with clear speech
   - Some emotions harder to detect than others

4. **No actions found**:
   - AI might not find actions if meeting is informal
   - Try adjusting LLM temperature in config

---

## 🎯 Next Steps

### Immediate
- [ ] Process 2-3 more meetings
- [ ] Explore different visualization options
- [ ] Download results as JSON
- [ ] Try the API docs (http://localhost:8000/docs)

### This Week
- [ ] Customize agent prompts for your use case
- [ ] Set up W&B experiment tracking
- [ ] Test with longer meetings (30+ minutes)
- [ ] Share with team members

### This Month
- [ ] Fine-tune on your meeting data
- [ ] Deploy to staging environment
- [ ] Integrate with calendar/email
- [ ] Build custom reports

---

## 💡 Pro Tips

1. **Start with short meetings** (5-10 min) to get familiar
2. **Check audio quality** before processing (clear speech, low noise)
3. **Use GPU if available** for 5-10x speed improvement
4. **Monitor W&B dashboard** to track model performance
5. **Experiment with prompts** to improve agent outputs
6. **Cache results** - re-processing same file uses cache
7. **Download JSON** for custom analysis/integration

---

## 📚 Where to Go Next

| Want to... | Read this... |
|------------|-------------|
| Understand the system | ARCHITECTURE.md |
| Deploy to production | DEPLOYMENT.md |
| See all features | PROJECT_SUMMARY.md |
| Troubleshoot issues | README.md → FAQ section |
| Customize agents | src/agents/ → Edit prompts |
| Add new features | ARCHITECTURE.md → Extensions |

---

## 🆘 Need Help?

1. **Check logs**: `logs/` directory or `docker-compose logs`
2. **Read docs**: Start with README.md
3. **Test components**: `python scripts/test_pipeline.py`
4. **API docs**: http://localhost:8000/docs
5. **GitHub Issues**: Report bugs or ask questions

---

## ✅ Success Checklist

After 30 minutes, you should have:

- [x] Virtual environment set up
- [x] API keys configured
- [x] Dependencies installed
- [x] Models downloaded
- [x] Application running
- [x] First meeting processed
- [x] Results viewed in UI
- [x] API health verified

**If all checked: Congratulations! 🎉 You're ready to analyze meetings with AI!**

---

**Happy analyzing! 🎙️ Your AI meeting assistant is ready!**

