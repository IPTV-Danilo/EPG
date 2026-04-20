import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

def scrape_gatotv():
    """
    Extrae programación de https://www.gatotv.com/guia_tv/completa
    La estructura es una tabla o grid con canales como filas y horas como columnas.
    """
    url = "https://www.gatotv.com/guia_tv/completa"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    programs = []
    # Detectamos la tabla principal (por lo general tiene clase 'tv-table')
    table = soup.find('table', class_='tv-table')
    if not table:
        return programs
    
    rows = table.find_all('tr')
    for row in rows:
        canal_cell = row.find('td', class_='channel')
        if not canal_cell:
            continue
        canal = canal_cell.get_text(strip=True)
        
        # Cada celda de programa contiene título y horario
        program_cells = row.find_all('td', class_='program')
        for cell in program_cells:
            title_tag = cell.find('div', class_='title')
            hour_tag = cell.find('div', class_='hour')
            if not (title_tag and hour_tag):
                continue
            
            titulo = title_tag.get_text(strip=True)
            hora_str = hour_tag.get_text(strip=True)  # "14:30"
            match = re.search(r'(\d{1,2}):(\d{2})', hora_str)
            if match:
                hora = int(match.group(1))
                minuto = int(match.group(2))
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                start_time = today + timedelta(hours=hora, minutes=minuto)
                end_time = start_time + timedelta(hours=1)  # Duración por defecto
                
                programs.append({
                    'channel': canal,
                    'title': titulo,
                    'start': start_time,
                    'end': end_time,
                    'source': 'gatotv'
                })
    
    return programs
