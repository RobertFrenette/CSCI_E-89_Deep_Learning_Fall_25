"""
Audio Processor Module

Handles speech-to-text and text-to-speech conversion.
Domain processor for audio input/output processing.
"""

import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path, whisper_model):
    """
    Convert audio to text using Whisper.
    
    Args:
        audio_path: Path to audio file
        whisper_model: Loaded Whisper model instance
        
    Returns:
        Transcribed text string, or empty string if transcription fails
    """
    if audio_path is None or audio_path == "":
        logger.warning("No audio path provided")
        return ""
    
    try:
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return ""
        
        file_size = os.path.getsize(audio_path)
        if file_size < 1000:
            logger.warning(f"Audio file too small ({file_size} bytes), likely empty")
            return ""
        
        logger.debug(f"Transcribing audio file: {audio_path} ({file_size} bytes)")
        result = whisper_model.transcribe(audio_path, fp16=False)
        transcribed_text = result["text"].strip()
        logger.info(f"Transcription successful: {len(transcribed_text)} characters")
        return transcribed_text
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        return ""


def text_to_speech(text):
    """
    Convert text to speech and save to WAV file.
    Uses macOS 'say' command to generate AIFF, then converts to WAV via ffmpeg.
    
    Args:
        text: Text string to convert to speech
        
    Returns:
        Path to generated WAV file, or None if conversion fails
    """
    try:
        logger.debug(f"Generating speech for {len(text)} characters")
        
        # Create temporary files
        temp_aiff = tempfile.NamedTemporaryFile(delete=False, suffix=".aiff")
        temp_aiff.close()
        
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        output_path = temp_wav.name
        temp_wav.close()
        
        # Use macOS 'say' command to generate AIFF
        subprocess.run(['say', '-o', temp_aiff.name, text], check=True, capture_output=True)
        logger.debug("AIFF file generated")
        
        # Convert AIFF to WAV using ffmpeg for better browser compatibility
        subprocess.run([
            'ffmpeg', '-i', temp_aiff.name, 
            '-y',  # Overwrite output file
            '-ar', '44100',  # Sample rate
            '-ac', '2',  # Stereo
            output_path
        ], check=True, capture_output=True)
        logger.debug("WAV file generated")
        
        # Clean up temporary AIFF file
        os.unlink(temp_aiff.name)
        
        # Verify WAV file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"TTS successful: {output_path}")
            return output_path
        
        logger.error("TTS output file is empty or missing")
        return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"TTS subprocess error: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"TTS error: {e}", exc_info=True)
        return None
