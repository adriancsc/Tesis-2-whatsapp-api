# 📋 Resumen del Proyecto MAS-CIS

Este archivo sirve como una guía de referencia rápida para comprender la estructura, el funcionamiento y cómo ejecutar el **Sistema Multiagente de Sincronización de Inventario (MAS-CIS)**.

---

## 🎯 ¿Qué es el Sistema MAS-CIS?

Es un prototipo de tesis diseñado para sincronizar en tiempo real el inventario físico de tiendas minoristas (ej. Gamarra) y su tienda en línea (E-commerce). Permite a los vendedores registrar transacciones (ventas, adición de stock, consultas) directamente a través de **WhatsApp** usando un **menú interactivo numérico** gestionado por un sistema basado en grafos de estado FSM (LangGraph).

---

## 📂 Estructura General del Directorio

```text
Prototipo Tesis 1/
│
├── frontend/                     # Interfaz web de usuario (HTML/CSS/JS)
│   ├── css/                      # Hojas de estilo (styles.css, store.css, etc.)
│   ├── js/                       # Lógica JS (app.js, store.js, product-detail.js)
│   ├── index.html                # Dashboard del Administrador
│   ├── store.html                # Catálogo público de la tienda
│   └── product-detail.html       # Detalle de variante de producto
│
├── src/                          # Código fuente del Backend (Python)
│   ├── agents/                   # Sistema de Agentes Autónomos (LangGraph)
│   │   ├── inventory_graph.py    # Grafo principal de agentes y lógica FSM
│   │   ├── conversation_state.py # Puente de memoria para current_step
│   │   └── dtos.py               # Data Transfer Objects (VariantDTO, ProductDTO)
│   │
│   ├── api/                      # Endpoints REST y Webhooks (FastAPI)
│   │   ├── main.py               # Enrutamiento, API Endpoints y Webhooks de WhatsApp
│   │   └── schemas.py            # Esquemas de datos para request/response (Pydantic)
│   │
│   ├── config/                   # Configuración del Sistema
│   │   └── settings.py           # Configuración con Pydantic Settings
│   │
│   ├── database/                 # Persistencia y ORM (SQLAlchemy)
│   │   ├── connection.py         # Conexión y context managers de base de datos
│   │   ├── models.py             # Definición de tablas y relaciones de SQLAlchemy
│   │   ├── repository.py         # Patrón repositorio para desacoplar ORM de los agentes
│   │   └── recreate_db_with_variants.py # Script para resetear y sembrar la base de datos
│   │
│   ├── gateway/                  # Puentes con APIs Externas
│   │   ├── whatsapp_gateway.py   # Conectividad con la API Cloud de WhatsApp (Meta)
│   │   └── message_router.py     # Router de mensajería entre Gateway y Agentes
│   │
│   └── utils/                    # Funciones y clases de soporte
│       ├── logger.py             # Registrador de eventos centralizado
│       └── validators.py         # Validadores de reglas de negocio
│
├── docs/                         # Documentación detallada de arquitectura y diagramas
├── .env                          # Variables de entorno locales
├── install.ps1                   # Script de instalación para Windows (PowerShell)
├── start.ps1                     # Script de inicio rápido (PowerShell)
├── main.py                       # Punto de entrada principal (ejecuta Uvicorn)
├── requirements.txt              # Dependencias del proyecto Python
└── mas_cis.db                    # Base de datos SQLite local para desarrollo
```

---

## ⚙️ Funcionamiento Principal

El flujo interactivo opera de la siguiente manera:
1. **Entrada de Usuario**: Un vendedor envía un número por WhatsApp (ej: *"1"* para seleccionar una opción de menú).
2. **Recepción & Ruteo**: 
   - El webhook de FastAPI (`/webhooks/whatsapp`) recibe el evento JSON.
   - El [whatsapp_gateway.py](file:///c:/Prototipo%20Tesis%201/src/gateway/whatsapp_gateway.py) extrae el número de teléfono y texto.
   - El [message_router.py](file:///c:/Prototipo%20Tesis%201/src/gateway/message_router.py) recupera el `current_step` de memoria y delega al grafo LangGraph.
3. **Navegación FSM (Store Node)**:
   - El `store_node` avanza la máquina de estados según el input del usuario (MAIN_MENU -> SELECT_PRODUCT -> SELECT_SIZE -> ...).
   - Acumula los datos (SKU de producto, talla, cantidad) en el `AgentState`.
4. **Validación y Ejecución (Coordinator Node)**:
   - Al confirmar, el `coordinator_node` localiza la variante del producto por SKU y talla.
   - Se valida el inventario físico disponible atómicamente.
   - Si es válido, se efectúa la transacción restando el stock, y se registra en `transactions` y `agent_logs`.
5. **Respuesta**:
   - LangGraph retorna el estado final.
   - El Gateway envía el mensaje de respuesta de vuelta al vendedor por WhatsApp.
   - El **Dashboard Web** (Frontend) se puede refrescar reflejando el nuevo stock.

---

## 🚀 Cómo Ejecutar el Proyecto

Sigue estos pasos para levantar el entorno de desarrollo local en Windows:

### Paso 1: Clonar e Instalar Dependencias
Abre una terminal de PowerShell en la raíz del proyecto y ejecuta:
```powershell
.\install.ps1
```
Este script:
- Verificará que tengas Python 3.10+.
- Instalará todas las librerías en `requirements.txt` (incluyendo LangGraph).
- Creará un archivo `.env` a partir de `.env.example`.

### Paso 2: Inicializar la Base de Datos
El proyecto viene preconfigurado para usar **SQLite** localmente (archivo `mas_cis.db`). Si deseas usar SQLite, no necesitas configurar nada más. Para poblar la base de datos con productos iniciales (polos, pantalones, camisas y accesorios con stock de prueba), ejecuta:
```powershell
python src/database/recreate_db_with_variants.py
```
*(Ingresa `s` cuando el script solicite confirmación para continuar).*

### Paso 3: Configurar las Credenciales (.env)
Abre el archivo [`.env`](file:///c:/Prototipo%20Tesis%201/.env) en el editor. Las variables principales son:
- `WHATSAPP_API_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`: Credenciales para conectar el webhook con Meta Developer Console.
- `DB_DRIVER`: Establecido en `sqlite` por defecto. Si decides usar Microsoft SQL Server, cambia la configuración a:
  ```ini
  DB_DRIVER=ODBC Driver 17 for SQL Server
  DB_SERVER=localhost
  DB_NAME=MAS_CIS_DB
  DB_TRUSTED_CONNECTION=True
  ```

### Paso 4: Iniciar el Servidor
Puedes iniciar el proyecto con el comando:
```powershell
.\start.ps1
```
o ejecutando directamente:
```bash
python main.py
```

El servidor FastAPI arrancará en: **`http://localhost:8000`**

### Paso 5: Probar las Interfaces
- **Administrador (Dashboard)**: [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)
- **Catálogo Web (Tienda)**: [http://localhost:8000/store](http://localhost:8000/store)
- **Documentación interactiva de la API**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Paso 6: Integración con WhatsApp (Webhook en Producción Local)
Como Meta requiere un endpoint seguro (`https`), debes exponer tu servidor local mediante un túnel:
1. Ejecuta ngrok en el puerto 8000:
   ```bash
   ngrok http 8000
   ```
2. Copia la URL HTTPS que provee ngrok (ej: `https://abcd-123.ngrok-free.app`).
3. En el panel de control de WhatsApp Business (Meta Developer):
   - Configura la URL del webhook como: `https://abcd-123.ngrok-free.app/webhooks/whatsapp`.
   - Token de verificación: `mas_cis_secret_token_2025` (o el que hayas configurado en `WHATSAPP_VERIFY_TOKEN` dentro de `.env`).
4. ¡Listo! Puedes enviar mensajes al número de prueba de WhatsApp y ver la actualización en el dashboard.
