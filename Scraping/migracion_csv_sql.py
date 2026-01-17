import pandas as pd
import sqlite3
import os

# CONFIGURACIÓN
ARCHIVO_CSV = "arriendos_valpo_normalizado.csv"
NOMBRE_DB = "inmobiliaria_chile.db"
NOMBRE_TABLA = "arriendos"

def migrar_datos():
    print("🚀 Iniciando migración de CSV a SQL...")

    # 1. Cargar el CSV limpio
    if not os.path.exists(ARCHIVO_CSV):
        print(f"❌ Error: No encuentro el archivo {ARCHIVO_CSV}")
        return

    df = pd.read_csv(ARCHIVO_CSV)
    print(f"📄 CSV cargado: {len(df)} registros encontrados.")

    # 2. Conectar a la Base de Datos (Se crea sola si no existe)
    conn = sqlite3.connect(NOMBRE_DB)
    cursor = conn.cursor()

    # 3. Crear la Tabla (Diseño Profesional)
    # Usamos IF NOT EXISTS para no romper nada si lo corres dos veces
    schema_sql = f"""
    CREATE TABLE IF NOT EXISTS {NOMBRE_TABLA} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        precio_clp INTEGER,
        precio_original TEXT,
        moneda_origen TEXT,
        descuento TEXT,
        link_web TEXT,
        fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(schema_sql)
    print("✅ Tabla creada (o verificada) exitosamente.")

    # 4. Insertar los datos
    # Pandas tiene una función mágica para esto: .to_sql()
    # if_exists='replace': Borra lo viejo y pone lo nuevo.
    # if_exists='append': Agrega los nuevos al final.
    
    # Seleccionamos y renombramos las columnas para que coincidan con la tabla SQL
    df_sql = df[['Titulo', 'Precio_CLP_Final', 'Precio_Original_Texto', 'Moneda_Origen', 'Descuento', 'Link']].copy()
    df_sql.columns = ['titulo', 'precio_clp', 'precio_original', 'moneda_origen', 'descuento', 'link_web']

    df_sql.to_sql(NOMBRE_TABLA, conn, if_exists='replace', index=False)
    print(f"💾 Se insertaron {len(df)} filas en la base de datos.")

    # 5. PRUEBA DE FUEGO: Una consulta SQL real
    print("\n--- 🔍 CONSULTA SQL: Top 3 Más Baratos ---")
    query = f"""
    SELECT titulo, precio_clp, moneda_origen 
    FROM {NOMBRE_TABLA} 
    WHERE precio_clp > 50000 -- Filtramos errores de precio cero
    ORDER BY precio_clp ASC 
    LIMIT 3;
    """
    
    for row in cursor.execute(query):
        print(f"💰 ${row[1]:,} ({row[2]}) - {row[0][:40]}...")

    conn.close()
    print("\n🎉 ¡PROYECTO COMPLETADO! Tu base de datos está lista.")

if __name__ == "__main__":
    migrar_datos()