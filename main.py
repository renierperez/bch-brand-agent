import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, SafetySetting
from tools import search_financial_news, search_social_media
from memory import BrandMemory
from mailer import send_alert_email
from datetime import datetime
import re
from visualizer import generate_trend_chart

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
        
        # Enviar correo de "Sin Novedades"
        months_es = {
            1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
        }
        now = datetime.now()
        month_es = months_es[now.month]
        formatted_date = f"[{month_es} {now.day}, {now.year}]"
        
        subject = f"{formatted_date} Banco de Chile: Reporte de Monitoreo - Sin Novedades"
        body = """
        <div style="text-align: center; padding: 30px 20px;">
            <div style="font-size: 48px; margin-bottom: 15px;">✅</div>
            <h2 style="color: #2E7D32; margin: 0 0 10px 0; font-family: Helvetica, Arial, sans-serif;">Sin Novedades Relevantes</h2>
            <p style="color: #555; font-size: 16px; line-height: 1.5; margin: 0 0 20px 0;">
                El sistema de monitoreo no ha detectado nuevas menciones críticas ni noticias relevantes desde la última ejecución.
            </p>
            <div style="background-color: #f5f5f5; border-radius: 8px; padding: 15px; display: inline-block;">
                <p style="color: #777; font-size: 14px; margin: 0;">
                    <strong>Estado del Agente:</strong> 🟢 Activo y Monitoreando
                </p>
            </div>
        </div>
        """
        send_alert_email(subject, body)
        return

    print(f"⚡ Procesando {len(new_items)} noticias nuevas con Gemini...")

    # 3. Análisis Cognitivo (Gemini 2.5 Pro con Grounding)
    # Definición de la herramienta de búsqueda
    # Usamos el workaround probado si la versión estándar falla, pero intentaremos seguir la guía del usuario.
    # Sin embargo, para asegurar compatibilidad con el entorno actual, usaré el workaround que sé que funciona
    # o la sintaxis robusta.
    # Definición de la herramienta de búsqueda
    # Usamos Tool.from_dict porque la clase 'GoogleSearch' no existe en la versión actual del SDK instalada.
    # Esto genera el payload JSON correcto: {"tools": [{"google_search": {}}]}
    # que es requerido por la API para evitar el error 400.
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
    context_str = "\n".join([f"- {n.get('title', 'Sin título')} (Date: {n.get('date', 'Unknown')}) [Link: {n.get('link', 'No link')}]" for n in new_items])

    prompt = f"""
    Analiza las siguientes menciones NUEVAS recolectadas hoy {datetime.now().strftime('%Y-%m-%d')}:
    
    {context_str}
    
    Tarea:
    1. Verifica la veracidad usando Grounding (Google Search).
    2. FILTRA: Descarta noticias con fecha > 3 meses.
    3. Genera el 'Resumen Ejecutivo de Riesgo' en formato HTML.
    4. Asegúrate de incluir 'Brand Health Index' (0-100) y Tags [CATEGORÍA].
    5. USA ENLACES DIRECTOS (No Google Redirects).
    """

    try:
        response = model.generate_content(prompt)
        html_report = response.text
        
        # Extract Score
        current_score = 0
        try:
            match = re.search(r"Brand Health Index:.*?(\d+)/100", html_report)
            if match:
                current_score = int(match.group(1))
        except Exception as e:
            logging.warning(f"Could not extract Brand Health Index: {e}")

        # Save to Memory
        if current_score > 0:
            memory.save_daily_summary(current_score)

        # Generate Chart
        history_data = memory.get_history_stats(limit=10)
        chart_buffer = None
        if len(history_data) > 1:
            try:
                chart_buffer = generate_trend_chart(history_data)
            except Exception as e:
                logging.error(f"Error generating chart: {e}")
        
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
        send_alert_email(subject, html_report, chart_buffer=chart_buffer)
        
        # Guardamos en memoria SOLO si el envío fue exitoso
        print("💾 Actualizando memoria...")
        for item in new_items:
            memory.remember_news(item)
            
        print("✅ Ciclo completado exitosamente.")

    except Exception as e:
        logging.error(f"❌ Error en la generación o envío: {e}")

if __name__ == "__main__":
    main()
