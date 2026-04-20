#!/usr/bin/env python3
"""
Sistema de scraping paralelo para GatoTV y TeleRed
Ejecuta ambos scrapers simultáneamente y combina resultados
"""

import asyncio
import aiohttp
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.gatotv_scraper import GatoTVScraper
from scrapers.telered_scraper import TeleRedScraper
from utils.xml_generator import XMLTVGenerator
from utils.validators import validate_epg
from config import SCRAPING_CONFIG, OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParallelEPGScraper:
    """Ejecuta múltiples scrapers en paralelo"""
    
    def __init__(self):
        self.results = {}
        self.errors = {}
        self.execution_times = {}
        self.generator = XMLTVGenerator()
        
    def ejecutar_scrapers_paralelo(self):
        """Ejecuta todos los scrapers en paralelo usando ThreadPool"""
        scrapers = {
            "gatotv": GatoTVScraper(SCRAPING_CONFIG),
            "telered": TeleRedScraper(SCRAPING_CONFIG)
        }
        
        logger.info(f"🚀 Iniciando {len(scrapers)} scrapers en paralelo...")
        
        # Usar ThreadPoolExecutor para paralelizar
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Enviar todas las tareas
            future_to_scraper = {
                executor.submit(self._ejecutar_scraper, nombre, scraper): nombre
                for nombre, scraper in scrapers.items()
            }
            
            # Recoger resultados a medida que completan
            for future in as_completed(future_to_scraper):
                scraper_name = future_to_scraper[future]
                try:
                    resultado, tiempo = future.result()
                    self.results[scraper_name] = resultado
                    self.execution_times[scraper_name] = tiempo
                    logger.info(f"✅ {scraper_name} completado en {tiempo:.2f} segundos")
                except Exception as e:
                    self.errors[scraper_name] = str(e)
                    logger.error(f"❌ {scraper_name} falló: {e}")
    
    def _ejecutar_scraper(self, nombre: str, scraper):
        """Wrapper para ejecutar un scraper y medir tiempo"""
        import time
        inicio = time.time()
        resultado = scraper.scrape()
        fin = time.time()
        return resultado, fin - inicio
    
    def combinar_resultados(self) -> Dict:
        """Combina los resultados de múltiples scrapers con prioridades"""
        logger.info("🔄 Combinando resultados de múltiples fuentes...")
        
        combinado = {}
        estadisticas = {
            "total_canales": 0,
            "total_programas": 0,
            "fuentes_usadas": []
        }
        
        # Definir prioridad de fuentes (GatoTV es más completa)
        prioridad = {
            "gatotv": 1,  # Mayor prioridad
            "telered": 2
        }
        
        # Primero, agregar todos los canales de todas las fuentes
        todos_canales = set()
        for fuente, datos in self.results.items():
            if datos:
                todos_canales.update(datos.keys())
                estadisticas["fuentes_usadas"].append(fuente)
        
        logger.info(f"📡 Canales únicos encontrados: {len(todos_canales)}")
        
        # Para cada canal, combinar programas de múltiples fuentes
        for canal in todos_canales:
            programas_por_fuente = {}
            
            # Recolectar programas de cada fuente
            for fuente, datos in self.results.items():
                if datos and canal in datos:
                    programas_por_fuente[fuente] = datos[canal]
            
            if not programas_por_fuente:
                continue
            
            # Elegir la mejor fuente según prioridad
            mejor_fuente = min(programas_por_fuente.keys(), 
                              key=lambda x: prioridad.get(x, 999))
            programas = programas_por_fuente[mejor_fuente]
            
            # Enriquecer con datos de otras fuentes si están disponibles
            for fuente, prog_fuente in programas_por_fuente.items():
                if fuente != mejor_fuente:
                    programas = self._enriquecer_programas(programas, prog_fuente)
            
            if programas:
                combinado[canal] = programas
                estadisticas["total_canales"] += 1
                estadisticas["total_programas"] += len(programas)
        
        logger.info(f"✅ Combinación completada: {estadisticas['total_canales']} canales, "
                   f"{estadisticas['total_programas']} programas")
        
        return combinado
    
    def _enriquecer_programas(self, programas_principal: List, 
                             programas_secundario: List) -> List:
        """Enriquece programas principales con datos de fuentes secundarias"""
        # Crear diccionario de programas por título para fácil acceso
        prog_dict = {p.get('titulo', '').lower(): p for p in programas_principal}
        
        for prog_sec in programas_secundario:
            titulo = prog_sec.get('titulo', '').lower()
            if titulo in prog_dict:
                # Enriquecer programa existente
                prog_principal = prog_dict[titulo]
                
                # Agregar descripción si no tiene
                if not prog_principal.get('descripcion') and prog_sec.get('descripcion'):
                    prog_principal['descripcion'] = prog_sec['descripcion']
                
                # Agregar horario si no tiene
                if not prog_principal.get('horario') and prog_sec.get('horario'):
                    prog_principal['horario'] = prog_sec['horario']
                
                # Agregar temporada/episodio si no tiene
                if not prog_principal.get('temporada') and prog_sec.get('temporada'):
                    prog_principal['temporada'] = prog_sec['temporada']
                    prog_principal['episodio'] = prog_sec.get('episodio')
        
        return programas_principal
    
    def generar_epg_final(self, datos_combinados: Dict):
        """Genera el EPG final combinado"""
        logger.info("📝 Generando EPG final combinado...")
        
        # Agregar canales
        for idx, (nombre_canal, programas) in enumerate(datos_combinados.items(), 1):
            channel_id = f"epg-{idx}.com.ar"
            self.generator.add_channel(channel_id, nombre_canal)
            
            # Procesar programas
            hoy = datetime.now()
            for programa in programas[:50]:  # Limitar a 50 programas por canal
                try:
                    titulo = programa.get('titulo', 'Sin título')
                    
                    # Determinar horario
                    if 'horario' in programa and programa['horario']:
                        hora_str = programa['horario']
                        try:
                            hora = datetime.strptime(hora_str, "%H:%M")
                            start_time = hoy.replace(hour=hora.hour, minute=hora.minute)
                        except:
                            start_time = hoy
                    else:
                        start_time = hoy
                    
                    end_time = start_time + timedelta(hours=1)
                    
                    # Agregar programa
                    self.generator.add_programme(
                        channel_id=channel_id,
                        title=titulo,
                        start=start_time,
                        end=end_time,
                        description=programa.get('descripcion', ''),
                        episode=programa.get('episodio'),
                        season=programa.get('temporada')
                    )
                except Exception as e:
                    logger.warning(f"Error procesando programa {programa.get('titulo', '?')}: {e}")
        
        # Guardar archivo
        archivo = self.generator.save(OUTPUT_DIR / "epg_combinado.xml")
        return archivo
    
    def generar_reporte(self):
        """Genera reporte detallado de la ejecución"""
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "scrapers_ejecutados": list(self.results.keys()),
            "scrapers_fallidos": list(self.errors.keys()),
            "tiempos_ejecucion": self.execution_times,
            "resultados": {
                fuente: {
                    "canales": len(datos),
                    "programas": sum(len(p) for p in datos.values()) if datos else 0
                }
                for fuente, datos in self.results.items()
            },
            "errores": self.errors
        }
        
        # Guardar reporte
        reporte_path = OUTPUT_DIR / "reporte_paralelo.json"
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📊 REPORTE DE EJECUCIÓN PARALELA")
        print("="*60)
        print(f"✅ Scrapers exitosos: {len(self.results)}/{len(self.results)+len(self.errors)}")
        print(f"⏱️  Tiempos de ejecución:")
        for scraper, tiempo in self.execution_times.items():
            print(f"   • {scraper}: {tiempo:.2f} segundos")
        print(f"\n📈 Resultados:")
        for fuente, stats in reporte["resultados"].items():
            print(f"   • {fuente}: {stats['canales']} canales, {stats['programas']} programas")
        
        if self.errors:
            print(f"\n⚠️ Errores:")
            for scraper, error in self.errors.items():
                print(f"   • {scraper}: {error[:100]}")
        
        print("="*60)
        
        return reporte

async def ejecutar_async():
    """Versión asíncrona (alternativa más rápida)"""
    import aiohttp
    import asyncio
    
    async def scrape_gatotv(session):
        """Scrapear GatoTV asíncronamente"""
        url = "https://www.gatotv.com/guia_tv/completa"
        async with session.get(url) as response:
            html = await response.text()
            # Procesar HTML...
            return {"canal1": [{"titulo": "Programa 1", "horario": "10:00"}]}
    
    async def scrape_telered(session):
        """Scrapear TeleRed asíncronamente"""
        url = "https://www.telered.com.ar/buscador-grilla"
        async with session.get(url) as response:
            html = await response.text()
            # Procesar HTML...
            return {"canal1": [{"titulo": "Programa 2", "horario": "10:30"}]}
    
    async with aiohttp.ClientSession() as session:
        # Ejecutar ambos scrapers en paralelo
        resultados = await asyncio.gather(
            scrape_gatotv(session),
            scrape_telered(session),
            return_exceptions=True
        )
        
        return resultados

def main():
    """Función principal"""
    print("🚀 INICIANDO SCRAPING PARALELO")
    print("="*60)
    
    # Crear instancia del scraper paralelo
    scraper = ParallelEPGScraper()
    
    # Ejecutar scrapers en paralelo
    scraper.ejecutar_scrapers_paralelo()
    
    # Verificar si hay resultados
    if not scraper.results:
        logger.error("❌ No se obtuvo ningún resultado de los scrapers")
        return 1
    
    # Combinar resultados
    datos_combinados = scraper.combinar_resultados()
    
    if not datos_combinados:
        logger.error("❌ No se pudo combinar los resultados")
        return 1
    
    # Generar EPG final
    archivo_final = scraper.generar_epg_final(datos_combinados)
    
    # Generar reporte
    reporte = scraper.generar_reporte()
    
    # Validar EPG
    stats = validate_epg(archivo_final)
    
    print(f"\n✨ ¡PROCESO COMPLETADO!")
    print(f"📁 Archivo EPG: {archivo_final}")
    print(f"📊 Estadísticas: {stats['total_canales']} canales, {stats['total_programas']} programas")
    
    return 0

if __name__ == "__main__":
    exit(main())
