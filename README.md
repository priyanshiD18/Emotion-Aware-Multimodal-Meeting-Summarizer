# 🎙️ Agentic AI Meeting Intelligence Platform

A production-ready AI pipeline for meeting transcription, speaker diarization, emotion detection, and intelligent summarization using multi-agent orchestration.

## 🌟 Features

- **High-Accuracy Transcription**: WhisperX for state-of-the-art ASR
- **Speaker Diarization**: Automatic speaker identification and labeling
- **Emotion Detection**: Real-time emotion and sentiment analysis per speaker
- **Multi-Agent Intelligence**: LangChain agents for action extraction, sentiment analysis, and context verification
- **Structured Outputs**: JSON-formatted summaries with decisions, action items, and speaker insights
- **Real-Time Visualization**: Interactive emotion timelines and speaker analytics
- **Production-Ready**: FastAPI backend, Streamlit frontend, Docker support

## 📁 Project Structure


```
audio_ML/
├── src/                          # Source code
│   ├── audio/                    # Audio processing
│   │   ├── loader.py            # File I/O & validation
│   │   └── preprocessing.py     # Noise reduction, normalization
│   │
│   ├── models/                   # ML models
│   │   ├── transcription.py     # WhisperX integration
│   │   ├── diarization.py       # Pyannote speaker diarization
│   │   └── emotion.py           # SpeechBrain emotion detection
│   │
│   ├── agents/                   # Multi-agent system
│   │   ├── base_agent.py        # Base agent class
│   │   ├── action_agent.py      # Action extraction
│   │   ├── sentiment_agent.py   # Sentiment analysis
│   │   ├── context_agent.py     # Historical context
│   │   └── orchestrator.py      # Agent coordination
│   │
│   ├── api/                      # FastAPI backend
│   │   ├── main.py              # API endpoints
│   │   ├── models.py            # Pydantic models
│   │   ├── pipeline.py          # Processing pipeline
│   │   └── tasks.py             # Task management
│   │
│   ├── frontend/                 # Streamlit UI
│   │   └── app.py               # Web application
│   │
│   └── config.py                 # Configuration management
│
├── scripts/                      # Utility scripts
│   ├── setup.py                 # Initial setup
│   ├── download_models.py       # Model downloads
│   └── test_pipeline.py         # Pipeline testing
│
├── tests/                        # Test suite
│   ├── test_audio_processing.py # Audio tests
│   └── test_api.py              # API tests
│
├── data/                         # Data storage
│   ├── uploads/                 # Uploaded audio
│   ├── outputs/                 # Processing results
│   └── chroma_db/               # Vector database
│
├── models/cache/                 # Model cache
├── logs/                         # Application logs
│
├── requirements.txt              # Python dependencies
├── config.env.example           # Configuration template
├── Dockerfile                    # Docker configuration
├── docker-compose.yml           # Docker orchestration
├── pytest.ini                    # Test configuration
│
├── README.md                     # Main documentation
├── QUICKSTART.md                # Quick start guide
├── ARCHITECTURE.md              # System architecture
├── DEPLOYMENT.md                # Deployment guide
└── LICENSE                       # MIT License

```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys
```

### 2. Model Downloads

```bash
# Download required models
python scripts/download_models.py
```

### 3. Run the Application

```bash
# Start FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# In another terminal, start Streamlit frontend
streamlit run src/frontend/app.py
```

### 4. Run with Docker

```bash
# Build and start services
docker-compose up --build

# Access at:
# - API: http://localhost:8000
# - Frontend: http://localhost:8501
```

## 📊 Usage

### Upload Audio
1. Navigate to http://localhost:8501
2. Upload a meeting recording (.wav, .mp3, .m4a)
3. Click "Process Audio"

### View Results
- **Transcription**: Full transcript with speaker labels
- **Emotion Timeline**: Interactive visualization of emotions over time
- **Summary**: Structured JSON with decisions and action items
- **Analytics**: Speaker statistics and engagement metrics

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_audio_processing.py -v
```

## 📈 MLOps & Monitoring

This project integrates Weights & Biases for experiment tracking:

```bash
# Initialize W&B
wandb login

# Experiments are automatically logged during processing
# View at: https://wandb.ai/your-entity/meeting-intelligence
```

## 🔧 Configuration

Key configurations in `.env`:
- **LLM Provider**: Switch between OpenAI GPT-4 or Google Gemini
- **Model Sizes**: Adjust Whisper model size for speed/accuracy tradeoff
- **Emotion Threshold**: Fine-tune emotion detection sensitivity

## 🚢 Deployment

### Cloud Deployment Options

**Google Cloud Platform**:
```bash
gcloud run deploy meeting-intelligence --source .
```

**AWS Lambda + API Gateway**:
```bash
serverless deploy
```

**Azure Container Apps**:
```bash
az containerapp up --name meeting-intelligence --source .
```

## 📝 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints

- `POST /api/v1/upload`: Upload audio file
- `POST /api/v1/transcribe`: Transcribe audio
- `POST /api/v1/analyze`: Full analysis pipeline
- `GET /api/v1/summary/{task_id}`: Retrieve result
  
---



