import os
import torch
from loguru import logger
from transformers import pipeline

_audio_pipeline = None

def load_audio_ml_model():
    global _audio_pipeline
    if _audio_pipeline is None:
        try:
            device = 0 if torch.cuda.is_available() else -1
            logger.info("Loading audio ML pipeline (MelodyMachine/Deepfake-audio-detection-V2)...")
            _audio_pipeline = pipeline(
                "audio-classification", 
                model="MelodyMachine/Deepfake-audio-detection-V2", 
                device=device
            )
            logger.info("Audio ML pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load audio ML model: {e}")

def analyze_audio_ml(wav_path: str) -> dict:
    load_audio_ml_model()
    if _audio_pipeline is None:
        return {"fake_probability": 0.5, "label": "unknown", "error": True}
    
    try:
        # Pipeline accepts path or bytes. Passing the 16kHz WAV path.
        results = _audio_pipeline(wav_path)
        
        # Parse standard huggingface audio-classification output
        fake_prob = 0.5
        # Example output: [{'score': 0.9, 'label': 'spoof'}, {'score': 0.1, 'label': 'bonafide'}]
        # or [{'score': 0.8, 'label': 'fake'}, {'score': 0.2, 'label': 'real'}]
        for res in results:
            label = res['label'].lower()
            if "fake" in label or "spoof" in label:
                fake_prob = float(res['score'])
                break
            if "real" in label or "bonafide" in label:
                fake_prob = 1.0 - float(res['score'])
                
        return {
            "fake_probability": fake_prob,
            "label": "FAKE" if fake_prob > 0.5 else "REAL",
            "model_used": "Wav2Vec2 (EN/HI Deepfake)",
            "error": False
        }
    except Exception as e:
        logger.error(f"Audio ML analysis failed: {e}")
        return {"fake_probability": 0.5, "label": "error", "error": True}
