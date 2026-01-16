import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import re

# --- CONFIGURACIÓN ---
base_url = "https://www.yapo.cl/bienes-raices-alquiler-apartamentos/valparaiso-valparaiso"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
NOMBRE_ARCHIVO = "arriendos_valpo_normalizado.csv"

# --- 1. NUEVA FUNCIÓN: OBTENER UF ---
def obtener_valor_uf():
    """Consulta la API de mindicador.cl para obtener la UF de hoy"""
    print("💰 Consultando valor de la UF hoy...")
    try:
        url_api = "https://mindicador.cl/api/uf"
        response = requests.get(url_api)
        data = response.json()
        # La API devuelve una lista de series, tomamos la de hoy (índice 0)
        valor = data['serie'][0]['valor']
        print(f"✅ Valor UF encontrado: ${valor}")
        return valor
    except Exception as e:
        print(f"⚠️ No se pudo obtener la UF ({e}). Usaremos 38000 por defecto.")
        return 38000 # Valor fallback por si falla internet

# --- 2. LÓGICA DE LIMPIEZA MEJORADA ---
def procesar_precio(texto_precio, valor_uf_dia):
    """
    Lógica inteligente:
    1. Limpia el texto de basura.
    2. Maneja puntos y comas correctamente.
    3. Si el valor es gigante (> 5000), asume CLP aunque diga UF.
    """
    if not texto_precio:
        return 0, "N/A"
    
    # Normalización: Quitamos todo lo que no sea número, punto o coma
    # Ejemplo: "UF 350.000,00" -> "350.000,00"
    limpio = re.sub(r'[^\d,.]', '', texto_precio)
    
    # Truco Chileno:
    # Si tiene coma, asumimos que es el decimal.
    # 1. Reemplazamos los puntos de mil por nada (350.000 -> 350000)
    # 2. Reemplazamos la coma por punto (para que Python entienda decimales)
    limpio_numerico = limpio.replace('.', '').replace(',', '.')
    
    try:
        valor_float = float(limpio_numerico)
    except ValueError:
        return 0, "ErrorFormato"

    # Lógica de detección de moneda
    es_uf_detectado = "UF" in texto_precio.upper()
    
    # REGLA DE SENTIDO COMÚN:
    # Si el valor es mayor a 5000, CASI SEGURO son pesos, no UF.
    # (Un arriendo de 5000 UF son 190 millones de pesos mensuales, imposible)
    if valor_float > 5000:
        return int(valor_float), "CLP (Corregido)"
        
    # Si es un número pequeño (ej: 12.5) y decía UF, entonces sí convertimos
    if es_uf_detectado:
        precio_en_pesos = int(valor_float * valor_uf_dia)
        return precio_en_pesos, "UF"
    
    # Caso por defecto: Pesos
    return int(valor_float), "CLP"

def obtener_ultima_pagina():
    # ... (Tu código de paginación sigue igual) ...
    try:
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        boton_ultima = soup.find(class_='d3-pagination__page--last')
        if boton_ultima and boton_ultima.text.strip().isdigit():
            return int(boton_ultima.text.strip())
        return 1
    except:
        return 1

# --- PROCESO PRINCIPAL ---
def ejecutar_scraper():
    datos_totales = []
    
    # 1. Obtenemos la UF UNA SOLA VEZ antes de empezar
    valor_uf_actual = obtener_valor_uf()
    
    total_paginas = obtener_ultima_pagina()
    
    print(f"🚀 Iniciando extracción con UF a ${valor_uf_actual}...")

    for pagina in range(1, total_paginas + 1):
        url_actual = base_url if pagina == 1 else f"{base_url}.{pagina}"
        print(f"--- Procesando Pág {pagina}/{total_paginas} ---")
        
        try:
            response = requests.get(url_actual, headers=headers)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            anuncios = soup.find_all('div', class_='d3-ad-tile')

            if not anuncios: break

            for anuncio in anuncios:
                titulo_el = anuncio.find(class_='d3-ad-tile__title')
                precio_el = anuncio.find(class_='d3-ad-tile__price')
                descuento_el = anuncio.find(class_='d3-ad-tile__price-reduction')
                # CAMBIO: Usamos find_all para traer TODOS los links posibles de la tarjeta
                links_candidatos = anuncio.find_all('a', href=True)
                link_final = "No disponible"

                for link_el in links_candidatos:
                    raw_link = link_el['href']
                    
                    # Aplicamos tus filtros inteligentes
                    if raw_link and raw_link != "#" and "yapo.cl" not in raw_link: 
                        # Nota: Agregué "yapo.cl not in raw_link" como seguridad, 
                        # pero tu lógica de startswith es la importante.
                        pass 

                    # Validación fuerte:
                    if raw_link and raw_link != "#":
                        # Caso Relativo
                        if raw_link.startswith("/"):
                            link_final = f"https://www.yapo.cl{raw_link}"
                            break # ¡ENCONTRADO! Rompemos el bucle y dejamos de buscar
                            
                        # Caso Absoluto
                        elif raw_link.startswith("http"):
                            link_final = raw_link
                            break # ¡ENCONTRADO!

                # Guardamos 'link_final' en tu diccionario o lista
                print(f"🔗 Link rescatado: {link_final}")

                if titulo_el and precio_el:
                    reduccion_interna = precio_el.find(class_="d3-ad-tile__price-reduction")
                    if reduccion_interna: reduccion_interna.decompose()

                    titulo = titulo_el.text.strip()
                    precio_texto = precio_el.text.strip()
                    
                    # 3. USAMOS LA NUEVA LÓGICA CONVERTIDORA
                    precio_final, moneda_origen = procesar_precio(precio_texto, valor_uf_actual)
                    
                    descuento_texto = descuento_el.text.strip() if descuento_el else "No"

                    item = {
                        "Titulo": titulo,
                        "Precio_Original_Texto": precio_texto, # Guardamos el original por si acaso
                        "Precio_CLP_Final": precio_final,      # Este es el que usaremos para SQL y Gráficos
                        "Moneda_Origen": moneda_origen,        # Para saber cual era UF
                        "Descuento": descuento_texto,
                        "Link": link_final
                    }
                    datos_totales.append(item)
            
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"❌ Error en página {pagina}: {e}")

    df = pd.DataFrame(datos_totales)
    df.to_csv(NOMBRE_ARCHIVO, index=False, encoding='utf-8-sig')
    print("✅ ¡Archivo guardado con conversión de UF exitosa!")

if __name__ == "__main__":
    ejecutar_scraper()