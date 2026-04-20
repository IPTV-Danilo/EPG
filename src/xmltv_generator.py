from datetime import datetime
import xml.etree.ElementTree as ET
import pytz
import os

def generar_xmltv(programs, output_file='data/epg.xml'):
    """
    Genera archivo XMLTV estándar
    """
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    tv = ET.Element('tv')
    tv.set('generator-info-name', 'EPG Argentina Completo')
    tv.set('source-info-url', 'https://github.com/tuusuario/epg-argentina-completo')
    tv.set('source-info-name', 'TeleRed + GatoTV')
    
    # Agrupar por canal
    canales = {}
    for prog in programs:
        if prog['channel'] not in canales:
            canales[prog['channel']] = True
            channel_elem = ET.SubElement(tv, 'channel', id=prog['channel'])
            display_name = ET.SubElement(channel_elem, 'display-name')
            display_name.text = prog['channel']
    
    # Agregar programas
    for prog in programs:
        # Formatear fechas para XMLTV
        start_str = prog['start'].strftime('%Y%m%d%H%M%S +0000')
        end_str = prog['end'].strftime('%Y%m%d%H%M%S +0000')
        
        programme = ET.SubElement(tv, 'programme',
                                  start=start_str,
                                  end=end_str,
                                  channel=prog['channel'])
        
        title = ET.SubElement(programme, 'title', lang='es')
        title.text = prog['title']
        
        # Agregar fuente como descripción
        desc = ET.SubElement(programme, 'desc', lang='es')
        desc.text = f"Fuente: {prog.get('source', 'desconocida')}"
    
    # Guardar archivo
    tree = ET.ElementTree(tv)
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"✅ XMLTV generado: {output_file}")
    
    # Mostrar estadísticas
    print(f"📊 Estadísticas: {len(canales)} canales, {len(programs)} programas")
