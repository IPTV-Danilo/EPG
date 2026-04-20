from datetime import datetime

def merge_epg(telered_data, gatotv_data):
    """
    Combina los datos de ambas fuentes.
    Si un mismo canal y horario tienen programas distintos:
    - Priorizamos GatoTV porque suele tener más detalles, pero conservamos el de TeleRed como alternativa.
    Retorna un dict con key (canal, start_time) y el mejor programa.
    """
    merged = {}
    
    # Primero cargamos GatoTV (prioritario)
    for prog in gatotv_data:
        key = (prog['channel'], prog['start'].timestamp())
        merged[key] = prog.copy()
    
    # Luego agregamos TeleRed solo si no existe o si tiene más información (duración más precisa, etc.)
    for prog in telered_data:
        key = (prog['channel'], prog['start'].timestamp())
        if key not in merged:
            merged[key] = prog.copy()
        else:
            # Si ya existe, complementamos datos (ej: descripción si la tuviera)
            if 'description' not in merged[key] and 'description' in prog:
                merged[key]['description'] = prog['description']
            merged[key]['source'] = 'merged'
    
    # Ordenar por canal y hora
    return sorted(merged.values(), key=lambda x: (x['channel'], x['start']))
