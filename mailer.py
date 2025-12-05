import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def _generate_indicators_html(indicators):
    if not indicators:
        return ""
    
    # CSS Inline para las "tarjetas" de indicadores
    card_style = """
        display: inline-block;
        width: 22%; 
        margin: 0 1%;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        text-align: center;
        padding: 10px 0;
    """
    
    value_style = "font-size: 16px; font-weight: bold; color: #003399; margin: 5px 0;"
    label_style = "font-size: 11px; color: #666; text-transform: uppercase;"

    html = f"""
    <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
        <h4 style="color: #444; margin-bottom: 15px; font-size: 14px;">Indicadores Económicos (Chile)</h4>
        <div style="text-align: center;">
            <div style="{card_style}">
                <div style="{label_style}">UF Hoy</div>
                <div style="{value_style}">{indicators['UF']['value']}</div>
            </div>
            <div style="{card_style}">
                <div style="{label_style}">Dólar</div>
                <div style="{value_style}">{indicators['Dolar']['value']}</div>
            </div>
            <div style="{card_style}">
                <div style="{label_style}">Euro</div>
                <div style="{value_style}">{indicators['Euro']['value']}</div>
            </div>
            <div style="{card_style}">
                <div style="{label_style}">UTM</div>
                <div style="{value_style}">{indicators['UTM']['value']}</div>
            </div>
        </div>
        <p style="font-size: 10px; color: #999; text-align: center; margin-top: 10px;">
            Fuente: mindicador.cl
        </p>
    </div>
    """
    return html

def send_alert_email(subject: str, body: str, recipient: str = None, chart_buffer=None, indicators=None, brand_config=None) -> str:
    """Sends an email alert with dynamic branding."""
    
    # Configuración de Marca (Fallback a Banco de Chile si no se provee)
    primary_color = brand_config.get('primary_color', '#003399') if brand_config else '#003399'
    secondary_color = brand_config.get('secondary_color', '#FFFFFF') if brand_config else '#FFFFFF'
    bank_name = brand_config.get('name', 'Banco de Chile') if brand_config else 'Banco de Chile'
    header_content = brand_config.get('header_html', bank_name) if brand_config else bank_name

    # CSS para el Tech Insight (Estilo Dinámico)
    tech_insight_style = f"""
    <style>
        .tech-insight {{
            background-color: #f8f9fa;
            border-left: 4px solid {primary_color}; /* Color dinámico */
            padding: 15px;
            margin-top: 20px;
            margin-bottom: 20px;
            font-family: 'Roboto', Arial, sans-serif;
            font-size: 14px;
            color: #5f6368;
            border-radius: 0 4px 4px 0;
        }}
        .tech-insight strong {{
            color: #202124;
            display: block;
            margin-bottom: 5px;
        }}
    </style>
    """

    sender_email = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASSWORD")
    if not recipient:
        recipient = os.environ.get("BCC_EMAILS", sender_email).replace(";", ",")
    
    if not sender_email or not password:
        return "Gmail credentials not found."
    
    msg = MIMEMultipart('related')
    msg['From'] = sender_email
    msg['To'] = sender_email # To field shows sender (self-copy) to hide BCCs
    msg['Subject'] = subject
    
    # Parse recipients list
    to_addrs = recipient.split(',')
    
    import markdown
    cleaned_body = body.replace("```html", "").replace("```", "").strip()
    html_body_content = markdown.markdown(cleaned_body)
    
    # Inyectamos el estilo
    html_body_content = tech_insight_style + html_body_content
    
    # Chart HTML section
    chart_html = ""
    if chart_buffer:
        chart_html = """
        <div style="margin-top: 30px; text-align: center;">
            <h3 style="color: #666; font-size: 16px; margin-bottom: 15px;">Tendencia Histórica (Brand Health Index)</h3>
            <img src="cid:trend_chart" alt="Gráfico de Tendencia" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
        </div>
        """

    # HTML Body con Branding Dinámico
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border: 1px solid #ddd; border-top: none;">
            <div style="background-color: {primary_color}; padding: 20px; text-align: center;">
                <h1 style="color: {secondary_color}; margin: 0; font-size: 24px;">{header_content}</h1>
                <p style="color: #eee; margin: 5px 0 0 0; font-size: 14px;">Vigilancia de Marca & Inteligencia de Mercado</p>
            </div>
            <div style="padding: 20px;">
                
                <!-- Executive Summary Section -->
                <div style="background-color: #f0f4f8; padding: 20px; border-left: 5px solid {primary_color}; margin-bottom: 25px; border-radius: 0 5px 5px 0;">
                    <h2 style="color: {primary_color}; margin-top: 0; font-size: 18px; border-bottom: 1px solid {primary_color}; padding-bottom: 10px;">Resumen Ejecutivo de Riesgo</h2>
                    <div style="font-size: 15px; line-height: 1.6; color: #333;">
                        {html_body_content}
                    </div>
                </div>
                
                {chart_html}
                
                {_generate_indicators_html(indicators)}
                
                <div style="font-size: 12px; color: #666; margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; text-align: center;">
                    <p style="margin: 5px 0;">Este es un mensaje automático del Agente de Vigilancia de Marca.</p>
                    <p style="margin: 5px 0;">Generado por la IA de <strong>Google Gemini 2.5 Pro</strong></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Attach HTML part
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    msg_alternative.attach(MIMEText(html_body, 'html'))
    
    # Attach Image if exists
    if chart_buffer:
        try:
            image = MIMEImage(chart_buffer.read())
            image.add_header('Content-ID', '<trend_chart>')
            image.add_header('Content-Disposition', 'inline', filename='trend.png')
            msg.attach(image)
        except Exception as e:
            print(f"Error attaching image: {e}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg, to_addrs=to_addrs)
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"
