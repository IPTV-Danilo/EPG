from src.scrapers.telered import scrape_telered
from src.scrapers.gatotv import scrape_gatotv
from src.merger import merge_epg
from src.xmltv_generator import generar_xmltv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Iniciando extracción de EPG...")
    
    logging.info("Scraping TeleRed...")
    telered_data = scrape_telered()
    logging.info(f"Obtenidos {len(telered_data)} programas de TeleRed")
    
    logging.info("Scraping GatoTV...")
    gatotv_data = scrape_gatotv()
    logging.info(f"Obtenidos {len(gatotv_data)} programas de GatoTV")
    
    logging.info("Fusionando ambas fuentes...")
    epg_completo = merge_epg(telered_data, gatotv_data)
    logging.info(f"Total después de fusión: {len(epg_completo)} programas")
    
    logging.info("Generando archivo XMLTV...")
    generar_xmltv(epg_completo)
    
    logging.info("Proceso completado.")

if __name__ == "__main__":
    main()
