import requests
import os
from typing import Dict, Optional
import json
import streamlit as st

class VideoAutomationPipeline:
    """Automated video generation from scripts using various AI services"""
    
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.synthesia_key = os.getenv("SYNTHESIA_API_KEY")
        self.did_key = os.getenv("DID_API_KEY")  # Alternative to Synthesia
        
    def create_avatar_video(self, script: str, avatar_id: str = "default") -> Dict:
        """Create video using Synthesia API"""
        if not self.synthesia_key:
            return {
                "error": "Synthesia API key not configured", 
                "message": "Add SYNTHESIA_API_KEY to your .env file to enable avatar videos"
            }
            
        headers = {
            "Authorization": f"Bearer {self.synthesia_key}",
            "Content-Type": "application/json"
        }
        
        # Enhanced payload with more options
        payload = {
            "script": script,
            "avatar": avatar_id,
            "voiceId": "en-US-1",
            "title": "AI Tool Discovery Video",
            "description": "Generated from AI Content Agent",
            "visibility": "private",
            "aspectRatio": "16:9"
        }
        
        try:
            response = requests.post(
                "https://api.synthesia.io/v2/videos",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "video_id": result.get("id"),
                    "status": "processing",
                    "message": "Video creation started successfully",
                    "estimated_time": "5-10 minutes"
                }
            else:
                return {
                    "error": f"API Error: {response.status_code}",
                    "message": response.text
                }
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout", "message": "API call took too long"}
        except Exception as e:
            return {"error": "Request failed", "message": str(e)}
    
    def create_text_to_speech(self, script: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> Dict:
        """Generate voiceover using ElevenLabs API"""
        if not self.elevenlabs_key:
            return {
                "error": "ElevenLabs API key not configured",
                "message": "Add ELEVENLABS_API_KEY to your .env file to enable text-to-speech"
            }
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }
        
        payload = {
            "text": script,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                # Save audio file
                audio_filename = f"voiceover_{voice_id[:8]}.mp3"
                with open(audio_filename, "wb") as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "audio_file": audio_filename,
                    "message": "Voiceover generated successfully"
                }
            else:
                return {
                    "error": f"ElevenLabs API Error: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {"error": "Audio generation failed", "message": str(e)}
    
    def create_slideshow_video(self, script: str) -> Dict:
        """Create slideshow-style video with auto-generated slides"""
        # This could be enhanced to:
        # 1. Parse script into sections
        # 2. Generate slides using Canva API
        # 3. Create voiceover with ElevenLabs
        # 4. Combine with FFmpeg
        
        sections = self._parse_script_sections(script)
        
        return {
            "status": "slideshow creation planned",
            "sections_found": len(sections),
            "message": "Slideshow video generation coming in next update",
            "sections": sections[:3]  # Preview first 3 sections
        }
    
    def _parse_script_sections(self, script: str) -> list:
        """Parse script into logical sections for slideshow creation"""
        lines = script.split('\n')
        sections = []
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('#') or line.endswith(':') or 'TIMESTAMP' in line.upper()):
                if current_section:
                    sections.append(current_section.strip())
                current_section = line
            else:
                current_section += f" {line}"
        
        if current_section:
            sections.append(current_section.strip())
            
        return sections
    
    def get_video_status(self, video_id: str) -> Dict:
        """Check status of video generation"""
        if not self.synthesia_key:
            return {"error": "API key not configured"}
            
        headers = {"Authorization": f"Bearer {self.synthesia_key}"}
        
        try:
            response = requests.get(
                f"https://api.synthesia.io/v2/videos/{video_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status check failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def script_to_video(self, script: str, style: str = "avatar", options: Dict = None) -> Dict:
        """Main function to convert script to video"""
        if not script or len(script.strip()) < 10:
            return {"error": "Script too short", "message": "Please provide a longer script"}
        
        options = options or {}
        
        if style == "avatar":
            avatar_id = options.get("avatar_id", "default")
            return self.create_avatar_video(script, avatar_id)
            
        elif style == "slideshow":
            return self.create_slideshow_video(script)
            
        elif style == "voiceover":
            voice_id = options.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
            return self.create_text_to_speech(script, voice_id)
            
        else:
            return {
                "error": "Unknown video style", 
                "message": "Available styles: avatar, slideshow, voiceover"
            }
    
    def get_available_options(self) -> Dict:
        """Get available video creation options based on configured APIs"""
        options = {
            "styles": [],
            "apis_configured": {},
            "estimated_costs": {}
        }
        
        if self.synthesia_key:
            options["styles"].append("avatar")
            options["apis_configured"]["synthesia"] = True
            options["estimated_costs"]["avatar"] = "$5-15 per video"
        
        if self.elevenlabs_key:
            options["styles"].append("voiceover")
            options["apis_configured"]["elevenlabs"] = True
            options["estimated_costs"]["voiceover"] = "$0.50-2 per video"
        
        options["styles"].append("slideshow")
        options["estimated_costs"]["slideshow"] = "Coming soon"
        
        return options

# Streamlit UI integration functions
def display_video_generation_ui(script_content: str, script_title: str):
    """Display video generation interface in Streamlit"""
    
    st.subheader("🎥 Video Generation")
    
    # Initialize video pipeline
    if 'video_pipeline' not in st.session_state:
        st.session_state.video_pipeline = VideoAutomationPipeline()
    
    # Get available options
    options = st.session_state.video_pipeline.get_available_options()
    
    if not options["styles"]:
        st.warning("No video APIs configured. Add API keys to .env file to enable video generation.")
        return
    
    # Video style selection
    col1, col2 = st.columns(2)
    
    with col1:
        video_style = st.selectbox(
            "Video Style",
            options["styles"],
            help="Choose video generation method"
        )
    
    with col2:
        if video_style in options["estimated_costs"]:
            st.info(f"Cost: {options['estimated_costs'][video_style]}")
    
    # Generation button
    if st.button(f"🎬 Generate {video_style.title()} Video", key=f"video_{script_title[:10]}"):
        with st.spinner(f"Creating {video_style} video..."):
            video_result = st.session_state.video_pipeline.script_to_video(
                script_content, 
                style=video_style
            )
            
            if "success" in video_result and video_result["success"]:
                st.success("✅ " + video_result["message"])
                
                if "video_id" in video_result:
                    st.info(f"Video ID: {video_result['video_id']}")
                    st.write(f"Estimated completion: {video_result.get('estimated_time', 'Unknown')}")
                
                if "audio_file" in video_result:
                    st.audio(video_result["audio_file"])
                    
            elif "error" in video_result:
                st.error("❌ " + video_result["error"])
                if "message" in video_result:
                    st.write(video_result["message"])
            else:
                st.json(video_result)

def add_video_generation_to_scripts():
    """Helper function to show where to add video generation in main app"""
    return """
    # Add this after each script is displayed:
    
    display_video_generation_ui(script_data['script'], script_data['idea'])
    """