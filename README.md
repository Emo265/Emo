# Emo
Full Automated Ai content video creator
# requirements.txt
openai>=1.0.0
transformers>=4.36.0
torch>=2.0.0
diffusers>=0.25.0
accelerate>=0.25.0
moviepy>=1.0.3
gtts>=2.3.0
python-dotenv>=1.0.0
Pillow>=10.0.0
requests>=2.31.0
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for the Emo video creator."""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    
    # Model settings
    TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-3.5-turbo")
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "stabilityai/stable-diffusion-2-1")
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")  # For OpenAI TTS, or use gTTS
    
    # Output directories
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
    
    # Video settings
    FPS = int(os.getenv("FPS", 24))
    VIDEO_RESOLUTION = tuple(map(int, os.getenv("VIDEO_RESOLUTION", "1920x1080").split("x")))
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        # text_generator.py
import openai
from config import Config

class TextGenerator:
    """Generate script content using OpenAI GPT."""
    
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.model = Config.TEXT_MODEL
    
    def generate_script(self, topic: str, max_tokens: int = 500) -> str:
        """Generate a video script based on a topic."""
        prompt = f"Write a short, engaging video script about {topic}. The script should be suitable for a 60-second video, with clear narration and visual cues."
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative scriptwriter for AI-generated videos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            script = response.choices[0].message.content.strip()
            return script
        except Exception as e:
            raise RuntimeError(f"Text generation failed: {e}")
            # image_generator.py
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
import os
from config import Config

class ImageGenerator:
    """Generate images using Stable Diffusion."""
    
    def __init__(self):
        self.pipe = StableDiffusionPipeline.from_pretrained(
            Config.IMAGE_MODEL,
            torch_dtype=torch.float16,
            use_auth_token=Config.HUGGINGFACE_TOKEN
        )
        self.pipe = self.pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    
    def generate_image(self, prompt: str, output_path: str) -> str:
        """Generate a single image from a text prompt."""
        try:
            with torch.no_grad():
                image = self.pipe(prompt).images[0]
            image.save(output_path)
            return output_path
        except Exception as e:
            raise RuntimeError(f"Image generation failed: {e}")
    
    def generate_sequence(self, prompts: list, output_dir: str) -> list:
        """Generate a sequence of images for a list of prompts."""
        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        for i, prompt in enumerate(prompts):
            path = os.path.join(output_dir, f"frame_{i:04d}.png")
            self.generate_image(prompt, path)
            image_paths.append(path)
        return image_paths
        # audio_generator.py
from gtts import gTTS
import os
from config import Config

class AudioGenerator:
    """Generate narration audio from text."""
    
    def generate_audio(self, text: str, output_path: str) -> str:
        """Convert text to speech using gTTS."""
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            raise RuntimeError(f"Audio generation failed: {e}")
            # video_compiler.py
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx import resize
import os
from config import Config

class VideoCompiler:
    """Compile images and audio into a final video."""
    
    def __init__(self):
        self.fps = Config.FPS
        self.resolution = Config.VIDEO_RESOLUTION
    
    def create_video(self, image_paths: list, audio_path: str, output_path: str) -> str:
        """Combine image sequence with audio to create a video."""
        # Load audio to get duration
        audio = AudioFileClip(audio_path)
        total_duration = audio.duration
        
        # Calculate duration per image
        duration_per_image = total_duration / len(image_paths)
        
        # Create clips for each image
        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(duration_per_image)
            clip = clip.resize(self.resolution)
            clips.append(clip)
        
        # Concatenate all image clips
        video = concatenate_videoclips(clips, method="compose")
        
        # Set audio
        video = video.set_audio(audio)
        
        # Write final video
        video.write_videofile(output_path, fps=self.fps, codec='libx264', audio_codec='aac')
        
        # Close clips to free memory
        audio.close()
        video.close()
        for clip in clips:
            clip.close()
        
        return output_path
        # main.py
import os
import uuid
from config import Config
from text_generator import TextGenerator
from image_generator import ImageGenerator
from audio_generator import AudioGenerator
from video_compiler import VideoCompiler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmoVideoCreator:
    """Orchestrates the entire automated video creation process."""
    
    def __init__(self):
        self.text_gen = TextGenerator()
        self.image_gen = ImageGenerator()
        self.audio_gen = AudioGenerator()
        self.video_comp = VideoCompiler()
    
    def create_video(self, topic: str, output_filename: str = None) -> str:
        """
        Generate a full video from a topic.
        
        Args:
            topic: The subject of the video.
            output_filename: Optional output filename (without path).
            
        Returns:
            Path to the generated video file.
        """
        # Generate unique session ID for temporary files
        session_id = str(uuid.uuid4())
        temp_dir = os.path.join(Config.TEMP_DIR, session_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Step 1: Generate script
            logger.info(f"Generating script for topic: {topic}")
            script = self.text_gen.generate_script(topic)
            logger.info(f"Script: {script[:100]}...")
            
            # Step 2: Split script into visual segments (simple heuristic)
            # For simplicity, we split by sentences or use a more advanced NLP approach.
            # Here we'll just use periods as separators.
            visual_prompts = [s.strip() + "." for s in script.split(".") if s.strip()]
            if not visual_prompts:
                visual_prompts = [script]
            
            # Step 3: Generate images for each visual prompt
            logger.info(f"Generating {len(visual_prompts)} images...")
            image_dir = os.path.join(temp_dir, "images")
            image_paths = self.image_gen.generate_sequence(visual_prompts, image_dir)
            
            # Step 4: Generate audio narration
            logger.info("Generating audio narration...")
            audio_path = os.path.join(temp_dir, "narration.mp3")
            self.audio_gen.generate_audio(script, audio_path)
            
            # Step 5: Compile video
            logger.info("Compiling final video...")
            if output_filename is None:
                output_filename = f"{topic.replace(' ', '_')}_{session_id[:8]}.mp4"
            output_path = os.path.join(Config.OUTPUT_DIR, output_filename)
            self.video_comp.create_video(image_paths, audio_path, output_path)
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            raise
        finally:
            # Optional: Clean up temp directory
            # import shutil
            # shutil.rmtree(temp_dir, ignore_errors=True)
            pass

def main():
    """Entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Emo - Fully Automated AI Content Video Creator")
    parser.add_argument("topic", help="Topic for the video")
    parser.add_argument("--output", "-o", help="Output filename (default: topic_timestamp.mp4)")
    args = parser.parse_args()
    
    creator = EmoVideoCreator()
    creator.create_video(args.topic, args.output)

if __name__ == "__main__":
    main()
    # .env.example
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_TOKEN=your_huggingface_token_here
TEXT_MODEL=gpt-3.5-turbo
IMAGE_MODEL=stabilityai/stable-diffusion-2-1
TTS_MODEL=tts-1
OUTPUT_DIR=./output
TEMP_DIR=./temp
FPS=24
VIDEO_RESOLUTION=1920x1080
