import matplotlib.pyplot as plt
import io
import matplotlib.dates as mdates

def generate_trend_chart(history_data: list) -> io.BytesIO:
    """Genera un gráfico PNG de la tendencia del Brand Index."""
    if not history_data:
        return None

    dates = [h['date'] for h in history_data]
    scores = [h['score'] for h in history_data]

    # Configuración de estilo "Corporativo"
    plt.figure(figsize=(8, 3)) # Ancho, Alto
    plt.style.use('bmh') # Estilo limpio
    
    # Dibujar línea
    plt.plot(dates, scores, marker='o', linestyle='-', color='#003399', linewidth=2, label='Brand Health')
    
    # Zona de "Salud" (Fondo verde suave arriba de 80)
    plt.axhspan(80, 100, color='green', alpha=0.1, label='Zona Saludable')
    plt.axhspan(0, 50, color='red', alpha=0.1, label='Zona Crítica')

    # Formato
    plt.title('Evolución Brand Health Index (Últimas Ejecuciones)', fontsize=10)
    plt.ylim(0, 105)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Formato de fechas en eje X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    plt.xticks(rotation=0)
    plt.tight_layout()

    # Guardar en buffer de memoria
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer
