import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends
import secrets
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

app = FastAPI()

limiter = Limiter(key_func=get_remote_address, default_limits=["5/second"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

###############################################################################################################################################################################################
# AUTENTICACION
###############################################################################################################################################################################################
security = HTTPBasic()

USUARIO_VALIDO = "admin"
CLAVE_VALIDA   = "nobel2024"

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    usuario_ok = secrets.compare_digest(credentials.username, USUARIO_VALIDO)
    clave_ok   = secrets.compare_digest(credentials.password, CLAVE_VALIDA)
    if not (usuario_ok and clave_ok):
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )

###############################################################################################################################################################################################
# GET endpoints
###############################################################################################################################################################################################
def cargar_datos():
    """
    Función auxiliar que abre el archivo y devuelve la lista de premios.
    """
    with open("prizes.json", encoding="utf-8") as f:
        return json.load(f)["prizes"]
    
def guardar_datos(prizes: list):
    """
    Función auxiliar que abre y escribe datos sobre el archivo.
    """
    with open("prizes.json", "w", encoding="utf-8") as f:
        json.dump({"prizes": prizes}, f, ensure_ascii=False, indent=2)

@app.get("/")
@limiter.limit("5/second")
def inicio(request: Request):
    return {"mensaje": "Servidor Nobel funcionando"}

@app.get("/premios")
@limiter.limit("5/second")
def listar_premios(request: Request):
    prizes = cargar_datos()
    return {"total": len(prizes), "premios": prizes}

# Usamos un parametro de ruta para que parte de la URL sea un valor variable, se indica dentro de {}
@app.get("/premios/{year}")
@limiter.limit("5/second")
def premios_por_anio(year: str, request: Request):
    prizes = cargar_datos()
    resultado = [p for p in prizes if p["year"] == year]
    return {"year": year, "total": len(resultado), "premios": resultado}

# Usamos DOS parametros de ruta, podemos usar los que queramos
@app.get("/premios/{year}/{category}")
@limiter.limit("5/second")
def premio_especifico(year: str, category: str, request: Request):
    prizes = cargar_datos()
    resultado = [
        p for p in prizes
        if p["year"] == year and p["category"].lower() == category.lower()
    ]
    if not resultado:
        raise HTTPException(status_code=404, detail=f"No se encontró el premio de {category} en {year}")
    return resultado[0]      # Como sabemos que año+categoría es único, devolvemos directamente el primer (y único) elemento en lugar de una lista

# Aqui vamos a usar un parametro de query
@app.get("/laureados/buscar")
@limiter.limit("5/second")
def buscar_laureado(nombre: str, request: Request):
    prizes = cargar_datos()
    encontrados = []
    for p in prizes:
        for lau in p.get("laureates", []):
            nombre_completo = f"{lau.get('firstname', '')} {lau.get('surname', '')}".lower()
            if nombre.lower() in nombre_completo:
                encontrados.append({
                    "year": p["year"],
                    "category": p["category"],
                    "laureado": lau
                })
    if not encontrados:
        raise HTTPException(status_code=404, detail=f"No se encontró ningún laureado con '{nombre}'")
    return {"total": len(encontrados), "resultados": encontrados}

###############################################################################################################################################################################################
# POST endpoints
###############################################################################################################################################################################################
class NuevoPremio(BaseModel):
    year: str
    category: str
    laureates: Optional[list] = []

@app.post("/premios", status_code=201)
@limiter.limit("5/second")
def agregar_premio(request: Request, nuevo: NuevoPremio, usuario: str = Depends(verificar_credenciales)):
    prizes = cargar_datos()
    prizes.append(nuevo.model_dump())
    guardar_datos(prizes)
    return {"mensaje": f"Premio de {nuevo.category} {nuevo.year} agregado.", "premio": nuevo}

###############################################################################################################################################################################################
# DELETE endpoints
###############################################################################################################################################################################################
@app.delete("/premios/{year}/{category}")
@limiter.limit("5/second")
def eliminar_premio(request: Request, year: str, category: str, usuario: str = Depends(verificar_credenciales)):
    prizes = cargar_datos()
    
    nuevos = [
        p for p in prizes
        if not (p["year"] == year and p["category"].lower() == category.lower())
    ]
    
    if len(nuevos) == len(prizes):
        raise HTTPException(status_code=404, detail=f"No se encontró el premio de {category} en {year}")
    
    guardar_datos(nuevos)
    return {"mensaje": f"Premio de {category} en {year} eliminado correctamente."}

###############################################################################################################################################################################################
# PATCH endpoints
###############################################################################################################################################################################################
class ActualizarMotivacion(BaseModel):
    motivation: str

@app.patch("/premios/{year}/{category}/laureado/{laureado_id}")
@limiter.limit("5/second")
def actualizar_motivacion(request: Request, year: str, category: str, laureado_id: str, datos: ActualizarMotivacion, usuario: str = Depends(verificar_credenciales)):
    prizes = cargar_datos()
    
    for p in prizes:
        if p["year"] == year and p["category"].lower() == category.lower():
            for lau in p.get("laureates", []):
                if lau["id"] == laureado_id:
                    lau["motivation"] = datos.motivation
                    guardar_datos(prizes)
                    return {"mensaje": "Motivación actualizada.", "laureado": lau}
            raise HTTPException(status_code=404, detail=f"Laureado {laureado_id} no encontrado.")
    
    raise HTTPException(status_code=404, detail=f"Premio {category} {year} no encontrado.")