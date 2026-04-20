import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def scrape_telered():
    """
    Extrae programación de https://www.telered.com.ar/buscador-grilla
    Versión robusta con múltiples selectores
    """
    url = "https://www.telered.com.ar/buscador-grilla"
    
    # Headers realistas
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al acceder a TeleRed: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'lxml')
    programs = []
    
    # Buscar por múltiples estructuras posibles
    # La página de TeleRed tiene canales con números y programas con horarios
    
    # Estrategia 1: Buscar bloques de canal
    canales = soup.find_all(['div', 'section'], class_=re.compile(r'(channel|canal|tv-channel)', re.I))
    
    if not canales:
        # Estrategia 2: Buscar por texto de números de canal
        for elemento in soup.find_all(['div', 'span', 'a']):
            texto = elemento.get_text(strip=True)
            # Buscar patrones como "7Canal Provincial7" o "8Net TV8"
            match = re.search(r'(\d+)([A-Za-z\s]+)', texto)
            if match and len(texto) < 50:
                canal_num = match.group(1)
                canal_nombre = match.group(2).strip()
                
                # Buscar programas cercanos
                parent = elemento.find_parent(['div', 'section'])
                if parent:
                    horarios = parent.find_all(string=re.compile(r'\d{1,2}:\d{2}hs?'))
                    titulos = parent.find_all(['span', 'div'], class_=re.compile(r'(title|programa)', re.I))
                    
                    for i, hora_elem in enumerate(horarios[:10]):  # Máximo 10 programas por canal
                        hora_texto = hora_elem.strip()
                        titulo = titulos[i].get_text(strip=True) if i < len(titulos) else "Programa"
                        
                        # Parsear hora
                        match_hora = re.search(r'(\d{1,2}):(\d{2})', hora_texto)
                        if match_hora:
                            hora = int(match_hora.group(1))
                            minuto = int(match_hora.group(2))
                            ahora = datetime.now()
                            start_time = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                            
                            # Si la hora ya pasó, asumir que es para mañana
                            if start_time < ahora:
                                start_time += timedelta(days=1)
                            
                            end_time = start_time + timedelta(hours=1)
                            
                            programs.append({
                                'channel': f"{canal_num} {canal_nombre}",
                                'title': titulo,
                                'start': start_time,
                                'end': end_time,
                                'source': 'telered'
                            })
    
    print(f"📡 TeleRed: {len(programs)} programas extraídos")
    return programs
