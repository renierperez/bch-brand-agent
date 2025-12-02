import os
import yaml
from adk import LlmAgent

class BrandMonitoringAgent(LlmAgent):
    def __init__(self):
        # Model configuration
        model_name = os.environ.get("MODEL_NAME", "gemini-2.5-pro")

        # Load prompts
        persona_path = os.path.join(os.path.dirname(__file__), 'prompts', 'persona.yaml')
        rules_path = os.path.join(os.path.dirname(__file__), 'prompts', 'rules.yaml')
        instructions_path = os.path.join(os.path.dirname(__file__), 'prompts', 'instructions.yaml')
        
        with open(persona_path, 'r') as f:
            persona_data = yaml.safe_load(f)
        with open(rules_path, 'r') as f:
            rules_data = yaml.safe_load(f)
        with open(instructions_path, 'r') as f:
            instructions_data = yaml.safe_load(f)
            
        combined_instructions = f"{persona_data['persona']}\n\n{rules_data['rules']}\n\n{instructions_data['instructions']}"
        
        from tools import search_social_media, search_financial_news, vertex_ai_search, store_in_bigquery
        from sentiment import analyze_sentiment
        from mailer import send_alert_email
        from memory import BrandMemory
        
        self.memory = BrandMemory()
        
        super().__init__(
            name="BrandMonitoringAgent",
            instructions=combined_instructions,
            model_name=model_name,
            tools=[search_social_media, search_financial_news, vertex_ai_search, store_in_bigquery, analyze_sentiment, send_alert_email, self.memory.get_recent_context]
        )
