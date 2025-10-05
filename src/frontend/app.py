"""
Streamlit frontend for Meeting Intelligence Platform
"""

import streamlit as st
import requests
import json
from pathlib import Path
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

# Configure page
st.set_page_config(
    page_title="Meeting Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .speaker-segment {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 3px solid;
    }
    .action-item {
        background-color: #fff3cd;
        padding: 0.8rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .decision-item {
        background-color: #d4edda;
        padding: 0.8rem;
        border-radius: 0.3rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">🎙️ Meeting Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("AI-powered meeting transcription, speaker diarization, emotion detection, and intelligent summarization")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Analysis options
        st.subheader("Analysis Options")
        enable_emotion = st.checkbox("Enable Emotion Detection", value=True)
        enable_context = st.checkbox("Enable Context Verification", value=True)
        num_speakers = st.number_input(
            "Number of Speakers (0 = auto-detect)",
            min_value=0,
            max_value=20,
            value=0
        )
        
        st.divider()
        
        # API health check
        st.subheader("System Status")
        if st.button("Check API Health"):
            try:
                response = requests.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    st.success("✅ API is healthy")
                else:
                    st.error("❌ API is not responding")
            except Exception as e:
                st.error(f"❌ API connection failed: {e}")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📊 Analysis Results", "📚 Meeting History"])
    
    with tab1:
        show_upload_tab(enable_emotion, enable_context, num_speakers)
    
    with tab2:
        show_results_tab()
    
    with tab3:
        show_history_tab()


def show_upload_tab(enable_emotion: bool, enable_context: bool, num_speakers: int):
    """Upload and processing tab"""
    
    st.markdown('<div class="section-header">Upload Meeting Audio</div>', unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "flac", "ogg"],
        help="Supported formats: WAV, MP3, M4A, FLAC, OGG"
    )
    
    if uploaded_file is not None:
        # Show file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Filename", uploaded_file.name)
        with col2:
            st.metric("Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB")
        with col3:
            st.metric("Type", uploaded_file.type)
        
        # Process button
        if st.button("🚀 Process Meeting", type="primary", use_container_width=True):
            process_meeting(uploaded_file, enable_emotion, enable_context, num_speakers)


def process_meeting(uploaded_file, enable_emotion: bool, enable_context: bool, num_speakers: int):
    """Process uploaded meeting"""
    
    # Upload file
    with st.spinner("Uploading file..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f"{API_BASE_URL}/api/v1/upload", files=files)
            response.raise_for_status()
            
            upload_result = response.json()
            file_id = upload_result["file_id"]
            
            st.success(f"✅ File uploaded successfully! ID: {file_id}")
            
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
            return
    
    # Start analysis
    with st.spinner("Starting analysis..."):
        try:
            params = {
                "file_id": file_id,
                "enable_emotion": enable_emotion,
                "enable_context": enable_context
            }
            
            if num_speakers > 0:
                params["num_speakers"] = num_speakers
            
            response = requests.post(f"{API_BASE_URL}/api/v1/analyze", params=params)
            response.raise_for_status()
            
            analysis_result = response.json()
            task_id = analysis_result["task_id"]
            
            st.info(f"📊 Analysis started! Task ID: {task_id}")
            
            # Store task ID in session state
            st.session_state["current_task_id"] = task_id
            st.session_state["current_file_name"] = uploaded_file.name
            
        except Exception as e:
            st.error(f"❌ Analysis failed to start: {e}")
            return
    
    # Monitor progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/status/{task_id}")
            response.raise_for_status()
            
            status = response.json()
            progress = status["progress"]
            task_status = status["status"]
            
            progress_bar.progress(progress)
            status_text.text(f"Status: {task_status} - Progress: {progress}%")
            
            if task_status == "completed":
                st.success("✅ Analysis complete!")
                st.session_state["latest_result_task_id"] = task_id
                time.sleep(1)
                st.rerun()
                break
            elif task_status == "failed":
                st.error(f"❌ Analysis failed: {status.get('error', 'Unknown error')}")
                break
            
            time.sleep(2)
            
        except Exception as e:
            st.error(f"❌ Error checking status: {e}")
            break


def show_results_tab():
    """Show analysis results"""
    
    st.markdown('<div class="section-header">Analysis Results</div>', unsafe_allow_html=True)
    
    # Task ID input
    task_id = st.text_input(
        "Task ID",
        value=st.session_state.get("latest_result_task_id", ""),
        help="Enter task ID to view results"
    )
    
    if st.button("Load Results") or task_id:
        if not task_id:
            st.warning("Please enter a task ID")
            return
        
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/result/{task_id}")
            response.raise_for_status()
            
            result = response.json()
            display_results(result)
            
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Failed to load results: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")


def display_results(result: dict):
    """Display comprehensive results"""
    
    # Executive Summary
    st.markdown('<div class="section-header">📋 Executive Summary</div>', unsafe_allow_html=True)
    
    exec_summary = result.get("executive_summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", f"{result.get('duration', 0):.1f}s")
    with col2:
        st.metric("Speakers", len(result.get("speakers", [])))
    with col3:
        st.metric("Action Items", len(result.get("action_items", [])))
    with col4:
        st.metric("Decisions", len(result.get("decisions", [])))
    
    # Mood and Tone
    if exec_summary.get("overall_mood"):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Overall Mood:** {exec_summary.get('overall_mood', 'N/A').title()}")
        with col2:
            st.info(f"**Meeting Tone:** {exec_summary.get('overall_tone', 'N/A').title()}")
    
    # Speaker Timeline Visualization
    st.markdown('<div class="section-header">👥 Speaker Timeline</div>', unsafe_allow_html=True)
    plot_speaker_timeline(result.get("segments", []))
    
    # Emotion Timeline
    st.markdown('<div class="section-header">😊 Emotion Timeline</div>', unsafe_allow_html=True)
    plot_emotion_timeline(result.get("segments", []))
    
    # Speaker Statistics
    st.markdown('<div class="section-header">📊 Speaker Statistics</div>', unsafe_allow_html=True)
    display_speaker_stats(result.get("diarization_stats", {}))
    
    # Transcript
    st.markdown('<div class="section-header">📝 Full Transcript</div>', unsafe_allow_html=True)
    display_transcript(result.get("segments", []))
    
    # Action Items
    st.markdown('<div class="section-header">✅ Action Items</div>', unsafe_allow_html=True)
    display_action_items(result.get("action_items", []))
    
    # Decisions
    st.markdown('<div class="section-header">⚖️ Decisions Made</div>', unsafe_allow_html=True)
    display_decisions(result.get("decisions", []))
    
    # Sentiment Analysis
    st.markdown('<div class="section-header">💭 Sentiment Analysis</div>', unsafe_allow_html=True)
    display_sentiment_analysis(result.get("speaker_sentiments", []), result.get("overall_sentiment", {}))
    
    # Download results
    st.markdown('<div class="section-header">💾 Download Results</div>', unsafe_allow_html=True)
    st.download_button(
        label="Download JSON",
        data=json.dumps(result, indent=2),
        file_name=f"meeting_analysis_{result.get('meeting_id', 'unknown')}.json",
        mime="application/json"
    )


def plot_speaker_timeline(segments: list):
    """Plot interactive speaker timeline"""
    
    if not segments:
        st.info("No segments available")
        return
    
    # Create timeline data
    timeline_data = []
    for seg in segments:
        timeline_data.append({
            "Speaker": seg.get("speaker", "UNKNOWN"),
            "Start": seg.get("start", 0),
            "End": seg.get("end", 0),
            "Duration": seg.get("end", 0) - seg.get("start", 0),
            "Text": seg.get("text", "")[:100] + "..."
        })
    
    df = pd.DataFrame(timeline_data)
    
    # Create Gantt-style chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Speaker",
        color="Speaker",
        hover_data=["Text"],
        title="Speaker Activity Timeline"
    )
    
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(height=400)
    
    st.plotly_chart(fig, use_container_width=True)


def plot_emotion_timeline(segments: list):
    """Plot emotion timeline"""
    
    if not segments or not any(seg.get("emotion") for seg in segments):
        st.info("No emotion data available")
        return
    
    # Emotion color mapping
    emotion_colors = {
        "neutral": "#95a5a6",
        "happy": "#f39c12",
        "sad": "#3498db",
        "angry": "#e74c3c",
        "fearful": "#9b59b6",
        "calm": "#1abc9c",
        "surprised": "#e67e22",
        "disgust": "#34495e"
    }
    
    # Create scatter plot
    emotion_data = []
    for seg in segments:
        if seg.get("emotion"):
            emotion_data.append({
                "Time": seg.get("start", 0),
                "Speaker": seg.get("speaker", "UNKNOWN"),
                "Emotion": seg.get("emotion", "unknown"),
                "Confidence": seg.get("emotion_confidence", 0)
            })
    
    df = pd.DataFrame(emotion_data)
    
    fig = px.scatter(
        df,
        x="Time",
        y="Speaker",
        color="Emotion",
        size="Confidence",
        hover_data=["Emotion", "Confidence"],
        title="Emotion Detection Over Time",
        color_discrete_map=emotion_colors
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Emotion distribution
    emotion_counts = df["Emotion"].value_counts()
    fig_pie = px.pie(
        values=emotion_counts.values,
        names=emotion_counts.index,
        title="Emotion Distribution",
        color=emotion_counts.index,
        color_discrete_map=emotion_colors
    )
    st.plotly_chart(fig_pie, use_container_width=True)


def display_speaker_stats(stats: dict):
    """Display speaker statistics"""
    
    speaker_times = stats.get("speaker_times", {})
    
    if not speaker_times:
        st.info("No speaker statistics available")
        return
    
    # Create bar chart
    speakers = list(speaker_times.keys())
    times = list(speaker_times.values())
    
    fig = go.Figure(data=[
        go.Bar(x=speakers, y=times, marker_color='lightblue')
    ])
    
    fig.update_layout(
        title="Speaking Time by Speaker",
        xaxis_title="Speaker",
        yaxis_title="Time (seconds)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_transcript(segments: list):
    """Display formatted transcript"""
    
    if not segments:
        st.info("No transcript available")
        return
    
    # Group by speaker for better readability
    for seg in segments:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg.get("text", "")
        start = seg.get("start", 0)
        emotion = seg.get("emotion", "")
        
        # Color code by speaker
        speaker_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        color_idx = hash(speaker) % len(speaker_colors)
        color = speaker_colors[color_idx]
        
        emotion_tag = f" [{emotion}]" if emotion else ""
        
        st.markdown(
            f'<div class="speaker-segment" style="border-color: {color}">'
            f'<strong>{speaker}</strong> <small>({start:.1f}s){emotion_tag}</small><br>{text}'
            f'</div>',
            unsafe_allow_html=True
        )


def display_action_items(action_items: list):
    """Display action items"""
    
    if not action_items:
        st.info("No action items identified")
        return
    
    for item in action_items:
        assignee = item.get("assignee", "UNKNOWN")
        task = item.get("task", "")
        priority = item.get("priority", "medium")
        deadline = item.get("deadline", "Not specified")
        
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        
        st.markdown(
            f'<div class="action-item">'
            f'{priority_emoji} <strong>{assignee}</strong><br>'
            f'{task}<br>'
            f'<small>Priority: {priority} | Deadline: {deadline}</small>'
            f'</div>',
            unsafe_allow_html=True
        )


def display_decisions(decisions: list):
    """Display decisions"""
    
    if not decisions:
        st.info("No decisions recorded")
        return
    
    for decision in decisions:
        decision_text = decision.get("decision", "")
        decision_maker = decision.get("decision_maker", "UNKNOWN")
        impact = decision.get("impact", "Not specified")
        
        st.markdown(
            f'<div class="decision-item">'
            f'<strong>Decision:</strong> {decision_text}<br>'
            f'<strong>Decision Maker:</strong> {decision_maker}<br>'
            f'<strong>Impact:</strong> {impact}'
            f'</div>',
            unsafe_allow_html=True
        )


def display_sentiment_analysis(speaker_sentiments: list, overall_sentiment: dict):
    """Display sentiment analysis"""
    
    if overall_sentiment:
        st.subheader("Overall Sentiment")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Mood:** {overall_sentiment.get('mood', 'N/A')}")
            st.write(f"**Tone:** {overall_sentiment.get('tone', 'N/A')}")
        with col2:
            st.write(f"**Description:** {overall_sentiment.get('description', 'N/A')}")
    
    if speaker_sentiments:
        st.subheader("Speaker Sentiments")
        for sentiment in speaker_sentiments:
            speaker = sentiment.get("speaker", "UNKNOWN")
            emotion = sentiment.get("dominant_emotion", "unknown")
            engagement = sentiment.get("engagement_level", "unknown")
            
            st.write(f"**{speaker}**: {emotion} (Engagement: {engagement})")


def show_history_tab():
    """Show meeting history"""
    
    st.markdown('<div class="section-header">Meeting History</div>', unsafe_allow_html=True)
    st.info("📚 Meeting history feature coming soon! This will show all previous meetings with quick access to summaries.")


if __name__ == "__main__":
    # Initialize session state
    if "current_task_id" not in st.session_state:
        st.session_state["current_task_id"] = None
    if "latest_result_task_id" not in st.session_state:
        st.session_state["latest_result_task_id"] = None
    
    main()

