import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, SafetySetting
from tools import search_financial_news, search_social_media
from memory import BrandMemory
from mailer import send_alert_email
from datetime import datetime

# Configuración de Logging
logging.basicConfig(level=logging.INFO)

def main():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = "us-central1" # Gemini 2.5 suele estar primero aquí
    model_name = "gemini-2.5-pro" #
    
    if not project_id:
        logging.error("GOOGLE_CLOUD_PROJECT environment variable not set.")
        return

    vertexai.init(project=project_id, location=location)
    memory = BrandMemory()
    
    print(f"🚀 Iniciando Agente de Vigilancia para Banco de Chile ({model_name})...")

    # 1. Recolección de Información (Búsqueda Amplia)
    raw_news = []
    print("🔎 Buscando en medios financieros y redes sociales...")
    
    # Búsqueda en Medios (DF, Mercurio, etc.)
    financial = search_financial_news("Banco de Chile", limit=10)
    if isinstance(financial, list): raw_news.extend(financial)
    
    # Búsqueda Social (X/Twitter via SerpApi)
    social = search_social_media("Banco de Chile reclamos", limit=10)
    if isinstance(social, list): raw_news.extend(social)

    # 2. Deduplicación (El Filtro de Memoria)
    new_items = []
    for item in raw_news:
        url = item.get('link')
        if url and not memory.is_duplicate(url):
            new_items.append(item)
        else:
            logging.info(f"♻️ Saltando duplicado: {item.get('title')}")

    if not new_items:
        print("✅ No hay noticias nuevas relevantes desde la última ejecución.")
        return

    print(f"⚡ Procesando {len(new_items)} noticias nuevas con Gemini...")

    # 3. Análisis Cognitivo (Gemini 2.5 Pro con Grounding)
    # Definición de la herramienta de búsqueda
    # Usamos el workaround probado si la versión estándar falla, pero intentaremos seguir la guía del usuario.
    # Sin embargo, para asegurar compatibilidad con el entorno actual, usaré el workaround que sé que funciona
    # o la sintaxis robusta.
    # Definición de la herramienta de búsqueda
    # Usamos el workaround probado directamente para evitar errores de compatibilidad API (400)
    print("⚠️ Usando workaround para Grounding Tool (google_search dict)...")
    tools = [Tool.from_dict({'google_search': {}})]

    # Cargar instrucciones detalladas desde el archivo YAML si existe, o usar string robusto
    try:
        with open('prompts/instructions.yaml', 'r') as f:
            import yaml
            loaded_instructions = yaml.safe_load(f).get('instructions', '')
    except Exception:
        # Fallback si falla la lectura del archivo
        loaded_instructions = """
        **Output Format (HTML)**:
        <p><strong>Estado General:</strong> <span style="color: [green/yellow/red];">[Estable/Alerta/Crisis]</span></p>
        <p><strong>Análisis:</strong> [2-3 líneas de análisis experto sobre por qué el estado es ese, mencionando tendencias o noticias clave]</p>
        <p><strong>Recomendación:</strong> [1 línea de recomendación para la alta dirección]</p>
        <hr>
        <h4>Detalle de Menciones</h4>
        <ul>
          <li><strong>Mención:</strong> [Resumen de la mención]. <strong>Sentimiento:</strong> <span style="color: #00C853;">Positivo</span> / <span style="color: #607D8B;">Neutro</span> / <span style="color: #D32F2F;">Negativo</span>. <a href="[URL]" target="_blank">leer más</a></li>
        </ul>
        """

    model = GenerativeModel(
        model_name,
        tools=tools,
        system_instruction=f"""Eres un Analista de Riesgo Reputacional Senior del Banco de Chile. 
        Tu trabajo es analizar las noticias ingresadas y generar un reporte ejecutivo HTML.
        
        Reglas:
        1. Evalúa la SEVERIDAD (Baja, Media, Crítica).
        2. Si la noticia es 'fake news' o irrelevante, descártala.
        3. Genera un resumen HTML limpio y profesional siguiendo ESTRICTAMENTE el formato solicitado.
        4. Usa etiquetas de sentimiento con colores: <span style="color: #00C853;">Positivo</span>, <span style="color: #607D8B;">Neutro</span>, <span style="color: #D32F2F;">Negativo</span>.
        5. Incluye enlaces 'leer más' a las fuentes.
        
        {loaded_instructions}"""
    )

    # Convertimos la lista de noticias nuevas a texto para el prompt
    context_str = "\n".join([f"- {n.get('title', 'Sin título')} ({n.get('link', 'No link')})" for n in new_items])

    prompt = f"""
    Analiza las siguientes menciones NUEVAS recolectadas hoy {datetime.now().strftime('%Y-%m-%d')}:
    
    {context_str}
    
    Tarea:
    1. Verifica la veracidad usando Grounding (Google Search).
    2. Genera el 'Resumen Ejecutivo de Riesgo' en formato HTML para el cuerpo del correo.
    3. Asegúrate de incluir 'Estado General', 'Análisis' y 'Recomendación' al inicio, antes del detalle.
    """

    try:
        response = model.generate_content(prompt)
        html_report = response.text
        
        # 4. Acción: Enviar Correo y Guardar en Memoria
        # Formato de fecha personalizado para el asunto
        months_es = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        now = datetime.now()
        month_es = months_es[now.month]
        formatted_date = f"[{month_es} {now.day}, {now.year}]"
        
        subject = f"{formatted_date} Banco de Chile: Resumen de Marca e Inteligencia de Mercado - Powered by Gemini"
        
        # Enviar correo
        send_alert_email(subject, html_report)
        
        # Guardamos en memoria SOLO si el envío fue exitoso
        print("💾 Actualizando memoria...")
        for item in new_items:
            memory.remember_news(item)
            
        print("✅ Ciclo completado exitosamente.")

    except Exception as e:
        logging.error(f"❌ Error en la generación o envío: {e}")

if __name__ == "__main__":
    main()
