import requests
from bs4 import BeautifulSoup
import time

# URL de ejemplo: Arriendos en la Región de Valparaíso
url = "https://www.yapo.cl/bienes-raices-alquiler-apartamentos/valparaiso-valparaiso"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extraer_datos_yapo():
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lanza error si la página falla
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # En Yapo, cada aviso suele estar en una etiqueta <tr class="ad"> o similar
        # Vamos a buscar los contenedores de los anuncios
        anuncios = soup.find_all('div', class_='d3-ad-tile') # Clase actualizada a 2026

        print(f"--- Se encontraron {len(anuncios)} anuncios ---\n")

        for anuncio in anuncios:
            # Buscamos el título (ajustar si la clase cambia al inspeccionar)
            titulo_el = anuncio.find(class_='d3-ad-tile__title')
            precio_el = anuncio.find(class_='d3-ad-tile__price')
            descuento_el = anuncio.find(class_='d3-ad-tile__price-reduction')
            

            if titulo_el and precio_el:
                if(descuento_el):
                    descuento = descuento_el.text.strip()
                reduccion = precio_el.find(class_="d3-ad-tile__price-reduction")
                if reduccion:
                    reduccion.decompose()
                titulo = titulo_el.text.strip()
                precio = precio_el.text.strip()
                

                print(f"Propiedad: {titulo}")
                print(f"Precio: {precio}")
                if(descuento):
                   print(f"Descuento: {descuento}")
                   descuento = ""
                print("-" * 30)

    except Exception as e:
        print(f"Ocurrió un error: {e}")

if __name__ == "__main__":
    extraer_datos_yapo()