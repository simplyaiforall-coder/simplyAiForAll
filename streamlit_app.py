import streamlit as st
import pandas as pd
import os
from openai import OpenAI
import tiktoken
from datetime import datetime, timedelta
import json
import requests
from typing import Dict, List, Optional
import schedule
import time
from google.cloud import storage
from google.oauth2 import service_account

# Add explicit .env loading
from dotenv import load_dotenv
load_dotenv()

# Import Claude if available
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# --- AI Tool Categories and Database ---
AI_TOOL_CATEGORIES = {
    "Text & Writing": {
        "icon": "✍️",
        "tools": {
            "ChatGPT": {
                "description": "Conversational AI for writing, coding, analysis",
                "features": ["Text generation", "Code writing", "Analysis", "Conversation"],
                "pricing": "Free tier + $20/month Pro",
                "best_for": "General purpose AI assistant",
                "website": "https://chat.openai.com",
                "release_date": "2022-11-30"
            },
            "Claude": {
                "description": "AI assistant focused on helpful, harmless, honest responses",
                "features": ["Long context", "Code analysis", "Creative writing", "Document analysis"],
                "pricing": "Free tier + $20/month Pro",
                "best_for": "Document analysis and creative tasks",
                "website": "https://claude.ai",
                "release_date": "2023-03-14"
            },
            "Grammarly": {
                "description": "AI-powered writing assistant and grammar checker",
                "features": ["Grammar checking", "Style suggestions", "Plagiarism detection", "Tone adjustment"],
                "pricing": "Free + $12/month Premium",
                "best_for": "Writing improvement and editing",
                "website": "https://grammarly.com",
                "release_date": "2009-07-01"
            },
            "Jasper": {
                "description": "AI content creation platform for marketing",
                "features": ["Marketing copy", "Blog posts", "Social media", "Email campaigns"],
                "pricing": "$39/month+",
                "best_for": "Marketing content creation",
                "website": "https://jasper.ai",
                "release_date": "2021-01-01"
            }
        }
    },
    "Image & Design": {
        "icon": "🎨",
        "tools": {
            "Canva AI": {
                "description": "Design platform with AI-powered features",
                "features": ["Magic Design", "Background removal", "Text to image", "Brand kit"],
                "pricing": "Free + $15/month Pro",
                "best_for": "Social media graphics and presentations",
                "website": "https://canva.com",
                "release_date": "2013-01-01"
            },
            "Midjourney": {
                "description": "AI image generation from text prompts",
                "features": ["Artistic image generation", "Style variations", "Upscaling", "Custom styles"],
                "pricing": "$10/month+",
                "best_for": "Artistic and creative imagery",
                "website": "https://midjourney.com",
                "release_date": "2022-07-12"
            },
            "DALL-E 3": {
                "description": "OpenAI's image generation model",
                "features": ["Photorealistic images", "Text integration", "Style control", "Safe generation"],
                "pricing": "Included with ChatGPT Plus",
                "best_for": "Realistic image generation",
                "website": "https://openai.com/dall-e-3",
                "release_date": "2023-10-01"
            },
            "Adobe Firefly": {
                "description": "Adobe's AI creative suite",
                "features": ["Text to image", "Generative fill", "Text effects", "Vector generation"],
                "pricing": "Free tier + Creative Cloud",
                "best_for": "Professional design workflow",
                "website": "https://firefly.adobe.com",
                "release_date": "2023-03-21"
            }
        }
    },
    "Video & Audio": {
        "icon": "🎬",
        "tools": {
            "Runway ML": {
                "description": "AI video editing and generation platform",
                "features": ["Text to video", "Video editing", "Green screen", "Motion tracking"],
                "pricing": "$12/month+",
                "best_for": "AI video creation and editing",
                "website": "https://runwayml.com",
                "release_date": "2018-01-01"
            },
            "ElevenLabs": {
                "description": "AI voice synthesis and cloning",
                "features": ["Voice cloning", "Text to speech", "Multiple languages", "Voice editing"],
                "pricing": "Free tier + $5/month+",
                "best_for": "Voiceovers and audio content",
                "website": "https://elevenlabs.io",
                "release_date": "2022-01-01"
            },
            "Synthesia": {
                "description": "AI video creation with virtual presenters",
                "features": ["AI avatars", "Text to video", "Multiple languages", "Custom avatars"],
                "pricing": "$30/month+",
                "best_for": "Training and presentation videos",
                "website": "https://synthesia.io",
                "release_date": "2017-01-01"
            },
            "Descript": {
                "description": "AI-powered video and podcast editing",
                "features": ["Text-based editing", "Voice cloning", "Transcription", "Overdub"],
                "pricing": "Free tier + $12/month+",
                "best_for": "Podcast and video editing",
                "website": "https://descript.com",
                "release_date": "2017-01-01"
            }
        }
    },
    "Productivity & Automation": {
        "icon": "⚡",
        "tools": {
            "Notion AI": {
                "description": "AI-powered workspace and note-taking",
                "features": ["Writing assistance", "Content generation", "Data analysis", "Task automation"],
                "pricing": "$10/month (add-on)",
                "best_for": "Note-taking and project management",
                "website": "https://notion.so",
                "release_date": "2023-02-22"
            },
            "Zapier AI": {
                "description": "Workflow automation with AI",
                "features": ["App integration", "Smart triggers", "Data parsing", "Workflow optimization"],
                "pricing": "Free tier + $20/month+",
                "best_for": "Business process automation",
                "website": "https://zapier.com",
                "release_date": "2011-01-01"
            },
            "Otter.ai": {
                "description": "AI meeting transcription and notes",
                "features": ["Real-time transcription", "Meeting summaries", "Action items", "Speaker identification"],
                "pricing": "Free tier + $10/month+",
                "best_for": "Meeting transcription and notes",
                "website": "https://otter.ai",
                "release_date": "2016-01-01"
            },
            "GitHub Copilot": {
                "description": "AI pair programmer for coding",
                "features": ["Code completion", "Function generation", "Code explanation", "Multiple languages"],
                "pricing": "$10/month",
                "best_for": "Software development",
                "website": "https://github.com/features/copilot",
                "release_date": "2021-06-29"
            }
        }
    },
    "Business & Analytics": {
        "icon": "📊",
        "tools": {
            "Tableau AI": {
                "description": "AI-powered data visualization and analytics",
                "features": ["Automated insights", "Natural language queries", "Predictive analytics", "Data prep"],
                "pricing": "$70/month+",
                "best_for": "Data visualization and business intelligence",
                "website": "https://tableau.com",
                "release_date": "2003-01-01"
            },
            "Salesforce Einstein": {
                "description": "AI for CRM and sales automation",
                "features": ["Lead scoring", "Sales forecasting", "Customer insights", "Automated workflows"],
                "pricing": "Included with Salesforce plans",
                "best_for": "Sales and customer relationship management",
                "website": "https://salesforce.com",
                "release_date": "2016-09-01"
            },
            "MonkeyLearn": {
                "description": "Text analysis and sentiment AI",
                "features": ["Sentiment analysis", "Text classification", "Data extraction", "API integration"],
                "pricing": "Free tier + $299/month+",
                "best_for": "Text analytics and customer feedback",
                "website": "https://monkeylearn.com",
                "release_date": "2014-01-01"
            }
        }
    },
    "Education & Learning": {
        "icon": "📚",
        "tools": {
            "Khan Academy AI": {
                "description": "Personalized AI tutoring (Khanmigo)",
                "features": ["Personalized tutoring", "Homework help", "Progress tracking", "Multiple subjects"],
                "pricing": "Free with Khan Academy",
                "best_for": "Student learning and tutoring",
                "website": "https://khanacademy.org",
                "release_date": "2023-05-01"
            },
            "Duolingo AI": {
                "description": "AI-powered language learning",
                "features": ["Personalized lessons", "Speech recognition", "Adaptive difficulty", "Progress tracking"],
                "pricing": "Free + $7/month Plus",
                "best_for": "Language learning",
                "website": "https://duolingo.com",
                "release_date": "2011-01-01"
            },
            "Coursera AI": {
                "description": "AI-enhanced online learning platform",
                "features": ["Course recommendations", "Skill assessments", "Career guidance", "Personalized paths"],
                "pricing": "Free courses + $39/month+",
                "best_for": "Professional skill development",
                "website": "https://coursera.org",
                "release_date": "2012-01-01"
            }
        }
    }
}

# --- AI Provider Management ---
class AIProvider:
    """Handles multiple AI providers with fallback support"""
    
    def __init__(self):
        # Load API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Initialize clients
        self.openai_client = None
        self.claude_client = None
        
        if self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
            except Exception as e:
                st.error(f"OpenAI initialization failed: {e}")
        
        if self.claude_key and CLAUDE_AVAILABLE:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.claude_key)
            except Exception as e:
                st.error(f"Claude initialization failed: {e}")
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        models = []
        if self.openai_client:
            models.extend(["GPT-3.5 Turbo", "GPT-4", "GPT-4 Turbo"])
        if self.claude_client:
            models.extend(["Claude 3.5 Sonnet", "Claude 3 Haiku"])
        return models
    
    def generate_content(self, prompt: str, model: str = "GPT-3.5 Turbo", 
                        max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Generate content using specified model with fallback"""
        
        try:
            # Try primary model
            if model in ["GPT-3.5 Turbo", "GPT-4", "GPT-4 Turbo"] and self.openai_client:
                return self._openai_generate(prompt, model, max_tokens, temperature)
            elif model in ["Claude 3.5 Sonnet", "Claude 3 Haiku"] and self.claude_client:
                return self._claude_generate(prompt, model, max_tokens, temperature)
            else:
                # Fallback to any available model
                available = self.get_available_models()
                if available:
                    fallback_model = available[0]
                    st.warning(f"⚠️ {model} not available, using {fallback_model}")
                    return self.generate_content(prompt, fallback_model, max_tokens, temperature)
                else:
                    raise Exception("No AI models available")
                    
        except Exception as e:
            st.error(f"Content generation failed: {e}")
            return ""
    
    def _openai_generate(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """OpenAI content generation"""
        model_map = {
            "GPT-3.5 Turbo": "gpt-3.5-turbo",
            "GPT-4": "gpt-4",
            "GPT-4 Turbo": "gpt-4-turbo-preview"
        }
        
        response = self.openai_client.chat.completions.create(
            model=model_map.get(model, "gpt-3.5-turbo"),
            messages=[{"role": "system", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def _claude_generate(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Claude content generation"""
        model_map = {
            "Claude 3.5 Sonnet": "claude-3-5-sonnet-20241022",
            "Claude 3 Haiku": "claude-3-haiku-20240307"
        }
        
        response = self.claude_client.messages.create(
            model=model_map.get(model, "claude-3-5-sonnet-20241022"),
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def get_model_cost(self, model: str) -> float:
        """Get cost per 1K tokens for model"""
        costs = {
            "GPT-3.5 Turbo": 0.002,
            "GPT-4": 0.03,
            "GPT-4 Turbo": 0.01,
            "Claude 3.5 Sonnet": 0.003,
            "Claude 3 Haiku": 0.00025
        }
        return costs.get(model, 0.002)

# Enhanced Content Segment Definitions
CONTENT_SEGMENTS = {
    "AI Education": {
        "icon": "🤖",
        "description": "AI tools, productivity, and technology education",
        "audiences": {
            "Parents": {
                "description": "AI tools for homework help, family productivity, child safety online",
                "focus_areas": ["ChatGPT for homework", "AI safety for kids", "Productivity tools for families"],
                "risk_level": "Family-safe content"
            },
            "Seniors (50+)": {
                "description": "Beginner-friendly AI guidance, accessibility focus",
                "focus_areas": ["Simple AI tools", "Voice assistants", "AI for health tracking"],
                "risk_level": "Beginner-friendly approach"
            },
            "Busy Professionals": {
                "description": "Productivity AI, workflow automation, business tools",
                "focus_areas": ["AI for emails", "Meeting automation", "Workflow optimization"],
                "risk_level": "Professional-grade tools"
            },
            "Stay-at-Home Moms": {
                "description": "Home management, meal planning, family organization",
                "focus_areas": ["Meal planning AI", "Schedule management", "Home automation"],
                "risk_level": "Family-focused solutions"
            },
            "Small Business Owners": {
                "description": "AI for business growth, customer service, marketing",
                "focus_areas": ["Customer service AI", "Marketing automation", "Business analytics"],
                "risk_level": "Business-appropriate tools"
            },
            "Kids (7-12)": {
                "description": "Age-appropriate AI education, creative tools, learning aids",
                "focus_areas": ["AI storytelling", "Educational games", "Creative projects"],
                "risk_level": "Child-safe, supervised use"
            }
        }
    },
    "Finance Education": {
        "icon": "💰",
        "description": "Responsible financial literacy and investing education",
        "audiences": {
            "Young Adults (18-25)": {
                "description": "Basic financial literacy, budgeting, first investments",
                "focus_areas": ["Budgeting apps", "Emergency funds", "Index fund basics", "Student loan management"],
                "risk_level": "Conservative, education-first approach"
            },
            "Adults (26-40)": {
                "description": "Portfolio building, retirement planning, major purchases",
                "focus_areas": ["401k optimization", "House down payments", "Portfolio diversification", "Tax strategies"],
                "risk_level": "Moderate risk tolerance, balanced approach"
            },
            "Middle-aged (41-55)": {
                "description": "Advanced investing, retirement acceleration, college savings",
                "focus_areas": ["Advanced portfolios", "Estate planning", "College funds", "Career transitions"],
                "risk_level": "Balanced approach with risk management"
            },
            "Pre-retirement (55+)": {
                "description": "Capital preservation, income generation, retirement planning",
                "focus_areas": ["Bond strategies", "Dividend investing", "Healthcare costs", "Social Security"],
                "risk_level": "Conservative, income-focused"
            },
            "General Finance": {
                "description": "Universal financial principles for all ages",
                "focus_areas": ["Financial literacy", "Risk management", "Investment basics", "Economic education"],
                "risk_level": "Educational foundation for all levels"
            }
        }
    },
    "Motivational & Inspiration": {
        "icon": "🌟",
        "description": "Positive motivation, inspiration, and wisdom for personal growth",
        "audiences": {
            "Young Adults (18-25)": {
                "description": "Goal-setting, resilience, career motivation, life direction",
                "focus_areas": ["Career goals", "Overcoming setbacks", "Building confidence", "Purpose finding"],
                "risk_level": "Balanced motivation without toxic positivity"
            },
            "Working Professionals": {
                "description": "Work-life balance, leadership, career growth, stress management",
                "focus_areas": ["Leadership wisdom", "Productivity motivation", "Stress relief", "Success principles"],
                "risk_level": "Professional growth with mental health awareness"
            },
            "Parents & Families": {
                "description": "Parenting wisdom, family values, patience, community building",
                "focus_areas": ["Parenting patience", "Family unity", "Community values", "Raising children"],
                "risk_level": "Family-positive, inclusive content"
            },
            "Students & Learners": {
                "description": "Study motivation, learning persistence, knowledge seeking, academic goals",
                "focus_areas": ["Study motivation", "Knowledge seeking", "Academic perseverance", "Learning wisdom"],
                "risk_level": "Educational motivation without pressure"
            },
            "General Inspiration": {
                "description": "Universal wisdom, life lessons, spiritual growth, inner peace",
                "focus_areas": ["Life wisdom", "Inner peace", "Gratitude", "Spiritual reflection", "Character building"],
                "risk_level": "Inclusive wisdom respecting diverse beliefs"
            },
            "Overcoming Challenges": {
                "description": "Resilience, hope during difficulties, strength building, recovery support",
                "focus_areas": ["Building resilience", "Hope in hardship", "Mental strength", "Recovery motivation"],
                "risk_level": "Supportive without replacing professional help"
            }
        }
    },
    "AI Tool Discovery": {
        "icon": "🔍",
        "description": "Latest AI tools, features, comparisons, and tutorials",
        "audiences": {
            "Tech Enthusiasts": {
                "description": "Early adopters interested in cutting-edge AI tools",
                "focus_areas": ["New AI releases", "Beta features", "Technical comparisons", "Advanced use cases"],
                "risk_level": "Technical depth with practical examples"
            },
            "Content Creators": {
                "description": "Creators looking for AI tools to enhance their workflow",
                "focus_areas": ["Content creation tools", "Editing AI", "Automation workflows", "Creative AI"],
                "risk_level": "Creative-focused with ROI considerations"
            },
            "Business Professionals": {
                "description": "Professionals seeking AI tools for productivity and growth",
                "focus_areas": ["Business AI tools", "Productivity automation", "ROI analysis", "Team collaboration"],
                "risk_level": "Business-focused with cost-benefit analysis"
            },
            "Students & Educators": {
                "description": "Educational AI tools for learning and teaching",
                "focus_areas": ["Learning AI", "Study tools", "Teaching aids", "Research assistance"],
                "risk_level": "Educational ethics and responsible use"
            },
            "Beginners": {
                "description": "New users learning about AI capabilities",
                "focus_areas": ["AI basics", "Getting started guides", "Free tools", "Simple tutorials"],
                "risk_level": "Beginner-friendly with safety guidelines"
            }
        }
    }
}

# --- AI Tool Discovery System ---
class AIToolDiscovery:
    """System for discovering and analyzing AI tools"""
    
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
    
    def get_tool_database(self) -> Dict:
        """Get the current AI tool database"""
        return AI_TOOL_CATEGORIES
    
    def search_tools(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search tools by query and optional category"""
        results = []
        categories_to_search = [category] if category else AI_TOOL_CATEGORIES.keys()
        
        for cat_name in categories_to_search:
            if cat_name in AI_TOOL_CATEGORIES:
                category_data = AI_TOOL_CATEGORIES[cat_name]
                for tool_name, tool_data in category_data["tools"].items():
                    # Simple search in tool name, description, and features
                    searchable_text = f"{tool_name} {tool_data['description']} {' '.join(tool_data['features'])}".lower()
                    if query.lower() in searchable_text:
                        results.append({
                            "name": tool_name,
                            "category": cat_name,
                            "category_icon": category_data["icon"],
                            **tool_data
                        })
        
        return results
    
    def generate_tool_comparison(self, tools: List[str], aspect: str, model: str = "Claude 3.5 Sonnet") -> str:
        """Generate detailed comparison between AI tools"""
        
        tool_details = []
        for tool_name in tools:
            for category in AI_TOOL_CATEGORIES.values():
                if tool_name in category["tools"]:
                    tool_details.append({
                        "name": tool_name,
                        **category["tools"][tool_name]
                    })
        
        if not tool_details:
            return "No tools found for comparison."
        
        prompt = f"""
        Create a detailed comparison of these AI tools focusing on {aspect}:
        
        Tools to compare:
        {json.dumps(tool_details, indent=2)}
        
        Please provide:
        1. Overview comparison table
        2. Detailed analysis of each tool's strengths/weaknesses for {aspect}
        3. Use case recommendations
        4. Pricing comparison
        5. Who should choose which tool and why
        
        Make it comprehensive yet easy to understand.
        """
        
        return self.ai_provider.generate_content(prompt, model, max_tokens=3000, temperature=0.3)
    
    def generate_tool_tutorial(self, tool_name: str, use_case: str, audience: str, model: str = "Claude 3.5 Sonnet") -> str:
        """Generate step-by-step tutorial for using an AI tool"""
        
        # Find tool details
        tool_data = None
        for category in AI_TOOL_CATEGORIES.values():
            if tool_name in category["tools"]:
                tool_data = category["tools"][tool_name]
                break
        
        if not tool_data:
            return f"Tool '{tool_name}' not found in database."
        
        prompt = f"""
        Create a comprehensive step-by-step tutorial for using {tool_name} for {use_case}.
        
        Tool Information:
        {json.dumps(tool_data, indent=2)}
        
        Target Audience: {audience}
        Specific Use Case: {use_case}
        
        Please include:
        1. Getting started (account setup, pricing considerations)
        2. Step-by-step walkthrough with screenshots descriptions
        3. Pro tips and best practices
        4. Common mistakes to avoid
        5. Advanced features for power users
        6. Alternative tools to consider
        7. Cost-benefit analysis
        
        Make it actionable and beginner-friendly while being comprehensive.
        """
        
        return self.ai_provider.generate_content(prompt, model, max_tokens=3500, temperature=0.3)
    
    def generate_daily_ai_news(self, model: str = "GPT-4") -> str:
        """Generate daily AI tool news and updates"""
        
        prompt = f"""
        Create a daily AI tools update covering:
        
        1. **New AI Tool Releases** (if any major ones this week)
        2. **Feature Updates** from major tools like ChatGPT, Claude, Canva, etc.
        3. **Trending AI Tools** gaining popularity
        4. **Tips of the Day** - practical AI tool usage tips
        5. **Community Spotlight** - interesting AI tool use cases
        
        Current date context: {datetime.now().strftime('%B %d, %Y')}
        
        Format as an engaging newsletter-style update that would work well for social media.
        Include practical tips that people can try today.
        
        Note: If you don't have access to real-time data, create educational content about AI tool categories and general best practices.
        """
        
        return self.ai_provider.generate_content(prompt, model, max_tokens=2000, temperature=0.7)

# Enhanced Content Generation Pipeline
class ContentAutomationPipeline:
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider
        self.content_calendar = []
        self.tool_discovery = AIToolDiscovery(ai_provider)
        
    def generate_multi_platform_content(self, segment: str, audience: str, topic: str = "", 
                                       num_days: int = 7, model: str = "GPT-3.5 Turbo") -> Dict:
        """Generate content for all platforms using selected segment and audience"""
        
        if segment == "Finance Education":
            return self._generate_finance_content(audience, topic, num_days, model)
        elif segment == "Motivational & Inspiration":
            return self._generate_motivational_content(audience, topic, num_days, model)
        elif segment == "AI Tool Discovery":
            return self._generate_ai_tool_content(audience, topic, num_days, model)
        else:
            return self._generate_ai_content(audience, topic, num_days, model)
    
    def _generate_ai_tool_content(self, audience: str, topic: str, num_days: int, model: str) -> Dict:
        """Generate AI tool discovery content"""
        
        audience_info = CONTENT_SEGMENTS["AI Tool Discovery"]["audiences"][audience]
        
        base_prompt = f"""
        Create a {num_days}-day AI TOOL DISCOVERY content strategy for '{audience}'.
        
        AUDIENCE PROFILE:
        - Description: {audience_info['description']}
        - Focus Areas: {', '.join(audience_info['focus_areas'])}
        - Content Approach: {audience_info['risk_level']}
        {f"- Specific Focus: {topic}" if topic else ""}
        
        CONTENT GUIDELINES:
        - Focus on practical, actionable AI tool knowledge
        - Include tool comparisons, tutorials, and new discoveries
        - Provide real-world use cases and ROI considerations
        - Include both free and paid tool options
        - Mention specific tools like ChatGPT, Claude, Canva, Notion AI, etc.
        - Include step-by-step guides and pro tips
        - Address common concerns about AI tool adoption
        
        For each day, generate:
        1. YouTube video idea (tool tutorial, comparison, or discovery)
        2. 3 TikTok concepts (quick tips, tool demos, before/after)
        3. 3 Instagram posts (tool highlights, comparison graphics, tips)
        4. 2 Facebook posts (detailed guides, community discussions)
        5. 5 Twitter threads (tool tips, discoveries, quick tutorials)
        
        Format as JSON with practical, actionable content.
        """
        
        try:
            response_text = self.ai_provider.generate_content(
                base_prompt, model, max_tokens=4000, temperature=0.7
            )
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                st.warning("⚠️ Received text format instead of JSON. Content generated successfully.")
                return {"day_1": {"content": response_text}}
                
        except Exception as e:
            st.error(f"Content generation failed: {e}")
            return {}
    
    def _generate_motivational_content(self, audience: str, topic: str, num_days: int, model: str) -> Dict:
        """Generate motivational content with wisdom from various sources"""
        
        audience_info = CONTENT_SEGMENTS["Motivational & Inspiration"]["audiences"][audience]
        
        base_prompt = f"""
        Create a {num_days}-day INSPIRATIONAL and MOTIVATIONAL content strategy for '{audience}'.
        
        AUDIENCE PROFILE:
        - Description: {audience_info['description']}
        - Focus Areas: {', '.join(audience_info['focus_areas'])}
        - Content Approach: {audience_info['risk_level']}
        {f"- Specific Theme: {topic}" if topic else ""}
        
        CONTENT GUIDELINES:
        - Include diverse sources of wisdom (philosophical, spiritual, literary, historical)
        - May include respectful references to Quran, Nahjul-Balagha, Bible, Buddhist teachings, etc.
        - Always cite sources respectfully and note that interpretations may vary
        - Focus on universal human values: compassion, perseverance, wisdom, justice, gratitude
        - Avoid toxic positivity - acknowledge real struggles while offering hope
        - Include disclaimer: "Inspirational content only. For personal struggles, consider professional support."
        - Respect diverse beliefs and backgrounds
        - Promote positive mental health and well-being
        
        SOURCES TO DRAW FROM (respectfully and with citations):
        - Quran and Islamic wisdom
        - Nahjul-Balagha (sayings of Ali ibn Abi Talib)
        - Biblical wisdom and proverbs
        - Philosophical teachings (Stoicism, etc.)
        - Historical figures and their wisdom
        - Literature and poetry
        - Modern psychology and well-being research
        
        For each day, generate:
        1. YouTube video idea (inspirational title, description, key wisdom points)
        2. 3 TikTok concepts (motivational hooks, key messages, uplifting content)
        3. 3 Instagram posts (quote graphics, reflection prompts, wisdom shares)
        4. 2 Facebook posts (community inspiration, discussion starters)
        5. 5 Twitter threads (daily wisdom, motivation chains, reflective thoughts)
        
        Format as JSON with appropriate sourcing and disclaimers.
        """
        
        try:
            response_text = self.ai_provider.generate_content(
                base_prompt, model, max_tokens=4000, temperature=0.7
            )
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                st.warning("⚠️ Received text format instead of JSON. Content generated successfully.")
                return {"day_1": {"content": response_text}}
                
        except Exception as e:
            st.error(f"Content generation failed: {e}")
            return {}
    
    def _generate_finance_content(self, audience: str, topic: str, num_days: int, model: str) -> Dict:
        """Generate finance-specific content with appropriate disclaimers"""
        
        audience_info = CONTENT_SEGMENTS["Finance Education"]["audiences"][audience]
        
        base_prompt = f"""
        Create a {num_days}-day EDUCATIONAL finance content strategy for '{audience}'.
        
        AUDIENCE PROFILE:
        - Description: {audience_info['description']}
        - Focus Areas: {', '.join(audience_info['focus_areas'])}
        - Risk Level: {audience_info['risk_level']}
        {f"- Specific Topic: {topic}" if topic else ""}
        
        IMPORTANT GUIDELINES:
        - This is EDUCATIONAL content only, not personalized financial advice
        - Emphasize {audience_info['risk_level']}
        - Include disclaimer: "Educational content only. Consult professionals for personalized advice."
        - Promote financial literacy and responsible investing
        - Warn against get-rich-quick schemes and excessive risk-taking
        - Emphasize long-term thinking and diversification
        
        Format as JSON with clear disclaimers throughout.
        """
        
        try:
            response_text = self.ai_provider.generate_content(
                base_prompt, model, max_tokens=4000, temperature=0.7
            )
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                st.warning("⚠️ Received text format instead of JSON. Content generated successfully.")
                return {"day_1": {"content": response_text}}
                
        except Exception as e:
            st.error(f"Content generation failed: {e}")
            return {}
    
    def _generate_ai_content(self, audience: str, topic: str, num_days: int, model: str) -> Dict:
        """Generate AI education content"""
        
        audience_info = CONTENT_SEGMENTS["AI Education"]["audiences"][audience]
        
        base_prompt = f"""
        Create a {num_days}-day AI education content strategy for '{audience}'.
        
        AUDIENCE PROFILE:
        - Description: {audience_info['description']}
        - Focus Areas: {', '.join(audience_info['focus_areas'])}
        - Approach: {audience_info['risk_level']}
        {f"- Specific Topic: {topic}" if topic else ""}
        
        Format as JSON.
        """
        
        try:
            response_text = self.ai_provider.generate_content(
                base_prompt, model, max_tokens=4000, temperature=0.7
            )
            
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                st.warning("⚠️ Received text format instead of JSON. Content generated successfully.")
                return {"day_1": {"content": response_text}}
                
        except Exception as e:
            st.error(f"Content generation failed: {e}")
            return {}

    def create_video_scripts(self, segment: str, audience: str, video_ideas: List[str], 
                           model: str = "Claude 3.5 Sonnet") -> List[Dict]:
        """Generate detailed video scripts"""
        scripts = []
        
        for idea in video_ideas:
            if segment == "Finance Education":
                script_prompt = f"""
                Create a detailed 10-15 minute EDUCATIONAL YouTube script for '{audience}' about: {idea}
                
                Include clear disclaimers about educational purposes only and responsible investing.
                """
            elif segment == "Motivational & Inspiration":
                script_prompt = f"""
                Create a detailed 10-15 minute INSPIRATIONAL YouTube script for '{audience}' about: {idea}
                
                IMPORTANT: This is motivational content with these requirements:
                - Include diverse sources of wisdom respectfully
                - May reference Quran, Nahjul-Balagha, and other spiritual texts with proper attribution
                - Focus on universal human values and positive mental health
                - Include disclaimer: "Inspirational content only. Interpretations may vary. For personal struggles, seek professional support."
                - Avoid toxic positivity - acknowledge real challenges while offering hope
                - Respect diverse beliefs and backgrounds
                
                Include sections with timestamps and inspirational focus.
                """
            elif segment == "AI Tool Discovery":
                script_prompt = f"""
                Create a detailed 10-15 minute AI TOOL tutorial/review script for '{audience}' about: {idea}
                
                Include:
                - Tool overview and key features
                - Step-by-step tutorial
                - Pros and cons
                - Pricing and alternatives
                - Real-world use cases
                - Who should use this tool
                
                Focus on practical, actionable guidance.
                """
            else:
                script_prompt = f"""
                Create a detailed 10-15 minute YouTube script for '{audience}' about: {idea}
                
                Focus on practical AI education with step-by-step guidance.
                """
            
            try:
                script_content = self.ai_provider.generate_content(
                    script_prompt, model, max_tokens=2500, temperature=0.7
                )
                
                if script_content:
                    scripts.append({
                        "idea": idea,
                        "script": script_content,
                        "segment": segment,
                        "audience": audience,
                        "model_used": model
                    })
            except Exception as e:
                st.error(f"Script generation failed for {idea}: {e}")
                
        return scripts

# Streamlit App
def main():
    st.set_page_config(
        page_title="Simply AI - Enhanced Content Pipeline with Tool Discovery", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize AI provider
    if 'ai_provider' not in st.session_state:
        st.session_state.ai_provider = AIProvider()
    
    # Initialize pipeline
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = ContentAutomationPipeline(st.session_state.ai_provider)
    
    # Get available models
    available_models = st.session_state.ai_provider.get_available_models()
    
    # Sidebar
    with st.sidebar:
        st.title("🚀 Content Automation")
        
        # Debug Info
        st.markdown("### 🔍 Debug Info")
        st.write(f"OpenAI Key: {'✅ Found' if st.session_state.ai_provider.openai_key else '❌ Missing'}")
        st.write(f"Claude Key: {'✅ Found' if st.session_state.ai_provider.claude_key else '❌ Missing'}")
        st.write(f"Claude Available: {'✅ Yes' if CLAUDE_AVAILABLE else '❌ No'}")
        st.write(f"Available Models: {available_models}")
        
        # AI Model Selection
        st.markdown("### 🧠 AI Model Selection")
        
        if not available_models:
            st.error("❌ No AI models available!")
            if not CLAUDE_AVAILABLE:
                st.warning("💡 Install Claude: `pip install anthropic`")
            st.stop()
        
        selected_model = st.selectbox("Choose AI Model", available_models)
        
        # Model info
        cost = st.session_state.ai_provider.get_model_cost(selected_model)
        st.info(f"💰 Cost: ${cost}/1K tokens")
        
        # Model recommendations
        if "Claude" in selected_model:
            if "Haiku" in selected_model:
                st.success("⚡ Fastest and cheapest!")
            else:
                st.success("🎨 Great for creative content!")
        elif "GPT-4" in selected_model:
            st.success("🧠 Best for complex tasks!")
        elif "GPT-3.5" in selected_model:
            st.success("⚡ Fast and economical!")
        
        # Navigation
        st.markdown("### 🔥 Features")
        page = st.selectbox("Choose Feature", [
            "📝 Generate Content Calendar",
            "🎬 Create Video Scripts", 
            "🔍 AI Tool Discovery",
            "📊 Tool Comparison",
            "📱 Platform Optimizer",
            "📅 Schedule Manager",
            "📊 Analytics Dashboard"
        ])
        
        # API Status
        st.markdown("### 🔐 API Status")
        if st.session_state.ai_provider.openai_client:
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ OpenAI Disconnected")
            
        if st.session_state.ai_provider.claude_client:
            st.success("✅ Claude Connected")
        else:
            st.error("❌ Claude Disconnected")
    
    # Main header
    st.title(f"🚀 Simply AI - Enhanced with Tool Discovery")
    st.markdown("Generate content about AI tools, finance education, and motivation across all platforms!")
    
    # Debug: Show available segments
    if st.checkbox("🔧 Debug Mode"):
        st.info(f"Available segments: {list(CONTENT_SEGMENTS.keys())}")
        st.json({name: data["description"] for name, data in CONTENT_SEGMENTS.items()})
    
    # Page: Generate Content Calendar
    if page == "📝 Generate Content Calendar":
        st.header("Multi-Platform Content Calendar Generator")
        
        # Segment Selection
        col1, col2 = st.columns(2)
        
        with col1:
            segment = st.selectbox(
                "📚 Content Segment",
                list(CONTENT_SEGMENTS.keys()),
                format_func=lambda x: f"{CONTENT_SEGMENTS[x]['icon']} {x}"
            )
        
        with col2:
            # Dynamic audience selection based on segment
            audiences = list(CONTENT_SEGMENTS[segment]["audiences"].keys())
            audience = st.selectbox(
                "👥 Target Audience",
                audiences
            )
        
        # Show audience description
        audience_info = CONTENT_SEGMENTS[segment]["audiences"][audience]
        st.info(f"🎯 **{audience}**: {audience_info['description']}")
        
        # Show suggested focus areas
        with st.expander("💡 Suggested Focus Areas"):
            for area in audience_info['focus_areas']:
                st.write(f"• {area}")
        
        # Topic and settings
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Dynamic placeholder based on segment
            example_topics = ", ".join(audience_info['focus_areas'][:2])
            topic = st.text_input(
                "Focus Topic (Optional)", 
                placeholder=f"e.g., {example_topics}"
            )
        
        with col2:
            num_days = st.number_input("Days of Content", min_value=1, max_value=30, value=7)
        
        with col3:
            # Show content approach
            st.caption(f"📋 Approach: {audience_info['risk_level']}")
        
        # Show content type warning for special segments
        if segment == "Finance Education":
            st.warning("📚 Financial Education Content: All content will be educational only with appropriate disclaimers.")
        elif segment == "Motivational & Inspiration":
            st.info("🌟 Inspirational Content: Includes diverse wisdom sources with respectful attribution and mental health awareness.")
        elif segment == "AI Tool Discovery":
            st.info("🔍 AI Tool Content: Focuses on practical tool knowledge, comparisons, and tutorials.")
        
        # Cost estimation
        estimated_tokens = 500 * num_days
        estimated_cost = (estimated_tokens / 1000) * st.session_state.ai_provider.get_model_cost(selected_model)
        st.info(f"🧮 Estimated cost: ${estimated_cost:.4f} using {selected_model}")
        
        if st.button("🎯 Generate Content Calendar", type="primary"):
            with st.spinner(f"Creating {segment} content with {selected_model}..."):
                content_calendar = st.session_state.pipeline.generate_multi_platform_content(
                    segment, audience, topic, num_days, selected_model
                )
                
                if content_calendar:
                    st.success(f"✅ Generated {num_days} days of {segment} content for {audience}!")
                    
                    # Display calendar with segment context
                    for day, content in content_calendar.items():
                        with st.expander(f"📅 {day.replace('_', ' ').title()} - {segment}"):
                            
                            # Display content for each platform
                            for platform in ['youtube', 'tiktok', 'instagram', 'facebook', 'twitter']:
                                if platform in content:
                                    platform_icons = {
                                        'youtube': '🎥',
                                        'tiktok': '📱',
                                        'instagram': '📸',
                                        'facebook': '📘',
                                        'twitter': '🐦'
                                    }
                                    
                                    st.subheader(f"{platform_icons[platform]} {platform.title()}")
                                    platform_content = content[platform]
                                    
                                    if isinstance(platform_content, list):
                                        for i, item in enumerate(platform_content):
                                            if isinstance(item, dict):
                                                for key, value in item.items():
                                                    if key not in ['disclaimer', 'source_attribution']:
                                                        st.write(f"**{key.title()}:** {value}")
                                                
                                                # Show disclaimers and attributions
                                                if 'disclaimer' in item and item['disclaimer']:
                                                    st.caption(f"⚠️ {item['disclaimer']}")
                                                if 'source_attribution' in item and item['source_attribution']:
                                                    st.caption(f"📖 Source: {item['source_attribution']}")
                                            else:
                                                st.write(f"**Item {i+1}:** {item}")
                                    elif isinstance(platform_content, dict):
                                        for key, value in platform_content.items():
                                            if key not in ['disclaimer', 'source_attribution']:
                                                st.write(f"**{key.title()}:** {value}")
                                        
                                        # Show disclaimers and attributions
                                        if 'disclaimer' in platform_content:
                                            st.caption(f"⚠️ {platform_content['disclaimer']}")
                                        if 'source_attribution' in platform_content:
                                            st.caption(f"📖 Source: {platform_content['source_attribution']}")
                                    else:
                                        st.write(platform_content)
                            
                            if 'content' in content:
                                st.markdown(content['content'])
                    
                    # Save to session state
                    st.session_state.content_calendar = content_calendar
                    st.session_state.current_segment = segment
                    st.session_state.current_audience = audience
                    
                    # Download option
                    filename = f"content_calendar_{segment.replace(' ', '_')}_{audience.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                    st.download_button(
                        label="📥 Download Content Calendar (JSON)",
                        data=json.dumps(content_calendar, indent=2),
                        file_name=filename,
                        mime="application/json"
                    )
    
    # AI Tool Discovery Page
    elif page == "🔍 AI Tool Discovery":
        st.header("AI Tool Discovery & Tutorial Generator")
        
        # Tool Database Explorer
        st.subheader("🗃️ AI Tool Database")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Category filter
            category_filter = st.selectbox(
                "Filter by Category",
                ["All Categories"] + list(AI_TOOL_CATEGORIES.keys()),
                format_func=lambda x: f"{AI_TOOL_CATEGORIES[x]['icon']} {x}" if x != "All Categories" else x
            )
        
        with col2:
            # Search tools
            search_query = st.text_input("🔍 Search Tools", placeholder="e.g., writing, video, automation")
        
        # Display tools
        if search_query:
            search_category = None if category_filter == "All Categories" else category_filter
            results = st.session_state.pipeline.tool_discovery.search_tools(search_query, search_category)
            
            if results:
                st.write(f"Found {len(results)} tools matching '{search_query}':")
                
                for i, tool in enumerate(results):
                    with st.expander(f"{tool['category_icon']} {tool['name']} - {tool['category']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Description:** {tool['description']}")
                            st.write(f"**Best for:** {tool['best_for']}")
                            st.write(f"**Pricing:** {tool['pricing']}")
                            if tool['website']:
                                st.markdown(f"**Website:** [Visit {tool['name']}]({tool['website']})")
                        
                        with col2:
                            st.write("**Features:**")
                            for feature in tool['features']:
                                st.write(f"• {feature}")
            else:
                st.warning(f"No tools found matching '{search_query}'")
        else:
            # Show all categories and tools
            for cat_name, cat_data in AI_TOOL_CATEGORIES.items():
                if category_filter == "All Categories" or category_filter == cat_name:
                    with st.expander(f"{cat_data['icon']} {cat_name} ({len(cat_data['tools'])} tools)"):
                        st.write(f"*{cat_data['description']}*")
                        
                        for tool_name, tool_data in cat_data['tools'].items():
                            st.markdown(f"**{tool_name}** - {tool_data['description']}")
                            st.write(f"💰 {tool_data['pricing']} | 🎯 {tool_data['best_for']}")
                            if tool_data['website']:
                                st.markdown(f"[Visit {tool_name}]({tool_data['website']})")
                            st.write("---")
        
        # Tutorial Generator
        st.subheader("📖 Generate Tool Tutorial")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get all tool names
            all_tools = []
            for category in AI_TOOL_CATEGORIES.values():
                all_tools.extend(category['tools'].keys())
            
            selected_tool = st.selectbox("Select Tool", sorted(all_tools))
        
        with col2:
            use_case = st.text_input("Use Case", placeholder="e.g., creating social media graphics")
        
        with col3:
            tutorial_audience = st.selectbox("Target Audience", [
                "Beginners", "Content Creators", "Business Professionals", 
                "Students & Educators", "Tech Enthusiasts"
            ])
        
        if st.button("📚 Generate Tutorial") and selected_tool and use_case:
            with st.spinner(f"Creating tutorial for {selected_tool}..."):
                tutorial = st.session_state.pipeline.tool_discovery.generate_tool_tutorial(
                    selected_tool, use_case, tutorial_audience, selected_model
                )
                
                if tutorial:
                    st.success(f"✅ Tutorial generated for {selected_tool}!")
                    
                    with st.expander(f"📖 {selected_tool} Tutorial: {use_case}", expanded=True):
                        st.markdown(tutorial)
                        
                        st.download_button(
                            label="📥 Download Tutorial",
                            data=tutorial,
                            file_name=f"tutorial_{selected_tool}_{use_case.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
        
        # Daily AI News Generator
        st.subheader("📰 Daily AI Tool Updates")
        
        if st.button("🔄 Generate Daily AI News"):
            with st.spinner("Creating daily AI updates..."):
                news = st.session_state.pipeline.tool_discovery.generate_daily_ai_news(selected_model)
                
                if news:
                    st.success("✅ Daily AI updates generated!")
                    
                    with st.expander("📰 Today's AI Tool Updates", expanded=True):
                        st.markdown(news)
                        
                        st.download_button(
                            label="📥 Download News Update",
                            data=news,
                            file_name=f"ai_news_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown"
                        )
    
    # Test First Post Page  
    elif page == "🚀 Test First Post":
        st.header("🚀 Test Your First AI Tool Post")
        
        st.info("This page helps you quickly test all features by creating your first AI tool discovery post!")
        
        # Quick post generator
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📱 Quick Post Generator")
            
            post_type = st.selectbox("Post Type", [
                "Tool Comparison (ChatGPT vs Claude)",
                "New Tool Alert",
                "Daily AI News",
                "Tool Tutorial Snippet",
                "5 Best AI Tools for Beginners"
            ])
            
            target_platform = st.selectbox("Target Platform", [
                "Twitter Thread",
                "Instagram Caption",
                "LinkedIn Post",
                "Facebook Post",
                "YouTube Description"
            ])
            
            if st.button("🎯 Generate Test Post"):
                with st.spinner("Creating your test post..."):
                    
                    if post_type == "Tool Comparison (ChatGPT vs Claude)":
                        prompt = f"""
                        Create a {target_platform.lower()} comparing ChatGPT vs Claude AI assistants.
                        
                        Include:
                        - Key differences in capabilities
                        - Pricing comparison
                        - Best use cases for each
                        - Personal recommendation
                        - Engaging hook and call-to-action
                        
                        Make it informative yet engaging for social media.
                        """
                    
                    elif post_type == "5 Best AI Tools for Beginners":
                        prompt = f"""
                        Create a {target_platform.lower()} about the 5 best AI tools for beginners.
                        
                        Include tools like:
                        - ChatGPT (conversation)
                        - Canva AI (design)
                        - Grammarly (writing)
                        - Otter.ai (transcription)
                        - Notion AI (productivity)
                        
                        For each tool mention: what it does, why it's beginner-friendly, pricing.
                        Add engaging hook and clear value proposition.
                        """
                    
                    else:
                        prompt = f"""
                        Create a {target_platform.lower()} about {post_type.lower()}.
                        
                        Make it:
                        - Informative and valuable
                        - Engaging for social media
                        - Include practical tips
                        - Add relevant hashtags
                        - Include call-to-action
                        """
                    
                    # Generate content
                    test_content = st.session_state.ai_provider.generate_content(
                        prompt, selected_model, max_tokens=800, temperature=0.7
                    )
                    
                    if test_content:
                        st.success("✅ Test post generated!")
                        st.text_area("Generated Content", test_content, height=300)
                        
                        # Download option
                        st.download_button(
                            label="📥 Download Post",
                            data=test_content,
                            file_name=f"test_post_{post_type.replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
        
        with col2:
            st.subheader("🔧 Feature Testing Checklist")
            
            st.markdown("""
            Test each feature by checking them off:
            
            **Basic Features:**
            - [ ] Content calendar generation works
            - [ ] Different segments appear (AI Education, Finance, etc.)
            - [ ] Multiple audiences available
            - [ ] AI models respond correctly
            
            **AI Tool Discovery:**
            - [ ] Tool database loads
            - [ ] Tool search functions
            - [ ] Comparison generator works
            - [ ] Tutorial creation functions
            
            **Content Generation:**
            - [ ] Multi-platform content creates
            - [ ] Video scripts generate
            - [ ] Different content types work
            - [ ] Download functions work
            
            **Advanced Features:**
            - [ ] Image generation (if enabled)
            - [ ] Social media posting (if APIs connected)
            - [ ] Scheduling works
            - [ ] Analytics display
            """)
            
            st.subheader("📊 Quick Stats")
            
            # Show some quick stats
            total_tools = len([tool for category in AI_TOOL_CATEGORIES.values() 
                             for tool in category['tools']])
            st.metric("AI Tools in Database", total_tools)
            st.metric("Content Segments", len(CONTENT_SEGMENTS))
            st.metric("Available Models", len(available_models))
            
            if st.button("🔄 Test Tool Comparison"):
                st.info("Redirecting to Tool Comparison page...")
                # This would ideally change the page selection
                st.markdown("**Manual Step:** Select '📊 Tool Comparison' from the sidebar to test comparisons!")
            
            if st.button("🛠️ Test Tool Discovery"):
                st.info("Redirecting to AI Tool Discovery page...")
                st.markdown("**Manual Step:** Select '🔍 AI Tool Discovery' from the sidebar to browse tools!")
        
        # Quick tips
        with st.expander("💡 Quick Testing Tips"):
            st.markdown("""
            **For fastest testing:**
            
            1. **Start with Content Calendar**: Select AI Tool Discovery → Tech Enthusiasts → Generate
            2. **Test Tool Comparison**: Go to Tool Comparison → Select ChatGPT vs Claude → Generate
            3. **Browse Tool Database**: Visit AI Tool Discovery page → Browse categories
            4. **Create a Script**: Go to Video Scripts → Enter an AI tool idea → Generate
            
            **If something doesn't work:**
            - Check API keys in .env file
            - Verify internet connection
            - Try refreshing the page (Ctrl+F5)
            - Check debug info in sidebar
            
            **Success indicators:**
            - Content generates without errors
            - Downloads work properly
            - Different models produce different styles
            - Tool database shows 25+ tools
            """)

    # Tool Comparison Page
    elif page == "📊 Tool Comparison":
        st.header("AI Tool Comparison Generator")
        
        # Get all tools for comparison
        all_tools = []
        for category in AI_TOOL_CATEGORIES.values():
            all_tools.extend(category['tools'].keys())
        
        col1, col2 = st.columns(2)
        
        with col1:
            tools_to_compare = st.multiselect(
                "Select Tools to Compare (2-5 tools)",
                sorted(all_tools),
                default=["ChatGPT", "Claude"],  # Set default selection
                max_selections=5
            )
        
        with col2:
            comparison_aspect = st.selectbox(
                "Comparison Focus",
                [
                    "Overall Features",
                    "Pricing & Value",
                    "Ease of Use",
                    "Business Use Cases",
                    "Creative Capabilities",
                    "Integration Options",
                    "Learning Curve"
                ]
            )
        
        # Show tool details for selected tools
        if tools_to_compare:
            st.subheader("📋 Selected Tools Overview")
            cols = st.columns(len(tools_to_compare))
            
            for i, tool_name in enumerate(tools_to_compare):
                with cols[i]:
                    # Find tool details
                    for category in AI_TOOL_CATEGORIES.values():
                        if tool_name in category['tools']:
                            tool_data = category['tools'][tool_name]
                            st.markdown(f"**{tool_name}**")
                            st.write(f"💰 {tool_data['pricing']}")
                            st.write(f"🎯 {tool_data['best_for']}")
                            break
        
        if st.button("⚖️ Generate Comparison") and len(tools_to_compare) >= 2:
            with st.spinner(f"Comparing {', '.join(tools_to_compare)}..."):
                comparison = st.session_state.pipeline.tool_discovery.generate_tool_comparison(
                    tools_to_compare, comparison_aspect, selected_model
                )
                
                if comparison:
                    st.success(f"✅ Comparison generated for {len(tools_to_compare)} tools!")
                    
                    with st.expander(f"⚖️ {comparison_aspect} Comparison", expanded=True):
                        st.markdown(comparison)
                        
                        st.download_button(
                            label="📥 Download Comparison",
                            data=comparison,
                            file_name=f"comparison_{'_'.join(tools_to_compare)}_{comparison_aspect.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
        elif len(tools_to_compare) < 2:
            st.info("Please select at least 2 tools to compare.")
        
        # Quick comparison buttons
        st.subheader("🚀 Quick Comparisons")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("ChatGPT vs Claude"):
                st.session_state.quick_comparison = ["ChatGPT", "Claude"]
        
        with col2:
            if st.button("Canva vs Adobe Firefly"):
                st.session_state.quick_comparison = ["Canva AI", "Adobe Firefly"]
        
        with col3:
            if st.button("Midjourney vs DALL-E"):
                st.session_state.quick_comparison = ["Midjourney", "DALL-E 3"]
    
    # Video Scripts Page
    elif page == "🎬 Create Video Scripts":
        st.header("YouTube Video Script Generator")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            segment = st.selectbox(
                "📚 Content Segment",
                list(CONTENT_SEGMENTS.keys()),
                format_func=lambda x: f"{CONTENT_SEGMENTS[x]['icon']} {x}"
            )
        
        with col2:
            audiences = list(CONTENT_SEGMENTS[segment]["audiences"].keys())
            audience = st.selectbox("👥 Target Audience", audiences)
        
        with col3:
            script_model = st.selectbox("AI Model for Scripts", available_models, 
                                       index=next((i for i, model in enumerate(available_models) 
                                                 if "Claude" in model), 0))
        
        # Show content guidelines
        if segment == "Motivational & Inspiration":
            st.info("🌟 Motivational content will include diverse wisdom sources with respectful attribution and mental health awareness.")
        elif segment == "AI Tool Discovery":
            st.info("🔍 AI Tool content will focus on practical tutorials, comparisons, and tool discovery.")
        
        video_ideas = st.text_area(
            "Video Ideas (one per line)",
            placeholder="Enter your video ideas here...",
            height=150
        ).split('\n')
        
        video_ideas = [idea.strip() for idea in video_ideas if idea.strip()]
        
        if st.button("🎬 Generate Scripts") and video_ideas:
            with st.spinner(f"Writing {segment} scripts with {script_model}..."):
                scripts = st.session_state.pipeline.create_video_scripts(
                    segment, audience, video_ideas, script_model
                )
                
                for script_data in scripts:
                    with st.expander(f"📝 {script_data['segment']} Script: {script_data['idea']}"):
                        st.markdown(f"*Audience: {script_data['audience']} | Model: {script_data['model_used']}*")
                        
                        if script_data['segment'] == "Finance Education":
                            st.info("📚 Financial Education Content - Includes appropriate disclaimers")
                        elif script_data['segment'] == "Motivational & Inspiration":
                            st.info("🌟 Inspirational Content - Includes diverse wisdom sources and mental health awareness")
                        elif script_data['segment'] == "AI Tool Discovery":
                            st.info("🔍 AI Tool Content - Includes practical tutorials and tool guidance")
                        
                        st.markdown(script_data['script'])
                        
                        st.download_button(
                            label=f"📥 Download Script",
                            data=script_data['script'],
                            file_name=f"script_{script_data['segment'][:10]}_{script_data['idea'][:30].replace(' ', '_')}.txt",
                            mime="text/plain",
                            key=f"download_{script_data['idea'][:10]}"
                        )
    
    # Analytics Dashboard
    elif page == "📊 Analytics Dashboard":
        st.header("Performance Analytics")
        
        # Sample metrics with all segments
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Views", "245K", "22%")
        with col2:
            st.metric("Engagement Rate", "11.5%", "4.2%")
        with col3:
            st.metric("New Subscribers", "4,180", "35%")
        with col4:
            st.metric("Tool Tutorials Created", "47", "18%")
        
        # Segment performance
        st.markdown("### 📊 Content Performance by Segment")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🤖 AI Education", "35%", "3%")
        with col2:
            st.metric("💰 Finance Education", "25%", "8%")
        with col3:
            st.metric("🌟 Motivational", "20%", "15%")
        with col4:
            st.metric("🔍 Tool Discovery", "20%", "45%")
        
        # Tool popularity chart
        st.markdown("### 🔥 Most Popular AI Tools Covered")
        tool_data = {
            "Tool": ["ChatGPT", "Claude", "Canva", "Midjourney", "Notion AI", "Grammarly"],
            "Video Views": [45000, 38000, 52000, 41000, 28000, 31000],
            "Engagement": [12.5, 11.8, 15.2, 13.1, 9.8, 10.4]
        }
        
        df = pd.DataFrame(tool_data)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()