import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def send_alert_email(subject: str, body: str, recipient: str = None, chart_buffer=None) -> str:
    """Sends an email alert with Banco de Chile branding and optional trend chart."""
    sender_email = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASSWORD")
    if not recipient:
        recipient = os.environ.get("BCC_EMAILS", sender_email) # Default to BCC or sender
    
    if not sender_email or not password:
        return "Gmail credentials not found."
    
    msg = MIMEMultipart('related')
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    
    import markdown
    # Clean Gemini output if it includes code blocks
    cleaned_body = body.replace("```html", "").replace("```", "").strip()
    html_body_content = markdown.markdown(cleaned_body)
    
    # Chart HTML section
    chart_html = ""
    if chart_buffer:
        chart_html = """
        <div style="margin-top: 30px; text-align: center;">
            <h3 style="color: #666; font-size: 16px; margin-bottom: 15px;">Tendencia Histórica (Brand Health Index)</h3>
            <img src="cid:trend_chart" alt="Gráfico de Tendencia" style="max-width: 100%; border: 1px solid #ddd; border-radius: 5px;">
        </div>
        """

    # Banco de Chile Branding (Simplified HTML)
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff; border: 1px solid #ddd; border-top: none;">
            <div style="background-color: #003399; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Banco de Chile</h1>
                <p style="color: #ccc; margin: 5px 0 0 0; font-size: 14px;">Vigilancia de Marca & Inteligencia de Mercado</p>
            </div>
            <div style="padding: 20px;">
                
                <!-- Executive Summary Section -->
                <div style="background-color: #f0f4f8; padding: 20px; border-left: 5px solid #003399; margin-bottom: 25px; border-radius: 0 5px 5px 0;">
                    <h2 style="color: #003399; margin-top: 0; font-size: 18px; border-bottom: 1px solid #003399; padding-bottom: 10px;">Resumen Ejecutivo de Riesgo</h2>
                    <div style="font-size: 15px; line-height: 1.6; color: #333;">
                        {html_body_content}
                    </div>
                </div>
                
                {chart_html}
                
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
            server.send_message(msg)
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email: {str(e)}"
