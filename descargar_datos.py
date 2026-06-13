import requests
import json


###############################################################################################################################################################################################
# ETAPA 1
###############################################################################################################################################################################################

url = "https://api.nobelprize.org/v1/prize.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

respuesta = requests.get(url, headers=headers)

print("\n",respuesta.status_code)
print("\n",respuesta.text[:500])   # solo los primeros 500 caracteres para no inundar la consola

datos = respuesta.json()

print("\n", type(datos))           # ¿qué tipo de dato es?
print("\n", datos.keys())          # ¿qué claves tiene?

prizes = datos["prizes"]

print(f"\nTotal de premios: {len(prizes)}")   # Cantidad de premios
print()

primero = prizes[0]

laureates = primero["laureates"]
print(type(laureates))           # ¿lista o dict?
print(f"\nCantidad de laureados: {len(laureates)}")
print()

# Miramos el primer laureado
print("\nClaves de un laureado:", laureates[0].keys())
print()
print("\nLaureado completo:")
print(json.dumps(laureates[0], indent=2, ensure_ascii=False))

sin_laureados = [p for p in prizes if not p.get("laureates")]
print(f"\nPremios sin laureados: {len(sin_laureados)}")
print(json.dumps(sin_laureados[2], indent=2, ensure_ascii=False))

with open("prizes.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)

print("Archivo guardado correctamente")

###############################################################################################################################################################################################