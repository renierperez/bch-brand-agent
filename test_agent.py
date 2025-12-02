import os
import sys
import yaml
# Mock ADK since it's not installed in this environment
class MockLlmAgent:
    def __init__(self, name, instructions, model_name, tools):
        self.name = name
        self.instructions = instructions
        self.model_name = model_name
        self.tools = tools

import sys
sys.modules['adk'] = type('adk', (), {'LlmAgent': MockLlmAgent})

from agent import BrandMonitoringAgent
from tools import search_social_media, search_financial_news

# Set environment variables
# os.environ["SERPAPI_KEY"] = "..." # Key removed for security
os.environ["MODEL_NAME"] = "gemini-2.5-pro"

def test_agent():
    print("Initializing Brand Monitoring Agent...")
    try:
        agent = BrandMonitoringAgent()
        print("Agent initialized successfully.")
        
        # Simulate a run (this depends on how the agent is structured to run)
        # For now, we'll just test the tools directly to verify the key
        from tools import search_social_media, search_financial_news
        from mailer import send_alert_email
        
        print("\nTesting search_social_media...")
        social_results = search_social_media("Banco de Chile", limit=2)
        print(f"Social Results: {social_results}")
        
        print("\nTesting search_financial_news...")
        financial_results = search_financial_news("Banco de Chile", limit=2)
        print(f"Financial Results: {financial_results}")
        
        print("\nTesting Executive Summary Generation (Real)...")
        # Gather data for Gemini
        data_for_gemini = f"Social Results: {social_results}\nFinancial Results: {financial_results}"
        
        try:
            try:
                from vertexai.generative_models import GenerativeModel, Tool
                import vertexai.preview.generative_models as generative_models
                
                model = GenerativeModel("gemini-2.5-pro")
                # Add Grounding with Google Search (Workaround for SDK compatibility)
                try:
                    tools = [Tool.from_dict({'google_search': {}})]
                    print("Grounding with Google Search enabled (via workaround).")
                except Exception as e:
                    print(f"Failed to enable Grounding: {e}")
                    tools = None
                
                # Load instructions for context
                with open('prompts/persona.yaml', 'r') as f:
                    persona = f.read()
                with open('prompts/instructions.yaml', 'r') as f:
                    instructions = f.read()
                
                prompt = f"{persona}\n\n{instructions}\n\nData to analyze:\n{data_for_gemini}"
                # Use tools for grounding
                if tools:
                    response = model.generate_content(prompt, tools=tools)
                    print("Response generated with Grounding.")
                    if hasattr(response, 'candidates') and response.candidates:
                        try:
                            print(f"Grounding Metadata: {response.candidates[0].grounding_metadata}")
                        except:
                            pass
                else:
                    response = model.generate_content(prompt)
                    print("Response generated without Grounding.")
                generated_summary = response.text
                print(f"Generated Summary:\n{generated_summary}")
            except (ImportError, Exception) as e:
                print(f"VertexAI not available or failed, using mock summary. Error: {e}")
                generated_summary = "<p><strong>Resumen de Prueba:</strong> Se detectó actividad normal en redes sociales y noticias financieras. No hay alertas críticas en este momento.</p>"
            
            if os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_PASSWORD"):
                print("\nSending email with summary...")
                from datetime import datetime
                
                # Custom Spanish date formatting
                months_es = {
                    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
                }
                now = datetime.now()
                month_es = months_es[now.month]
                formatted_date = f"[{month_es} {now.day}, {now.year}]"
                
                subject = f"{formatted_date} Banco de Chile: Resumen de Marca e Inteligencia de Mercado - Powered by Gemini"
                alert_result = send_alert_email(subject, generated_summary)
                print(f"Alert Result: {alert_result}")
            else:
                print("\nSkipping email send: GMAIL_USER or GMAIL_PASSWORD not set.")
        except Exception as e:
            print(f"Failed during summary generation or email send: {e}")
            # Fallback to hardcoded for email test if generation fails
            if os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_PASSWORD"):
                send_alert_email("Test Alerta (Fallback)", "<p>Fallback: No se pudo generar el resumen real.</p>")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_agent()
