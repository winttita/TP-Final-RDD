"""
servidor.py — API REST de Premios Nobel
Materia: IA3.5 Redes de Datos — TUIA, FCEIA UNR

Este servidor expone los datos de Premios Nobel (almacenados en prizes.json)
a través de una API REST, usando FastAPI como framework y uvicorn como
servidor ASGI que efectivamente abre el puerto y escucha las solicitudes.

FastAPI define QUÉ hace cada endpoint. Uvicorn es quien realmente lo ejecuta:
    python -m uvicorn servidor:app --host 0.0.0.0 --port 8000 --reload
"""

import json
import secrets
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# ─────────────────────────────────────────────────────────────────
# Creación de la app
# ─────────────────────────────────────────────────────────────────
# FastAPI() crea el objeto principal de la aplicación. Todo lo que se
# defina con @app.get, @app.post, etc. se registra dentro de este objeto.
# Uvicorn busca exactamente esta variable ("app") cuando se le indica
# "servidor:app" en la línea de comandos.
app = FastAPI()


# ─────────────────────────────────────────────────────────────────
# Rate limiting (Etapa 4 del TP)
# ─────────────────────────────────────────────────────────────────
# Limiter de slowapi: limita cuántas solicitudes por segundo puede hacer
# un mismo cliente, identificado por su dirección IP (get_remote_address).
# default_limits=["5/second"] aplica esa cota a TODOS los endpoints que
# usen el decorador @limiter.limit más abajo.
limiter = Limiter(key_func=get_remote_address, default_limits=["5/second"])
app.state.limiter = limiter

# Si se supera el límite, slowapi lanza RateLimitExceeded. Este handler le
# dice a FastAPI cómo convertir esa excepción en una respuesta HTTP 429
# (Too Many Requests) automáticamente, sin que cada endpoint tenga que
# manejarlo a mano.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


###############################################################################
# AUTENTICACIÓN (Etapa 4 del TP)
###############################################################################
# HTTPBasic() es el esquema de autenticación "Basic" de HTTP: el cliente
# manda usuario y contraseña codificados en Base64 en el header
# "Authorization". No es encriptación, solo codificación — por eso en
# producción real se usaría siempre sobre HTTPS.
security = HTTPBasic()

# Credenciales válidas (hardcodeadas para este TP académico).
USUARIO_VALIDO = "admin"
CLAVE_VALIDA = "nobel2024"


def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Dependencia de FastAPI que valida usuario y contraseña.

    Depends(security) le dice a FastAPI: "antes de ejecutar el endpoint que
    use esta función, ejecutá primero HTTPBasic() y pasame las credenciales
    que extrajo del header Authorization".

    secrets.compare_digest() compara dos strings en tiempo CONSTANTE, sin
    importar si coinciden o no. Esto evita ataques de timing: si usáramos
    el operador == normal, un atacante podría medir cuántos microsegundos
    tarda la comparación para deducir, carácter por carácter, cuál es la
    contraseña correcta. compare_digest() siempre tarda lo mismo.
    """
    usuario_ok = secrets.compare_digest(credentials.username, USUARIO_VALIDO)
    clave_ok = secrets.compare_digest(credentials.password, CLAVE_VALIDA)
    if not (usuario_ok and clave_ok):
        # raise HTTPException (no return): esto lanza una excepción que
        # FastAPI atrapa y convierte automáticamente en una respuesta HTTP
        # con el status_code indicado. El header WWW-Authenticate es el que
        # le indica al navegador/cliente qué tipo de autenticación se espera.
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )


###############################################################################
# FUNCIONES AUXILIARES DE PERSISTENCIA
###############################################################################
# Estas dos funciones son el único punto de contacto entre el servidor y el
# archivo prizes.json. Todos los endpoints leen/escriben a través de ellas
# en vez de abrir el archivo directamente, para no repetir código.

def cargar_datos() -> list:
    """
    Lee prizes.json y devuelve solamente la lista de premios.

    json.load(f) convierte el contenido del archivo (texto JSON) en
    estructuras nativas de Python: el dict raíz {"prizes": [...]} se
    convierte en un dict de Python, y accedemos a la clave "prizes" para
    quedarnos solo con la lista.
    """
    with open("prizes.json", encoding="utf-8") as f:
        return json.load(f)["prizes"]


def guardar_datos(prizes: list) -> None:
    """
    Escribe la lista de premios de vuelta en prizes.json, sobreescribiendo
    el contenido anterior.

    "w" en open() es el modo ESCRITURA (sin esto, Python no podría
    modificar el archivo, solo leerlo). json.dump(obj, f) hace el camino
    inverso a json.load(): convierte el dict/list de Python en texto JSON
    y lo escribe directamente en el archivo f.

    Envolvemos la lista en {"prizes": prizes} para conservar la misma
    estructura raíz que tenía el archivo original.
    """
    with open("prizes.json", "w", encoding="utf-8") as f:
        json.dump({"prizes": prizes}, f, ensure_ascii=False, indent=2)


###############################################################################
# ENDPOINTS GET — Consultas (no requieren autenticación)
###############################################################################

@app.get("/")
@limiter.limit("5/second")
def inicio(request: Request):
    """
    Endpoint raíz. Sirve para confirmar rápidamente que el servidor está
    arriba y respondiendo.

    NOTA SOBRE EL DECORADOR @app.get("/"):
    El símbolo @ indica un "decorador" — una función que envuelve a otra
    para agregarle comportamiento. @app.get("/") le dice a FastAPI:
    "cuando llegue una solicitud HTTP GET a la ruta '/', ejecutá la función
    de abajo y devolvé lo que retorne, convertido automáticamente a JSON".

    NOTA SOBRE request: Request:
    Es obligatorio para que el decorador @limiter.limit pueda identificar
    de qué IP vino la solicitud y aplicar el conteo de rate limiting.
    """
    return {"mensaje": "Servidor Nobel funcionando"}


@app.get("/premios")
@limiter.limit("5/second")
def listar_premios(request: Request):
    """Devuelve todos los premios almacenados, sin filtrar."""
    prizes = cargar_datos()
    return {"total": len(prizes), "premios": prizes}


@app.get("/premios/{year}")
@limiter.limit("5/second")
def premios_por_anio(year: str, request: Request):
    """
    Devuelve todos los premios otorgados en un año determinado.

    NOTA SOBRE {year} EN LA URL (parámetro de ruta / path parameter):
    Las llaves en la ruta indican un fragmento variable de la URL. FastAPI
    toma automáticamente lo que el cliente puso ahí y lo pasa como
    argumento a la función (year: str). Por ejemplo, una solicitud a
    /premios/2023 ejecuta esta función con year="2023".
    """
    prizes = cargar_datos()
    resultado = [p for p in prizes if p["year"] == year]
    return {"year": year, "total": len(resultado), "premios": resultado}


@app.get("/premios/{year}/{category}")
@limiter.limit("5/second")
def premio_especifico(year: str, category: str, request: Request):
    """
    Devuelve el premio de una categoría puntual en un año puntual
    (por ejemplo: physics, 2023).

    Se pueden usar tantos parámetros de ruta como se necesiten — FastAPI
    los va emparejando con los argumentos de la función por nombre.

    .lower() se aplica a ambos lados de la comparación para que la
    búsqueda sea insensible a mayúsculas/minúsculas (Physics == physics).

    Si no se encuentra nada, se lanza un HTTPException 404 en vez de un
    simple return con un mensaje de error. La diferencia es clave: con
    raise, el status code real de la respuesta HTTP es 404 (Not Found),
    lo cual el cliente puede verificar programáticamente. Si solo
    devolviéramos {"error": "..."} con un return, el status code seguiría
    siendo 200 (éxito), lo que sería semánticamente incorrecto.
    """
    prizes = cargar_datos()
    resultado = [
        p for p in prizes
        if p["year"] == year and p["category"].lower() == category.lower()
    ]
    if not resultado:
        raise HTTPException(status_code=404, detail=f"No se encontró el premio de {category} en {year}")
    return resultado[0]  # año + categoría es único, así que devolvemos el único elemento


@app.get("/laureados/buscar")
@limiter.limit("5/second")
def buscar_laureado(nombre: str, request: Request):
    """
    Busca laureados cuyo nombre o apellido contenga el texto indicado
    (insensible a mayúsculas). Ejemplo: /laureados/buscar?nombre=curie

    NOTA SOBRE nombre: str SIN {nombre} EN LA RUTA (query parameter):
    A diferencia de year y category, "nombre" no aparece entre llaves en
    la URL del decorador (@app.get("/laureados/buscar")). Cuando FastAPI
    ve un parámetro en la función que no está en la ruta, lo trata
    automáticamente como query parameter — se pasa así:
        /laureados/buscar?nombre=curie
    El "?nombre=curie" después del signo de pregunta es el query parameter.

    Recorre cada premio y, dentro de él, cada laureado, comparando el
    nombre completo en minúsculas contra el texto buscado.
    """
    prizes = cargar_datos()
    encontrados = []
    for p in prizes:
        for lau in p.get("laureates", []):
            nombre_completo = f"{lau.get('firstname', '')} {lau.get('surname', '')}".lower()
            if nombre.lower() in nombre_completo:
                encontrados.append({
                    "year": p["year"],
                    "category": p["category"],
                    "laureado": lau,
                })
    if not encontrados:
        raise HTTPException(status_code=404, detail=f"No se encontró ningún laureado con '{nombre}'")
    return {"total": len(encontrados), "resultados": encontrados}


###############################################################################
# ENDPOINT POST — Crear (requiere autenticación)
###############################################################################

class NuevoPremio(BaseModel):
    """
    Modelo Pydantic que define la forma esperada del cuerpo (body) de la
    solicitud POST.

    NOTA SOBRE BaseModel (Pydantic, usado por primera vez):
    Al heredar de BaseModel, FastAPI valida automáticamente que el JSON
    recibido tenga estos campos con estos tipos. Si falta "year" o
    "category", o vienen con un tipo incorrecto, FastAPI responde
    automáticamente con un 422 (Unprocessable Entity) sin que el código
    del endpoint tenga que comprobarlo a mano.

    Optional[list] = [] indica que "laureates" no es obligatorio; si el
    cliente no lo manda, toma el valor por defecto de lista vacía.
    """
    year: str
    category: str
    laureates: Optional[list] = []


@app.post("/premios", status_code=201)
@limiter.limit("5/second")
def agregar_premio(request: Request, nuevo: NuevoPremio, usuario: str = Depends(verificar_credenciales)):
    """
    Agrega un nuevo premio al archivo JSON.

    Requiere autenticación Basic (usuario: admin / contraseña: nobel2024).
    usuario: str = Depends(verificar_credenciales) hace que, antes de
    ejecutar esta función, FastAPI corra primero verificar_credenciales().
    Si las credenciales son inválidas, esa dependencia lanza el 401 y esta
    función ni siquiera llega a ejecutarse.

    status_code=201 (en vez del 200 por defecto): es el código HTTP
    correcto para indicar que un recurso nuevo fue creado exitosamente
    ("201 Created"), a diferencia de un 200 genérico de "todo OK".

    nuevo: NuevoPremio recibe automáticamente el body de la solicitud ya
    validado y convertido a un objeto Python. nuevo.model_dump() lo
    convierte de vuelta a un dict plano de Python, listo para guardarse
    en la lista junto a los demás premios (que también son dicts).

    NOTA SOBRE EL ORDEN DE LOS PARÁMETROS:
    request siempre va primero, después los parámetros de ruta/body, y al
    final los que tienen Depends (porque tienen un valor "por defecto" —
    en Python, un argumento con valor por defecto no puede ir antes de uno
    sin valor por defecto).
    """
    prizes = cargar_datos()
    prizes.append(nuevo.model_dump())
    guardar_datos(prizes)
    return {"mensaje": f"Premio de {nuevo.category} {nuevo.year} agregado.", "premio": nuevo}


###############################################################################
# ENDPOINT DELETE — Eliminar (requiere autenticación)
###############################################################################

@app.delete("/premios/{year}/{category}")
@limiter.limit("5/second")
def eliminar_premio(request: Request, year: str, category: str, usuario: str = Depends(verificar_credenciales)):
    """
    Elimina el premio de una categoría y año específicos.

    Lógica de eliminación con list comprehension: en vez de buscar y
    sacar un elemento puntual, se construye una lista nueva ("nuevos")
    que contiene TODOS los premios que NO coinciden con el año y
    categoría a eliminar. El "not (...)" invierte la condición de
    búsqueda que usamos en otros endpoints.

    Si "nuevos" tiene la misma longitud que "prizes", significa que el
    filtro no descartó ningún elemento — o sea, no existía ese premio —
    y se devuelve 404. Si la longitud cambió, sí se eliminó algo.

    DELETE no recibe body en este caso: toda la información necesaria
    para identificar qué borrar ya viene en la URL (year, category).
    """
    prizes = cargar_datos()

    nuevos = [
        p for p in prizes
        if not (p["year"] == year and p["category"].lower() == category.lower())
    ]

    if len(nuevos) == len(prizes):
        raise HTTPException(status_code=404, detail=f"No se encontró el premio de {category} en {year}")

    guardar_datos(nuevos)
    return {"mensaje": f"Premio de {category} en {year} eliminado correctamente."}


###############################################################################
# ENDPOINT PATCH — Modificar parcialmente (requiere autenticación)
###############################################################################

class ActualizarMotivacion(BaseModel):
    """Modelo Pydantic para el body del PATCH: solo el nuevo texto de motivación."""
    motivation: str


@app.patch("/premios/{year}/{category}/laureado/{laureado_id}")
@limiter.limit("5/second")
def actualizar_motivacion(
    request: Request,
    year: str,
    category: str,
    laureado_id: str,
    datos: ActualizarMotivacion,
    usuario: str = Depends(verificar_credenciales),
):
    """
    Modifica el campo "motivation" de un laureado puntual, identificado
    por año + categoría del premio + id del laureado.

    Búsqueda en dos niveles: primero se recorre la lista de premios
    buscando el que coincide con year y category; una vez encontrado, se
    recorre su lista de laureados buscando el que coincide con
    laureado_id. Al encontrarlo, se modifica directamente el diccionario
    (lau["motivation"] = ...) y se guarda todo de nuevo en el archivo.

    PATCH se usa (en vez de PUT) porque solo se está modificando UNA
    parte del recurso (la motivación), no reemplazándolo por completo.

    Si no se encuentra el laureado dentro del premio, o no se encuentra
    el premio en absoluto, se lanza 404 en cada caso con un mensaje
    específico de qué fue lo que no se encontró.
    """
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