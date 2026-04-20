import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def scrape_telered():
    """
    Extrae programación de https://www.telered.com.ar/buscador-grilla
    Retorna lista de dicts: {'channel': 'Canal 7', 'title': 'Programa', 'start': datetime, 'end': datetime}
    """
    url = "https://www.telered.com.ar/buscador-grilla"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    programs = []
    # La estructura de telered: cada bloque .tv-program (o similar)
    # Según el HTML que veo, hay divs con información de canal y horario
    # Ejemplo: <div class="tv-program"> ... <span class="channel">...</span> <span class="time">...</span> <span class="title">...</span>
    
    # Adapto el selector a lo que realmente tiene la página (inspeccioné)
    for bloque in soup.find_all('div', class_='tv-program'):
        canal_tag = bloque.find('div', class_='channel')
        titulo_tag = bloque.find('div', class_='program-title')
        hora_tag = bloque.find('div', class_='schedule-time')
        
        if not (canal_tag and titulo_tag and hora_tag):
            continue
        
        canal = canal_tag.get_text(strip=True)
        titulo = titulo_tag.get_text(strip=True)
        hora_str = hora_tag.get_text(strip=True)  # Ej: "10:00hs"
        
        # Convertir hora a datetime (asumimos fecha actual)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        match = re.search(r'(\d{1,2}):(\d{2})', hora_str)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2))
            start_time = today + timedelta(hours=hora, minutes=minuto)
            # Asumimos duración típica 1 hora (se puede mejorar)
            end_time = start_time + timedelta(hours=1)
            
            programs.append({
                'channel': canal,
                'title': titulo,
                'start': start_time,
                'end': end_time,
                'source': 'telered'
            })
    
    return programs
