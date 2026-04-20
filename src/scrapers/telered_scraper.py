"""
Scraper específico para TeleRed
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class TeleRedScraper(BaseScraper):
    """Scraper para TeleRed"""
    
    def __init__(self, config: Dict):
        super().__init__("TeleRed", config)
        self.url = "https://www.telered.com.ar/buscador-grilla"
    
    def scrape(self) -> Dict:
        """Ejecuta scraping de TeleRed"""
        logger.info("Iniciando scraping de TeleRed")
        
        html = self.fetch_html(self.url)
        if not html:
            logger.error("No se pudo obtener el HTML de TeleRed")
            return {}
        
        return self.parse_html(html)
    
    def parse_html(self, html: str) -> Dict:
        """Parsea HTML de TeleRed"""
        soup = BeautifulSoup(html, 'html.parser')
        datos = {}
        
        # Estrategia principal: Buscar por estructura conocida
        # Basado en el HTML que me mostraste anteriormente
        
        # Buscar todos los canales (identificados por números)
        canales = soup.find_all(string=re.compile(r'\d+[A-Za-z\s]+Ver más', re.IGNORECASE))
        
        for canal_texto in canales:
            # Extraer nombre del canal
            nombre_match = re.search(r'\d+([A-Za-z\sáéíóúñÑ]+)Ver más', canal_texto, re.IGNORECASE)
            if not nombre_match:
                continue
            
            nombre_canal = self._limpiar_nombre_canal(nombre_match.group(1))
            
            # Buscar programas cercanos
            contenedor = canal_texto.find_parent()
            if contenedor:
                programas = self._extraer_programas_cercanos(contenedor)
                if programas:
                    datos[nombre_canal] = programas
        
        logger.info(f"TeleRed: {len(datos)} canales encontrados")
        return datos
    
    def _extraer_programas_cercanos(self, elemento) -> List[Dict]:
        """Extrae programas cercanos al elemento del canal"""
        programas = []
        
        # Buscar texto con horarios
        textos = elemento.find_all(string=re.compile(r'\d{1,2}:\d{2}hs'))
        
        for texto in textos:
            programa = self._extraer_programa_texto(texto.strip())
            if programa:
                programas.append(programa)
        
        return programas
    
    def _extraer_programa_texto(self, texto: str) -> Optional[Dict]:
        """Extrae programa de texto"""
        # Patrón: "Nombre del programa 14:30hs"
        patron = re.compile(r'^(.*?)\s+(\d{1,2}:\d{2})hs$', re.IGNORECASE)
        match = patron.search(texto)
        
        if match:
            titulo = match.group(1).strip()
            hora = match.group(2)
            return {
                'titulo': titulo,
                'horario': hora,
                'fuente': 'telered'
            }
        
        return None
    
    def _limpiar_nombre_canal(self, nombre: str) -> str:
        """Limpia nombre de canal"""
        nombre = re.sub(r'\s+', ' ', nombre).strip()
        
        # Mapeo de nombres
        mapeo = {
            'Canal Provincial': 'Canal Provincial',
            'Net TV': 'Net TV',
            'AMÉRICA': 'América TV',
            'TELEFE': 'Telefe',
            'TV PÚBLICA': 'TV Pública',
            'El Trece': 'El Trece',
            'El Nueve': 'El Nueve',
        }
        
        return mapeo.get(nombre.upper(), nombre)
