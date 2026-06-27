# TP Final — Comunicación API Cliente-Servidor
### IA3.5 Redes de Datos · TUIA · FCEIA UNR

API REST para consultar y modificar la base de datos de **Premios Nobel**, implementada con FastAPI y consumida por un cliente interactivo por consola.

---

## Descripción

El proyecto implementa una comunicación cliente-servidor real entre dos hosts en red local. El servidor expone los datos del archivo `prizes.json` (descargado de la API oficial de Nobel) a través de endpoints REST. El cliente permite interactuar con esos datos desde otra máquina mediante un menú por consola.

Cubre las cinco etapas del TP:
- **Etapa 1** — Descarga y exploración del dataset JSON
- **Etapa 2** — Servidor API con FastAPI y uvicorn
- **Etapa 3** — Cliente interactivo con requests
- **Etapa 4** — Autenticación HTTP Basic y rate limiting
- **Etapa 5** — Comunicación entre dos hosts en LAN

---

## Estructura del proyecto

```
TP-Final-RDD/
├── descargar_datos.py   # Descarga el JSON de Nobel y lo guarda localmente
├── servidor.py          # API REST (FastAPI + uvicorn)
├── cliente.py           # Cliente interactivo por consola
├── prizes.json          # Dataset de Premios Nobel (generado por descargar_datos.py)
├── requirements.txt     # Dependencias del proyecto
└── README.md
```

---

## Dataset

**Fuente:** [Nobel Prize API](https://api.nobelprize.org/v1/prize.json)

| Campo | Descripción |
|---|---|
| 682 premios | Desde 1901 hasta 2025 |
| 6 categorías | physics, chemistry, medicine, literature, peace, economics |
| 49 sin laureados | Años en que el premio fue declarado desierto |

Cada premio tiene: `year`, `category`, `overallMotivation` y una lista de `laureates` con `id`, `firstname`, `surname`, `motivation` y `share`.

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/winttita/TP-Final-RDD.git
cd TP-Final-RDD

# Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Descargar el dataset (solo la primera vez)
python descargar_datos.py
```

---

## Uso

### Servidor

```bash
# Desarrollo (solo localhost)
python -m uvicorn servidor:app --reload

# Producción / Etapa 5 (acepta conexiones desde la red)
python -m uvicorn servidor:app --host 0.0.0.0 --port 8000
```

La documentación interactiva de la API queda disponible en:
- `http://localhost:8000/docs` → Swagger UI
- `http://localhost:8000/redoc` → ReDoc

### Cliente

```bash
python cliente.py
```

Para conectarse a un servidor remoto, modificar `BASE_URL` en `cliente.py`:
```python
BASE_URL = "http://192.168.100.30:8000"
```

---

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/` | No | Info general del servidor |
| GET | `/premios` | No | Lista todos los premios |
| GET | `/premios/{year}` | No | Premios de un año |
| GET | `/premios/{year}/{category}` | No | Premio específico |
| GET | `/laureados/buscar?nombre=...` | No | Buscar por nombre/apellido |
| POST | `/premios` | Sí | Agregar un nuevo premio |
| PATCH | `/premios/{year}/{category}/laureado/{id}` | Sí | Modificar motivación |
| DELETE | `/premios/{year}/{category}` | Sí | Eliminar un premio |

**Credenciales para endpoints protegidos:**
```
Usuario: admin
Contraseña: nobel2024
```

---

## Seguridad

- **Autenticación HTTP Basic** en todos los métodos que modifican datos (POST, PATCH, DELETE). Comparación de credenciales con `secrets.compare_digest()` para prevenir ataques de timing.
- **Rate limiting** de 5 solicitudes/segundo por IP implementado con `slowapi`. Superar el límite devuelve HTTP 429.

---

## Dependencias

```
fastapi
uvicorn
slowapi
requests
pydantic
```

---

## Tecnologías

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![uvicorn](https://img.shields.io/badge/uvicorn-ASGI-499848)

---

## Autores

FRANK, Maximiliano · WINTER, Federico
Tecnicatura Universitaria en Inteligencia Artificial — FCEIA, UNR · 2026
