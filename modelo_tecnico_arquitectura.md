# 🗺️ Modelo Técnico de Arquitectura: Hardware, Software y Telecomunicaciones

Este documento presenta el modelo técnico integral del **Sistema MAS-CIS**, detallando la infraestructura física (**Hardware**), las tecnologías aplicadas (**Software**) y los canales de comunicación e interconexión (**Telecomunicaciones**).

---

## 📊 Diagrama Técnico de Arquitectura General

El siguiente diagrama gráfico representa la interacción visual de todo el sistema (incluyendo hardware, software y telecomunicaciones):

![Modelo Técnico de Arquitectura (Estilo Bizagi con Fondo Claro)](C:/Users/adria/.gemini/antigravity-ide/brain/130378f6-77bb-4102-a36b-a494923b36dc/bizagi_architecture_local_nlp_1779536944459.png)

### 📊 Diagrama Técnico de Bloques (Código Mermaid)

El siguiente diagrama de bloques representa la interacción entre las diferentes capas físicas y lógicas del sistema:

```mermaid
flowchart TB
    %% Definición de Estilos
    classDef hardware fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#000;
    classDef software fill:#efebe9,stroke:#5d4037,stroke-width:2px,color:#000;
    classDef telecom fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#000;
    classDef cloud fill:#fce4ec,stroke:#c2185b,stroke-width:2px,color:#000;

    subgraph PRESENTACION ["📱 Capa de Cliente / Presentación"]
        HW_Celular["🖥️ Smartphone / Celular<br/>(Hardware)"]:::hardware
        HW_PC["🖥️ PC / Laptop (Admin)<br/>(Hardware)"]:::hardware
        
        SW_WA["💬 WhatsApp App / Web<br/>(Software)"]:::software
        SW_Browser["🌐 Web Browser (Chrome/Firefox)<br/>(Software)"]:::software
        
        HW_Celular --> SW_WA
        HW_PC --> SW_Browser
    end

    subgraph TELECOM_WAN ["🌐 Red de Telecomunicaciones (Internet WAN)"]
        TC_HTTPS["🔒 HTTPS / REST API<br/>(Protocolo)"]:::telecom
        TC_SSL["🔑 SSL / TLS Encryption<br/>(Seguridad)"]:::telecom
        TC_Tunnel["🚇 Túnel Ngrok<br/>(Redirección WAN a LAN)"]:::telecom
        
        TC_HTTPS --- TC_SSL
        TC_SSL --- TC_Tunnel
    end

    subgraph CLOUD_SERVICES ["☁️ Servicios e Integraciones Cloud"]
        TC_Meta["🔗 Meta Cloud API<br/>(WhatsApp Server)"]:::cloud
    end

    subgraph SERVIDOR_LOCAL ["💻 Capa de Servidor Aplicativo (Backend)"]
        HW_Server["🖥️ Servidor Local / VM Cloud<br/>(Hardware: CPU, RAM, Disk)"]:::hardware
        
        subgraph SW_BACKEND ["Entorno de Software (Python 3.10+)"]
            SW_Uvicorn["⚡ ASGI Server: Uvicorn<br/>(Puerto 8000)"]:::software
            SW_FastAPI["🚀 Framework: FastAPI<br/>(Web Endpoints)"]:::software
            SW_MAS["🤖 Capa MAS (Multiagentes)<br/>(Store Agent & Coordinator)"]:::software
            SW_NLU["🧠 Procesador NLP Local<br/>(spaCy model + Regex)"]:::software
            SW_ORM["🛠️ ORM: SQLAlchemy<br/>(Conexión BD)"]:::software
            
            SW_Uvicorn --> SW_FastAPI
            SW_FastAPI --> SW_MAS
            SW_MAS --> SW_NLU
            SW_MAS --> SW_ORM
        end
        
        HW_Server --> SW_BACKEND
    end

    subgraph PERSISTENCIA ["🗄️ Capa de Datos / Persistencia"]
        HW_DB["💾 Almacenamiento SSD / HDD<br/>(Hardware)"]:::hardware
        
        subgraph SW_BD ["Motores de Base de Datos"]
            SW_SQLite["📁 SQLite (Local: mas_cis.db)<br/>(Software)"]:::software
            SW_SQLServer["🗄️ MS SQL Server (Prod)<br/>(Software: Puerto 1433)"]:::software
        end
        
        HW_DB --> SW_BD
    end

    %% Enlaces y Comunicaciones (Telecomunicaciones)
    SW_WA ==>|1. Mensaje Celular / 4G-5G-WiFi| TC_Meta
    TC_Meta ==>|2. Webhook HTTPS POST / Internet| TC_Tunnel
    TC_Tunnel ==>|3. localhost:8000 / Red LAN| SW_Uvicorn
    
    SW_Browser ==>|HTTP Get/Put/Delete / Red LAN| SW_FastAPI
    
    SW_MAS ===>|Procesamiento Local NLU| SW_NLU
    SW_ORM ==>|5. SQLite File IO / TCP 1433| SW_BD
    
    SW_MAS -.->|6. Logs & Notificación| SW_FastAPI
    SW_FastAPI -.->|7. Actualización JSON| SW_Browser

    %% Leyenda rápida
    style PRESENTACION fill:#f1f8e9,stroke:#82b1ff,stroke-width:1px
    style SERVIDOR_LOCAL fill:#fff8e1,stroke:#ffe082,stroke-width:1px
    style PERSISTENCIA fill:#e0f2f1,stroke:#a7ffeb,stroke-width:1px
    style CLOUD_SERVICES fill:#f3e5f5,stroke:#ea80fc,stroke-width:1px
    style TELECOM_WAN fill:#eceff1,stroke:#b0bec5,stroke-width:1px
```

---

## 🛠️ Detalle de los Tres Pilares Tecnológicos

### 1. Hardware (Infraestructura Física)
Representa los equipos físicos donde reside y se procesa el sistema:

- **Dispositivo del Vendedor**: Teléfonos inteligentes (Smartphones) Android o iOS que ejecutan la interfaz de chat (WhatsApp). No requieren potencia de cómputo especial, ya que el procesamiento es delegado al servidor.
- **Dispositivo de Administración (Cliente Web)**: PC de escritorio, laptop o tablets que ejecutan un navegador web para acceder al Dashboard interactivo.
- **Servidor Aplicativo (Hosting)**: 
  - En desarrollo: PC local (Windows OS).
  - En producción: Una Máquina Virtual (VM) en la nube (AWS EC2, Google Compute Engine, Azure VM) con CPU de arquitectura x86_64, memoria RAM (mínimo 2GB para soportar spaCy) y almacenamiento en disco de estado sólido (SSD).
- **Servidor de Base de Datos**: Servidor local o administrado (ej: Azure SQL Database) para alojar las transacciones e inventario.

---

### 2. Software (Capa Lógica y Aplicativa)
Define los programas, librerías y componentes lógicos del sistema:

- **Capa Cliente (Frontend)**:
  - Navegador web interpretando código nativo: **HTML5 semántico**, **CSS3 vanilla** para diseño visual de la interfaz y **JavaScript (ES6+)** para hacer peticiones asíncronas fetch y manejar la renderización de datos.
  - Aplicación propietaria de WhatsApp (Meta).
- **Capa de Aplicación (Backend - Python 3.10+)**:
  - **Uvicorn**: Servidor web con interfaz ASGI de alta velocidad para Python.
  - **FastAPI**: Framework web encargado del enrutamiento de peticiones API y validación de esquemas (Pydantic).
  - **spaCy & Regex (NLU Local)**: Procesamiento de lenguaje natural local en español sin depender de APIs de pago externas, reduciendo costos.
  - **SQLAlchemy ORM**: Mapeador objeto-relacional para interactuar con la base de datos de manera agnóstica al driver.
- **Base de Datos**:
  - **SQLite**: Motor de base de datos relacional ligero contenido en el archivo local `mas_cis.db`.
  - **Microsoft SQL Server**: Motor corporativo usado mediante el driver **pyodbc**.

---

### 3. Telecomunicaciones (Protocolos de Red e Interconectividad)
Describe los medios físicos de transmisión, las redes y los protocolos de comunicación que permiten a los componentes hablar entre sí:

- **Redes Móviles (4G/5G) y WiFi**: Medios de acceso inalámbrico que enlazan el smartphone del vendedor con la red WAN de internet.
- **Meta Cloud Webhooks (HTTPS / Puerto 443)**: Enlace cifrado SSL/TLS por donde Meta envía las notificaciones en formato JSON cada vez que llega un mensaje al número de WhatsApp Business configurado.
- **Túnel de Redirección (Ngrok / HTTPS)**: Software de tunelización que expone el puerto local `8000` (LAN) a una dirección pública segura `HTTPS` (WAN), permitiendo a los servidores externos de Meta enviar webhooks de forma segura a una máquina local en desarrollo.
- **APIs de Integración Cloud (REST / JSON / HTTPS)**:
  - Comunicación del backend hacia los endpoints de Graph API de Meta para enviar los mensajes de confirmación de vuelta al chat del vendedor.
- **Protocolo de Red Local (Localhost Loopback)**: Comunicación por socket TCP interna en el servidor para unir el Servidor Uvicorn (`127.0.0.1:8000`) con el navegador del Administrador o el motor SQL local.
- **Conectividad de Base de Datos**: Puerto `1433` (protocolo TCP/IP corporativo) si se conecta a un servidor remoto de Microsoft SQL Server.
