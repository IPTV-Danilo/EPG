from datetime import datetime
import xml.etree.ElementTree as ET
import pytz

def generar_xmltv(programs, output_file='data/epg.xml'):
    """
    Genera un archivo XMLTV compatible con reproductores.
    """
    tv = ET.Element('tv')
    tv.set('generator-info-name', 'EPG Argentina Completo')
    tv.set('source-info-url', 'https://github.com/tuusuario/epg-argentina-completo')
    
    # Agrupar programas por canal para crear los <channel>
    channels = set(p['channel'] for p in programs)
    for ch in channels:
        channel_elem = ET.SubElement(tv, 'channel', id=ch)
        display_name = ET.SubElement(channel_elem, 'display-name')
        display_name.text = ch
    
    # Agregar cada programa
    for prog in programs:
        programme = ET.SubElement(tv, 'programme',
                                  start=prog['start'].astimezone(pytz.UTC).strftime('%Y%m%d%H%M%S %z'),
                                  end=prog['end'].astimezone(pytz.UTC).strftime('%Y%m%d%H%M%S %z'),
                                  channel=prog['channel'])
        title = ET.SubElement(programme, 'title')
        title.text = prog['title']
        
        if 'description' in prog:
            desc = ET.SubElement(programme, 'desc')
            desc.text = prog['description']
    
    # Guardar archivo
    tree = ET.ElementTree(tv)
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"✅ EPG generado en {output_file}")
