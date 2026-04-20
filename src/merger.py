def merge_epg(telered_data, gatotv_data):
    """
    Fusiona datos de ambas fuentes
    Prioridad: GatoTV (más completo), complementa con TeleRed
    """
    merged = {}
    
    # Primero cargar GatoTV (prioritario)
    for prog in gatotv_data:
        key = (prog['channel'], prog['start'].isoformat())
        merged[key] = prog.copy()
        merged[key]['source'] = 'gatotv_primary'
    
    # Luego agregar TeleRed donde no exista
    for prog in telered_data:
        key = (prog['channel'], prog['start'].isoformat())
        if key not in merged:
            merged[key] = prog.copy()
            merged[key]['source'] = 'telered_secondary'
        else:
            # Si existe, complementar información
            if len(prog['title']) > len(merged[key]['title']):
                merged[key]['title'] = prog['title']
    
    # Convertir a lista y ordenar
    result = list(merged.values())
    result.sort(key=lambda x: (x['channel'], x['start']))
    
    print(f"🔗 Fusión completada: {len(result)} programas únicos")
    return result
