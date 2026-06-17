import requests
import json
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8000"
AUTH = HTTPBasicAuth("admin", "nobel2024")

def mostrar(response):
    print(f"\n{'='*50}")
    print(f"HTTP {response.status_code}")
    print('='*50)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def premios_por_anio(year):
    r = requests.get(f"{BASE_URL}/premios/{year}")
    mostrar(r)

def premio_especifico(year, category):
    r = requests.get(f"{BASE_URL}/premios/{year}/{category}")
    mostrar(r)

def buscar_laureado(nombre):
    r = requests.get(f"{BASE_URL}/laureados/buscar", params={"nombre": nombre})
    mostrar(r)

def agregar_premio(year, category, laureates=None):
    payload = {
        "year": year,
        "category": category,
        "laureates": laureates or []
    }
    r = requests.post(f"{BASE_URL}/premios", json=payload, auth=AUTH)
    mostrar(r)

def actualizar_motivacion(year, category, laureado_id, nueva_motivacion):
    payload = {"motivation": nueva_motivacion}
    r = requests.patch(
        f"{BASE_URL}/premios/{year}/{category}/laureado/{laureado_id}",
        json=payload,
        auth=AUTH
    )
    mostrar(r)

def eliminar_premio(year, category):
    r = requests.delete(f"{BASE_URL}/premios/{year}/{category}", auth=AUTH)
    mostrar(r)

def main():
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

        elif opcion == "0":
            print("Chau!")
            break

        else:
            print("Opción inválida")