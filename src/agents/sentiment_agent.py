"""
Agent for analyzing sentiment and emotional dynamics in meetings
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
import json
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SentimentAnalysisAgent(BaseAgent):
    """Analyzes sentiment and emotional dynamics per speaker"""
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for sentiment analysis"""
        template = """You are an AI assistant specialized in analyzing emotional dynamics and sentiment in meetings.

Your task is to analyze the meeting transcript along with detected emotions to provide insights into:
1. **Overall Sentiment**: The general mood and tone of the meeting
2. **Speaker Sentiments**: Individual sentiment analysis for each speaker
3. **Emotional Shifts**: Significant changes in emotional tone during the meeting
4. **Engagement Levels**: How engaged each participant was
5. **Conflict Indicators**: Any signs of disagreement or tension

Meeting Transcript with Emotions:
{transcript_with_emotions}

Emotion Detection Results:
{emotion_summary}

Return your analysis in the following JSON format:
{{
    "overall_sentiment": {{
        "mood": "positive/neutral/negative/mixed",
        "tone": "collaborative/tense/productive/casual",
        "description": "brief description of overall meeting atmosphere"
    }},
    "speaker_sentiments": [
        {{
            "speaker": "speaker name",
            "dominant_emotion": "primary emotion",
            "sentiment": "positive/neutral/negative",
            "engagement_level": "high/medium/low",
            "key_moments": ["notable emotional moments"],
            "communication_style": "assertive/supportive/analytical/etc"
        }}
    ],
    "emotional_shifts": [
        {{
            "timestamp": "approximate time",
            "from_emotion": "previous emotion",
            "to_emotion": "new emotion",
            "trigger": "what caused the shift",
            "impact": "how it affected the discussion"
        }}
    ],
    "meeting_dynamics": {{
        "collaboration_score": 0-10,
        "tension_level": 0-10,
        "productivity_indicators": ["indicators of productive discussion"],
        "red_flags": ["any concerns or issues noticed"]
    }}
}}

Provide insightful analysis based on both the textual content and emotion detection results.
"""
        return PromptTemplate(
            template=template,
            input_variables=["transcript_with_emotions", "emotion_summary"]
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment from meeting data
        
        Args:
            input_data: Dictionary with 'segments' (with emotion annotations)
            
        Returns:
            Dictionary with sentiment analysis
        """
        logger.info("Analyzing sentiment and emotional dynamics...")
        
        # Format transcript with emotions
        transcript_with_emotions = self._format_transcript_with_emotions(
            input_data.get("segments", [])
        )
        
        # Create emotion summary
        emotion_summary = self._create_emotion_summary(
            input_data.get("segments", [])
        )
        
        # Format prompt
        prompt = self.format_prompt(
            transcript_with_emotions=transcript_with_emotions,
            emotion_summary=emotion_summary
        )
        
        # Invoke LLM
        response = self.invoke_llm(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info("Sentiment analysis complete")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "overall_sentiment": {},
                "speaker_sentiments": [],
                "emotional_shifts": [],
                "meeting_dynamics": {},
                "raw_response": response
            }
    
    def _format_transcript_with_emotions(self, segments: List[Dict]) -> str:
        """Format transcript with emotion annotations"""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "")
            emotion = seg.get("emotion", "unknown")
            confidence = seg.get("emotion_confidence", 0)
            timestamp = seg.get("start", 0)
            
            lines.append(
                f"[{timestamp:.1f}s] {speaker} ({emotion}, {confidence:.2f}): {text}"
            )
        
        return "\n".join(lines)
    
    def _create_emotion_summary(self, segments: List[Dict]) -> str:
        """Create summary of emotion distribution"""
        # Group by speaker
        speaker_emotions = {}
        
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            emotion = seg.get("emotion", "unknown")
            duration = seg.get("end", 0) - seg.get("start", 0)
            
            if speaker not in speaker_emotions:
                speaker_emotions[speaker] = {}
            
            if emotion not in speaker_emotions[speaker]:
                speaker_emotions[speaker][emotion] = 0
            
            speaker_emotions[speaker][emotion] += duration
        
        # Format summary
        summary_lines = []
        for speaker, emotions in speaker_emotions.items():
            total_time = sum(emotions.values())
            emotion_percentages = {
                emotion: (time / total_time) * 100
                for emotion, time in emotions.items()
            }
            
            # Sort by percentage
            sorted_emotions = sorted(
                emotion_percentages.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            emotion_str = ", ".join([
                f"{emotion}: {pct:.1f}%"
                for emotion, pct in sorted_emotions[:3]  # Top 3 emotions
            ])
            
            summary_lines.append(f"{speaker}: {emotion_str}")
        
        return "\n".join(summary_lines)

