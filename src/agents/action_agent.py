"""
Agent for extracting action items and decisions from meeting transcripts
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
import json
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ActionExtractionAgent(BaseAgent):
    """Extracts action items, decisions, and tasks from meeting transcripts"""
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for action extraction"""
        template = """You are an AI assistant specialized in analyzing meeting transcripts to extract actionable items.

Your task is to analyze the following meeting transcript and identify:
1. **Action Items**: Specific tasks assigned to individuals with deadlines
2. **Decisions Made**: Important decisions reached during the meeting
3. **Follow-ups**: Items that need future discussion or clarification
4. **Commitments**: Promises or commitments made by participants

Meeting Transcript:
{transcript}

Speaker Information:
{speaker_info}

Return your analysis in the following JSON format:
{{
    "action_items": [
        {{
            "assignee": "person name or UNKNOWN",
            "task": "clear description of the task",
            "deadline": "deadline if mentioned or null",
            "priority": "high/medium/low",
            "context": "relevant context from the meeting"
        }}
    ],
    "decisions": [
        {{
            "decision": "clear statement of the decision",
            "decision_maker": "who made the decision or COLLECTIVE",
            "rationale": "reasoning behind the decision if mentioned",
            "impact": "expected impact or implications"
        }}
    ],
    "follow_ups": [
        {{
            "topic": "topic that needs follow-up",
            "reason": "why it needs follow-up",
            "suggested_action": "recommended next steps"
        }}
    ],
    "commitments": [
        {{
            "person": "who made the commitment",
            "commitment": "what they committed to",
            "timeline": "when if mentioned"
        }}
    ]
}}

Be specific and extract all relevant information. If no items exist for a category, return an empty list.
"""
        return PromptTemplate(
            template=template,
            input_variables=["transcript", "speaker_info"]
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract actions from meeting data
        
        Args:
            input_data: Dictionary with 'transcript' and 'segments'
            
        Returns:
            Dictionary with extracted actions, decisions, etc.
        """
        logger.info("Extracting actions and decisions...")
        
        # Prepare transcript
        transcript = self._format_transcript(input_data.get("segments", []))
        
        # Prepare speaker info
        speaker_info = self._format_speaker_info(input_data.get("segments", []))
        
        # Format prompt
        prompt = self.format_prompt(
            transcript=transcript,
            speaker_info=speaker_info
        )
        
        # Invoke LLM
        response = self.invoke_llm(prompt)
        
        # Parse JSON response
        try:
            result = json.loads(response)
            logger.info(
                f"Extracted: {len(result.get('action_items', []))} actions, "
                f"{len(result.get('decisions', []))} decisions"
            )
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "action_items": [],
                "decisions": [],
                "follow_ups": [],
                "commitments": [],
                "raw_response": response
            }
    
    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format segments into readable transcript"""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            text = seg.get("text", "")
            timestamp = seg.get("start", 0)
            
            lines.append(f"[{timestamp:.1f}s] {speaker}: {text}")
        
        return "\n".join(lines)
    
    def _format_speaker_info(self, segments: List[Dict]) -> str:
        """Format speaker statistics"""
        speakers = {}
        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")
            if speaker not in speakers:
                speakers[speaker] = {
                    "segments": 0,
                    "total_time": 0
                }
            speakers[speaker]["segments"] += 1
            speakers[speaker]["total_time"] += seg.get("end", 0) - seg.get("start", 0)
        
        info_lines = []
        for speaker, stats in speakers.items():
            info_lines.append(
                f"- {speaker}: {stats['segments']} segments, "
                f"{stats['total_time']:.1f}s total speaking time"
            )
        
        return "\n".join(info_lines)

