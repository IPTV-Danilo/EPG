import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def scrape_gatotv():
    """
    Extrae programación de https://www.gatotv.com/guia_tv/completa
    """
    url = "https://www.gatotv.com/guia_tv/completa"
    
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al acceder a GatoTV: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'lxml')
    programs = []
    
    # Buscar la tabla principal
    tabla = soup.find('table', class_=re.compile(r'(tv-table|guia|programacion)', re.I))
    if not tabla:
        tabla = soup.find('table')
    
    if not tabla:
        print("⚠️ No se encontró tabla en GatoTV")
        return []
    
    filas = tabla.find_all('tr')
    
    for fila in filas:
        # Buscar nombre del canal
        canal_cell = fila.find('td', class_=re.compile(r'(channel|canal)', re.I))
        if not canal_cell:
            # Intentar con th
            canal_cell = fila.find('th')
        
        if canal_cell:
            canal = canal_cell.get_text(strip=True)
            # Limpiar nombre del canal
            canal = re.sub(r'\s+', ' ', canal).strip()
            
            # Buscar celdas de programas
            celdas_programa = fila.find_all('td', class_=re.compile(r'(program|show)', re.I))
            if not celdas_programa:
                celdas_programa = fila.find_all('td')[1:]  # Todas excepto la primera
            
            for celda in celdas_programa:
                # Buscar título
                titulo_elem = celda.find(['div', 'span'], class_=re.compile(r'(title|nombre)', re.I))
                if not titulo_elem:
                    titulo_elem = celda
                
                titulo = titulo_elem.get_text(strip=True)
                if len(titulo) < 2 or titulo == "":  # Saltar celdas vacías
                    continue
                
                # Buscar hora
                hora_elem = celda.find(['div', 'span'], class_=re.compile(r'(hour|hora|time)', re.I))
                if hora_elem:
                    hora_texto = hora_elem.get_text(strip=True)
                else:
                    # Buscar patrón de hora en el texto
                    match_hora = re.search(r'(\d{1,2}):(\d{2})', celda.get_text())
                    if match_hora:
                        hora_texto = match_hora.group(0)
                    else:
                        continue
                
                # Parsear hora
                match_hora = re.search(r'(\d{1,2}):(\d{2})', hora_texto)
                if match_hora:
                    hora = int(match_hora.group(1))
                    minuto = int(match_hora.group(2))
                    ahora = datetime.now()
                    start_time = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                    
                    if start_time < ahora:
                        start_time += timedelta(days=1)
                    
                    end_time = start_time + timedelta(hours=1)
                    
                    programs.append({
                        'channel': canal,
                        'title': titulo,
                        'start': start_time,
                        'end': end_time,
                        'source': 'gatotv'
                    })
    
    print(f"📺 GatoTV: {len(programs)} programas extraídos")
    return programs
