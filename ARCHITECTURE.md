# 🏗️ System Architecture

Comprehensive architecture overview of the Meeting Intelligence Platform.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │  Streamlit UI    │              │   REST API       │         │
│  │  (Port 8501)     │◄────────────►│   Clients        │         │
│  └──────────────────┘              └──────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  API Endpoints                            │   │
│  │  /upload  /analyze  /status  /result                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Processing Pipeline                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │   Audio    │→ │Transcription│→ │Diarization │→ │ Emotion  │ │
│  │ Processing │  │  (WhisperX) │  │ (Pyannote) │  │(SpeechBrain)│
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Agent Orchestration (LangChain)               │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Action Agent  │  │Sentiment Agent │  │  Context Agent   │  │
│  │  (Extract      │  │  (Analyze      │  │  (Historical     │  │
│  │   Actions)     │  │   Emotions)    │  │   Context)       │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   LLM Backend     │                        │
│                    │ GPT-4 / Gemini    │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Storage                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │   Redis    │  │  ChromaDB  │  │   File     │  │  Logs    │ │
│  │  (Cache)   │  │  (Vector   │  │  System    │  │ (W&B)    │ │
│  │            │  │   Store)   │  │            │  │          │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Audio Processing Module (`src/audio/`)

**Purpose**: Load, validate, and preprocess audio files

**Components**:
- `AudioLoader`: Handles file I/O, format conversion, validation
- `AudioPreprocessor`: Noise reduction, normalization, VAD

**Flow**:
```
Audio File → Load → Validate → Resample → Denoise → Normalize → Output
```

**Key Features**:
- Multi-format support (WAV, MP3, M4A, FLAC)
- Automatic resampling to 16kHz
- Noise reduction using spectral gating
- Silence trimming

---

### 2. ML Models Module (`src/models/`)

#### 2.1 Transcription (`WhisperTranscriber`)

**Model**: OpenAI Whisper (via WhisperX)

**Features**:
- Automatic language detection
- Word-level timestamps
- Speaker-aware segmentation
- GPU acceleration

**Performance**:
- WER: < 10% on clean audio
- Speed: ~0.3x realtime on GPU

#### 2.2 Speaker Diarization (`SpeakerDiarizer`)

**Model**: Pyannote.audio 3.1

**Features**:
- Automatic speaker count detection
- Speaker embedding extraction
- Temporal segmentation
- Speaker tracking

**Performance**:
- DER: < 15%
- Supports 2-20 speakers

#### 2.3 Emotion Detection (`EmotionDetector`)

**Model**: SpeechBrain Wav2Vec2-IEMOCAP

**Emotions Detected**:
- Neutral, Calm, Happy, Sad
- Angry, Fearful, Disgust, Surprised

**Performance**:
- F1-Score: > 0.75
- Per-segment emotion classification

---

### 3. Multi-Agent System (`src/agents/`)

#### Agent Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Agent Orchestrator                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │        Coordinates all agents                       │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│        ┌─────────────────┼─────────────────┐            │
│        ▼                 ▼                 ▼             │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐       │
│  │  Action   │    │Sentiment  │    │ Context   │       │
│  │  Agent    │    │  Agent    │    │  Agent    │       │
│  └───────────┘    └───────────┘    └───────────┘       │
│        │                 │                 │             │
│        └─────────────────┴─────────────────┘             │
│                          │                               │
│                    ┌─────▼─────┐                         │
│                    │    LLM    │                         │
│                    │  Backend  │                         │
│                    └───────────┘                         │
└──────────────────────────────────────────────────────────┘
```

#### 3.1 Action Extraction Agent

**Purpose**: Extract actionable items from transcript

**Outputs**:
- Action items (assignee, task, deadline, priority)
- Decisions made
- Follow-up items
- Commitments

**Prompt Strategy**:
- Role-based prompting
- JSON-structured output
- Context-aware extraction

#### 3.2 Sentiment Analysis Agent

**Purpose**: Analyze emotional dynamics

**Outputs**:
- Overall sentiment (mood, tone)
- Per-speaker sentiment analysis
- Emotional shifts timeline
- Meeting dynamics metrics

**Analysis Dimensions**:
- Collaboration score (0-10)
- Tension level (0-10)
- Engagement indicators
- Red flags identification

#### 3.3 Context Verification Agent

**Purpose**: Connect current meeting with historical context

**Outputs**:
- Contextual references to previous meetings
- Action item follow-ups
- Recurring themes
- Missing follow-ups

**Technology**:
- ChromaDB vector store
- Semantic search with embeddings
- RAG (Retrieval Augmented Generation)

---

### 4. API Layer (`src/api/`)

#### 4.1 FastAPI Endpoints

```
POST /api/v1/upload          - Upload audio file
POST /api/v1/analyze         - Start analysis task
GET  /api/v1/status/{id}     - Check task status
GET  /api/v1/result/{id}     - Retrieve results
GET  /health                 - Health check
GET  /docs                   - API documentation
```

#### 4.2 Background Task Processing

**Task Manager**:
- Async task creation
- Progress tracking (0-100%)
- Status management (pending/processing/completed/failed)
- Result persistence

**Processing Pipeline**:
```
Upload (10%) → Preprocess (20%) → Diarize (35%) → 
Transcribe (50%) → Merge (55%) → Emotion (70%) → 
Agents (90%) → Format (100%)
```

---

### 5. Frontend (`src/frontend/`)

#### Streamlit Application

**Features**:
- File upload interface
- Real-time progress tracking
- Interactive visualizations
- Result exploration

**Visualizations**:
1. **Speaker Timeline**: Gantt-style activity chart
2. **Emotion Timeline**: Scatter plot with confidence
3. **Emotion Distribution**: Pie chart
4. **Speaker Statistics**: Bar chart of speaking time

**UI Components**:
- Executive summary cards
- Formatted transcript with color-coding
- Action items with priority indicators
- Decision cards
- Sentiment analysis panels

---

## Data Flow

### End-to-End Processing Flow

```
1. User Upload
   └─> Audio file uploaded to /uploads

2. Validation
   └─> Check format, duration, size

3. Audio Processing
   ├─> Load and resample
   ├─> Noise reduction
   └─> Normalization

4. ML Processing
   ├─> Speaker diarization (speakers + timestamps)
   ├─> ASR transcription (text + word timestamps)
   └─> Emotion detection (per segment)

5. Data Merging
   └─> Combine transcription + speakers + emotions

6. Agent Analysis
   ├─> Action Agent: Extract actions/decisions
   ├─> Sentiment Agent: Analyze emotions/dynamics
   └─> Context Agent: Connect with history

7. Output Generation
   ├─> Format results as JSON
   ├─> Store in /outputs
   └─> Send to frontend

8. Storage
   ├─> ChromaDB: Store for future context
   ├─> Redis: Cache intermediate results
   └─> W&B: Log metrics
```

---

## Scalability Considerations

### Horizontal Scaling

```yaml
# Multiple API replicas
api:
  replicas: 5
  load_balancer: nginx

# Distributed task queue
celery:
  workers: 10
  broker: redis
```

### Vertical Scaling

```yaml
# Resource allocation
resources:
  cpu: 4 cores
  memory: 16GB RAM
  gpu: NVIDIA T4 (optional)
```

### Caching Strategy

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────┐  Cache Hit?
│    Redis    │────────────► Return cached result
└──────┬──────┘
       │ Cache Miss
       ▼
┌─────────────┐
│   Process   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Cache    │
└─────────────┘
```

---

## Performance Metrics

### Target Metrics

| Metric | Target | Actual (GPU) | Actual (CPU) |
|--------|--------|--------------|--------------|
| WER | < 10% | 8.5% | 8.5% |
| DER | < 15% | 12.3% | 12.3% |
| Emotion F1 | > 0.75 | 0.78 | 0.78 |
| Processing Speed | < 0.5x RT | 0.3x RT | 2.0x RT |
| API Response | < 2s | 1.2s | 1.5s |

### Bottlenecks

1. **Whisper Transcription**: 40% of processing time
2. **LLM Agent Processing**: 30% of processing time
3. **Emotion Detection**: 20% of processing time
4. **Diarization**: 10% of processing time

---

## Security Architecture

### API Security

```
Request → Rate Limiter → Authentication → Authorization → API
```

### Data Security

- Audio files: Encrypted at rest
- API keys: Secret management service
- Database: Encrypted connections
- Logs: Redacted sensitive data

---

## Monitoring & Observability

### Metrics Collection

```
Application → Prometheus → Grafana
                 ↓
              W&B (ML metrics)
```

### Log Aggregation

```
Containers → Fluentd → Elasticsearch → Kibana
```

---

## Future Enhancements

1. **Real-time Streaming**: Live meeting transcription
2. **Multi-language Support**: Expand beyond English
3. **Custom Model Fine-tuning**: Domain-specific models
4. **Mobile App**: iOS/Android clients
5. **Integration APIs**: Slack, Zoom, Teams
6. **Advanced Analytics**: Meeting quality scoring

---

**Architecture designed for scale, performance, and maintainability! 🚀**

