import json
from fastapi import FastAPI

###############################################################################################################################################################################################
# ETAPA 2
###############################################################################################################################################################################################
app = FastAPI()

def cargar_datos():
    """
    Función auxiliar que abre el archivo y devuelve la lista de premios.
    """
    with open("prizes.json", encoding="utf-8") as f:
        return json.load(f)["prizes"]

@app.get("/")
def inicio():
    return {"mensaje": "Servidor Nobel funcionando"}

@app.get("/premios")
def listar_premios():
    prizes = cargar_datos()
    return {"total": len(prizes), "premios": prizes}

# Usamos un parametro de ruta para que parte de la URL sea un valor variable, se indica dentro de {}
@app.get("/premios/{year}")
def premios_por_anio(year: str):
    prizes = cargar_datos()
    resultado = [p for p in prizes if p["year"] == year]
    return {"year": year, "total": len(resultado), "premios": resultado}

# Usamos DOS parametros de ruta, podemos usar los que queramos
@app.get("/premios/{year}/{category}")
def premio_especifico(year: str, category: str):
    prizes = cargar_datos()
    resultado = [
        p for p in prizes
        if p["year"] == year and p["category"].lower() == category.lower()
    ]
    if not resultado:
        return {"error": f"No se encontró el premio de {category} en {year}"}
    return resultado[0]      # Como sabemos que año+categoría es único, devolvemos directamente el primer (y único) elemento en lugar de una lista
