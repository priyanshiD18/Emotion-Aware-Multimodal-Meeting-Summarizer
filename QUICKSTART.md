# 🚀 Quick Start Guide

Get up and running with the Meeting Intelligence Platform in minutes!

## Prerequisites

- Python 3.11 or higher
- 8GB RAM minimum (16GB recommended)
- GPU optional but recommended for faster processing

## 1. Installation

### Step 1: Clone and Setup

```bash
# Navigate to project directory
cd audio_ML

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup script
python scripts/setup.py
```

### Step 2: Configure API Keys

Edit `config.env` and add your API keys:

```env
# Required for LLM agents
OPENAI_API_KEY=your_openai_key_here
# OR
GOOGLE_API_KEY=your_google_gemini_key_here

# Required for speaker diarization
HUGGINGFACE_TOKEN=your_hf_token_here

# Optional for experiment tracking
WANDB_API_KEY=your_wandb_key_here
```

**Getting API Keys:**

- **OpenAI**: https://platform.openai.com/api-keys
- **Google Gemini**: https://ai.google.dev/
- **HuggingFace**: https://huggingface.co/settings/tokens
  - Accept license for diarization model: https://huggingface.co/pyannote/speaker-diarization-3.1
- **Weights & Biases**: https://wandb.ai/authorize

### Step 3: Download Models

```bash
# Download all required models (may take 10-20 minutes)
python scripts/download_models.py
```

## 2. Quick Test

### Option A: Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# Access:
# - API: http://localhost:8000
# - Frontend: http://localhost:8501
# - API Docs: http://localhost:8000/docs
```

### Option B: Manual Start

**Terminal 1 - Start API:**
```bash
uvicorn src.api.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run src/frontend/app.py
```

## 3. Process Your First Meeting

### Using the Web Interface

1. Open http://localhost:8501
2. Upload a meeting audio file (.wav, .mp3, .m4a)
3. Click "Process Meeting"
4. View results with interactive visualizations

### Using the API

```bash
# Upload file
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@your_meeting.wav"

# Start analysis (use file_id from upload response)
curl -X POST "http://localhost:8000/api/v1/analyze?file_id=YOUR_FILE_ID&enable_emotion=true"

# Check status (use task_id from analyze response)
curl "http://localhost:8000/api/v1/status/YOUR_TASK_ID"

# Get results
curl "http://localhost:8000/api/v1/result/YOUR_TASK_ID"
```

### Using Python Script

```python
from pathlib import Path
from src.api.pipeline import MeetingPipeline

# Initialize pipeline
pipeline = MeetingPipeline()

# Process meeting
result = pipeline.process_meeting(
    audio_path=Path("your_meeting.wav"),
    num_speakers=None,  # Auto-detect
    enable_emotion=True,
    enable_context=True
)

# Access results
print(f"Duration: {result['duration']:.1f}s")
print(f"Speakers: {', '.join(result['speakers'])}")
print(f"Action Items: {len(result['action_items'])}")
print(f"Decisions: {len(result['decisions'])}")
```

## 4. Test with Sample

```bash
# Test the pipeline with a sample audio file
python scripts/test_pipeline.py data/sample_meeting.wav
```

## 5. API Documentation

Once the API is running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Issues

### Issue: CUDA Out of Memory

**Solution**: Use CPU or smaller models
```env
# In config.env
WHISPER_MODEL=medium  # or small, base
```

### Issue: Diarization Model Not Loading

**Solution**: 
1. Accept the model license on HuggingFace
2. Create a token with read access
3. Add token to `config.env`

### Issue: Slow Processing

**Solutions**:
- Use GPU if available
- Use smaller Whisper model
- Disable emotion detection for faster processing

## Next Steps

- Read the full README.md for detailed documentation
- Explore different LLM providers (OpenAI vs Google)
- Fine-tune emotion detection on your domain
- Set up W&B for experiment tracking
- Deploy to cloud (GCP, AWS, Azure)

## Support

- **Issues**: Open a GitHub issue
- **Documentation**: See README.md
- **API Docs**: http://localhost:8000/docs

---


