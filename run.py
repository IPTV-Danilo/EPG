#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.telered import scrape_telered
from scrapers.gatotv import scrape_gatotv
from merger import merge_epg
from xmltv_generator import generar_xmltv

def main():
    print("=" * 60)
    print(f"🚀 Iniciando EPG Argentina - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Scraping
    print("\n📡 1. Extrayendo datos de TeleRed...")
    telered_data = scrape_telered()
    print(f"   ✓ {len(telered_data)} programas")
    
    print("\n📺 2. Extrayendo datos de GatoTV...")
    gatotv_data = scrape_gatotv()
    print(f"   ✓ {len(gatotv_data)} programas")
    
    # Fusión
    print("\n🔗 3. Fusionando ambas fuentes...")
    epg_completo = merge_epg(telered_data, gatotv_data)
    
    # Generar XML
    print("\n💾 4. Generando archivo XMLTV...")
    generar_xmltv(epg_completo)
    
    print("\n✅ Proceso completado exitosamente!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
