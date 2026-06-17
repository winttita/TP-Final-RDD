"""
cliente.py — Cliente interactivo para la API de Premios Nobel
Materia: IA3.5 Redes de Datos — TUIA, FCEIA UNR

Este programa es el CLIENTE de la comunicación cliente-servidor: no
almacena ni procesa los datos directamente, solo envía solicitudes HTTP
al servidor (servidor.py) y muestra las respuestas que recibe.

BASE_URL apunta a la IP del host donde corre el servidor. En Etapa 5
(comunicación entre hosts distintos) esta es la única línea que cambió
respecto a la versión que corría todo en localhost — todas las funciones
de abajo usan BASE_URL como variable global, así que el cambio se
propaga automáticamente a todas ellas sin tocar nada más.
"""

import requests
import json
from requests.auth import HTTPBasicAuth

BASE_URL = "http://192.168.100.30:8000"

# HTTPBasicAuth empaqueta usuario y contraseña en el formato que espera
# la autenticación Basic de HTTP (se codifican en Base64 y se mandan en
# el header "Authorization" de la solicitud). Se usa en las funciones que
# llaman a endpoints protegidos (POST, PATCH, DELETE).
AUTH = HTTPBasicAuth("admin", "nobel2024")


def mostrar(response):
    """
    Función auxiliar para imprimir cualquier respuesta del servidor de
    forma legible: muestra el status code HTTP y el cuerpo JSON
    formateado con sangría.

    response.status_code es el código HTTP que el servidor devolvió
    (200, 401, 404, 429, etc.) — es la forma estándar en que el cliente
    sabe qué pasó con la solicitud, sin necesidad de interpretar el
    contenido del mensaje.

    json.dumps(..., indent=2) convierte el dict de Python (ya parseado
    por response.json()) de nuevo a texto, pero con formato legible para
    humanos en la consola.
    """
    print(f"\n{'='*50}")
    print(f"HTTP {response.status_code}")
    print('='*50)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


# ─────────────────────────────────────────────────────────────────
# Funciones de consulta (GET) — no requieren autenticación
# ─────────────────────────────────────────────────────────────────

def premios_por_anio(year):
    """
    Llama a GET /premios/{year}.
    El f-string inserta el valor de "year" directamente en la URL, ya que
    en el servidor este es un parámetro de RUTA.
    """
    r = requests.get(f"{BASE_URL}/premios/{year}")
    mostrar(r)


def premio_especifico(year, category):
    """Llama a GET /premios/{year}/{category}."""
    r = requests.get(f"{BASE_URL}/premios/{year}/{category}")
    mostrar(r)


def buscar_laureado(nombre):
    """
    Llama a GET /laureados/buscar?nombre=...

    NOTA SOBRE EL ARGUMENTO params (usado por primera vez):
    En vez de armar manualmente el string "?nombre=valor" dentro de la
    URL, se le pasa un diccionario al argumento params de requests.get().
    La librería se encarga de construir correctamente el query string,
    incluyendo el "?" y el "=", y de codificar caracteres especiales
    (espacios, tildes, símbolos) si los hubiera. Esto es más seguro que
    concatenar strings a mano.
    """
    r = requests.get(f"{BASE_URL}/laureados/buscar", params={"nombre": nombre})
    mostrar(r)


# ─────────────────────────────────────────────────────────────────
# Funciones de modificación (POST / PATCH / DELETE) — requieren auth
# ─────────────────────────────────────────────────────────────────

def agregar_premio(year, category, laureates=None):
    """
    Llama a POST /premios (endpoint protegido).

    NOTA SOBRE EL ARGUMENTO json= (usado por primera vez):
    requests.post(url, json=payload) hace dos cosas automáticamente:
    1) convierte el diccionario "payload" a texto JSON,
    2) lo coloca en el cuerpo (body) de la solicitud HTTP, y
    3) agrega el header "Content-Type: application/json" para que el
       servidor sepa cómo interpretar ese contenido.
    Sin esto, habría que hacer json.dumps(payload) a mano y setear el
    header manualmente.

    NOTA SOBRE auth=AUTH:
    Le indica a requests que incluya las credenciales de HTTPBasicAuth en
    el header "Authorization" de la solicitud. Si se omitiera, el
    servidor respondería 401 porque este endpoint exige autenticación.

    "laureates or []" es un patrón típico de Python: si "laureates" es
    None (su valor por defecto) o cualquier valor "falsy", se usa una
    lista vacía en su lugar.
    """
    payload = {
        "year": year,
        "category": category,
        "laureates": laureates or [],
    }
    r = requests.post(f"{BASE_URL}/premios", json=payload, auth=AUTH)
    mostrar(r)


def actualizar_motivacion(year, category, laureado_id, nueva_motivacion):
    """
    Llama a PATCH /premios/{year}/{category}/laureado/{laureado_id}
    (endpoint protegido).

    Mismo patrón que agregar_premio: el nuevo texto va en el body como
    JSON, y las credenciales se mandan vía auth=AUTH.
    """
    payload = {"motivation": nueva_motivacion}
    r = requests.patch(
        f"{BASE_URL}/premios/{year}/{category}/laureado/{laureado_id}",
        json=payload,
        auth=AUTH,
    )
    mostrar(r)


def eliminar_premio(year, category):
    """
    Llama a DELETE /premios/{year}/{category} (endpoint protegido).

    A diferencia de POST y PATCH, no se manda ningún body (no hay
    argumento json=): toda la información necesaria para identificar qué
    eliminar ya está en la URL (year, category). Sí se sigue mandando
    auth=AUTH porque el endpoint exige autenticación igual.
    """
    r = requests.delete(f"{BASE_URL}/premios/{year}/{category}", auth=AUTH)
    mostrar(r)


# ─────────────────────────────────────────────────────────────────
# Menú interactivo por consola
# ─────────────────────────────────────────────────────────────────

def main():
    """
    Bucle principal del cliente: muestra un menú de texto, lee la opción
    elegida por el usuario con input(), pide los datos necesarios para
    esa operación, y llama a la función correspondiente de las definidas
    más arriba.

    while True crea un bucle infinito que solo se interrumpe con
    "break" (opción "0"), permitiendo repetir operaciones sin tener que
    reiniciar el programa cada vez.
    """
    while True:
        print("\n--- CLIENTE API NOBEL ---")
        print("1. Premios por año")
        print("2. Premio específico (año + categoría)")
        print("3. Buscar laureado por nombre")
        print("4. Agregar premio")
        print("5. Actualizar motivación")
        print("6. Eliminar premio")
        print("0. Salir")

        opcion = input("Elegí una opción: ")

        if opcion == "1":
            year = input("Año: ")
            premios_por_anio(year)

        elif opcion == "2":
            year = input("Año: ")
            category = input("Categoría: ")
            premio_especifico(year, category)

        elif opcion == "3":
            nombre = input("Laureado: ")
            buscar_laureado(nombre)

        elif opcion == "4":
            # No se pide la lista de laureados acá: el modelo del servidor
            # (NuevoPremio) define "laureates" como opcional, así que se
            # crea el premio sin laureados y se podrían agregar/editar
            # después con el endpoint PATCH.
            year = input("Año: ")
            category = input("Categoría: ")
            agregar_premio(year, category)

        elif opcion == "5":
            year = input("Año: ")
            category = input("Categoría: ")
            id = input("ID del laureado: ")
            motivacion = input("Nueva motivacion: ")
            actualizar_motivacion(year, category, id, motivacion)

        elif opcion == "6":
            year = input("Año: ")
            category = input("Categoría: ")
            eliminar_premio(year, category)

        elif opcion == "0":
            print("\nChau!\n")
            break

        else:
            print("\nOpción inválida")


# Patrón estándar de Python: el bloque de abajo solo se ejecuta cuando
# este archivo se corre directamente (python cliente.py), no cuando se
# importa desde otro script. Así, si en el futuro se quisiera reutilizar
# alguna de las funciones de arriba desde otro archivo, importarlas no
# dispararía accidentalmente el menú interactivo.
if __name__ == "__main__":
    main()