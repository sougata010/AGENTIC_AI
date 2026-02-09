# Agent modules - lazy loaded to avoid import blocking

def get_agents():
    """Lazy load agents to avoid startup blocking"""
    from .base import BaseAgent
    from .image_gen import ImageGenAgent
    from .presentation_gen import PresentationGenAgent
    from .quiz_gen import QuizGenAgent
    from .roadmap_gen import RoadmapGenAgent
    from .video_gen import VideoGenAgent
    from .email_gen import EmailGenAgent
    from .security_recon import SecurityReconAgent
    from .nacle import NacleAgent
    from .nexus import NexusAgent
    from .quanta import QuantaAgent
    from .scholar import ScholarAgent
    from .student_gen import StudentGenAgent
    from .career_gen import ResumeAgent, DebateAgent
    from .travel_gen import TravelAgent
    
    return {
        'image_gen': ImageGenAgent,
        'presentation_gen': PresentationGenAgent,
        'quiz_gen': QuizGenAgent,
        'roadmap_gen': RoadmapGenAgent,
        'video_gen': VideoGenAgent,
        'email_gen': EmailGenAgent,
        'security_recon': SecurityReconAgent,
        'nacle': NacleAgent,
        'nexus': NexusAgent,
        'quanta': QuantaAgent,
        'scholar': ScholarAgent,
        'student_gen': StudentGenAgent,
        'resume_opt': ResumeAgent,
        'debate_coach': DebateAgent,
        'travel_plan': TravelAgent,
    }

# Agent metadata without imports
AGENT_INFO = [
    {'id': 'image_gen', 'name': 'image_gen', 'description': 'Generate Pinterest-optimized images with AI-driven creative strategy', 'icon': '<i class="ph ph-palette"></i>'},
    {'id': 'presentation_gen', 'name': 'presentation_gen', 'description': 'Create professional PowerPoint presentations with AI-generated content', 'icon': '<i class="ph ph-presentation-chart"></i>'},
    {'id': 'quiz_gen', 'name': 'quiz_gen', 'description': 'Generate educational quizzes with multiple choice questions', 'icon': '<i class="ph ph-exam"></i>'},
    {'id': 'roadmap_gen', 'name': 'roadmap_gen', 'description': 'Create structured learning roadmaps with resources and timelines', 'icon': '<i class="ph ph-map-trifold"></i>'},
    {'id': 'video_gen', 'name': 'video_gen', 'description': 'Create video content strategies and scripts for social media', 'icon': '<i class="ph ph-film-strip"></i>'},
    {'id': 'email_gen', 'name': 'email_gen', 'description': 'Generate professional email templates for various contexts', 'icon': '<i class="ph ph-envelope-simple"></i>'},
    {'id': 'security_recon', 'name': 'security_recon', 'description': 'Perform security analysis and reconnaissance for domains', 'icon': '<i class="ph ph-shield-check"></i>'},
    {'id': 'nacle', 'name': 'nacle', 'description': 'Generate knowledge graphs and learning materials with metacognitive analysis', 'icon': '<i class="ph ph-brain"></i>'},
    {'id': 'nexus', 'name': 'nexus', 'description': 'Code review, debugging, and system design analysis', 'icon': '<i class="ph ph-circuitry"></i>'},
    {'id': 'quanta', 'name': 'quanta', 'description': 'Scientific research analysis and quantum computing insights', 'icon': '<i class="ph ph-atom"></i>'},
    {'id': 'scholar', 'name': 'scholar', 'description': 'Academic research assistant for literature reviews and hypothesis generation', 'icon': '<i class="ph ph-graduation-cap"></i>'},
    {'id': 'student_gen', 'name': 'student_gen', 'description': 'Personalized learning paths, quizzes, and code debugging', 'icon': '<i class="ph ph-student"></i>'},
    {'id': 'resume_opt', 'name': 'resume_opt', 'description': 'Optimize resumes for ATS and get rewrite suggestions', 'icon': '<i class="ph ph-file-text"></i>'},
    {'id': 'debate_coach', 'name': 'debate_coach', 'description': 'Practice negotiation and debate with AI feedback', 'icon': '<i class="ph ph-scales"></i>'},
    {'id': 'travel_plan', 'name': 'travel_gen', 'description': 'Generate detailed travel itineraries and packing lists', 'icon': '<i class="ph ph-airplane-tilt"></i>'},
]
