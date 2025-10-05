"""
Test script for the complete pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.pipeline import MeetingPipeline
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pipeline(audio_path: str):
    """
    Test the complete pipeline with a sample audio file
    
    Args:
        audio_path: Path to audio file
    """
    logger.info("=" * 60)
    logger.info("Testing Meeting Intelligence Pipeline")
    logger.info("=" * 60)
    
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Processing: {audio_path}")
    
    # Initialize pipeline
    pipeline = MeetingPipeline()
    
    # Progress callback
    def progress_callback(progress: int):
        logger.info(f"Progress: {progress}%")
    
    try:
        # Process meeting
        result = pipeline.process_meeting(
            audio_path=audio_path,
            num_speakers=None,  # Auto-detect
            language=None,  # Auto-detect
            enable_emotion=True,
            enable_context=True,
            task_id="test_001",
            progress_callback=progress_callback
        )
        
        # Display results
        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        
        logger.info(f"Meeting ID: {result['meeting_id']}")
        logger.info(f"Duration: {result['duration']:.2f}s")
        logger.info(f"Language: {result['language']}")
        logger.info(f"Speakers: {', '.join(result['speakers'])}")
        logger.info(f"Processing time: {result['processing_time_seconds']:.2f}s")
        logger.info(f"Realtime factor: {result['realtime_factor']:.2f}x")
        
        logger.info(f"\nTranscript segments: {len(result['segments'])}")
        logger.info(f"Action items: {len(result['action_items'])}")
        logger.info(f"Decisions: {len(result['decisions'])}")
        
        # Show first few action items
        if result['action_items']:
            logger.info("\nAction Items:")
            for i, action in enumerate(result['action_items'][:3], 1):
                logger.info(f"  {i}. {action.get('task', '')} ({action.get('assignee', 'UNKNOWN')})")
        
        # Show first few decisions
        if result['decisions']:
            logger.info("\nDecisions:")
            for i, decision in enumerate(result['decisions'][:3], 1):
                logger.info(f"  {i}. {decision.get('decision', '')}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Test completed successfully!")
        logger.info("=" * 60)
        
        # Cleanup
        pipeline.cleanup()
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_pipeline.py <audio_file>")
        print("\nExample:")
        print("  python scripts/test_pipeline.py data/sample_meeting.wav")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    test_pipeline(audio_path)


if __name__ == "__main__":
    main()

