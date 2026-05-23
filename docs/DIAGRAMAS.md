# 📊 Diagramas de Diseño - Sistema MAS-CIS

## Documentación Visual para Revisión de Asesor de Tesis

---

## 1. Diagrama de Arquitectura General

![Arquitectura General del Sistema MAS-CIS](C:/Users/adria/.gemini/antigravity/brain/dec6a524-04a5-428a-9856-ab0e16c3e196/mas_cis_architecture_diagram_1764201718593.png)

### Descripción

Este diagrama muestra la arquitectura completa del Sistema MAS-CIS con sus tres capas principales:

**Capa de Usuario:**
- Vendedor emergente interactuando vía WhatsApp

**Capa de Agentes (MAS):**
- Gateway de Comunicación (WhatsApp Business API)
- Agente de Tienda con procesamiento NLU
- Agente Coordinador para sincronización

**Capa de Datos:**
- Base de datos SQL Server
- Integración con plataforma de E-commerce

---

## 2. Diagrama de Componentes Detallado

```mermaid
graph TB
    subgraph "CAPA DE PRESENTACIÓN"
        V[👤 Vendedor Emergente<br/>Gamarra, Perú]
        D[💻 Dashboard Admin<br/>Monitoreo Web]
    end
    
    subgraph "CAPA DE COMUNICACIÓN"
        WA[📱 WhatsApp Business<br/>Meta Cloud API]
        GW[🌐 Gateway de Comunicación<br/>Webhook Handler]
        API[🔌 API REST<br/>FastAPI]
    end
    
    subgraph "CAPA DE AGENTES - SISTEMA MULTIAGENTE"
        direction TB
        SA[🏪 Agente de Tienda<br/>Store Agent<br/>─────────<br/>• Recepción de mensajes<br/>• Procesamiento NLU<br/>• Gestión de sesiones<br/>• Validación de comandos]
        
        NLU[🧠 Procesador NLU<br/>spaCy + Regex<br/>─────────<br/>• Extracción de intención<br/>• Extracción de entidades<br/>• Cálculo de confianza<br/>• Parsing en español]
        
        CA[🔄 Agente Coordinador<br/>Coordinator Agent<br/>─────────<br/>• Validación de stock<br/>• Actualización de BD<br/>• Registro de transacciones<br/>• Sincronización]
        
        MR[📨 Message Router<br/>Enrutador<br/>─────────<br/>• Coordinación de agentes<br/>• Gestión de flujo<br/>• Manejo de respuestas]
    end
    
    subgraph "CAPA DE DATOS"
        DB[(💾 Base de Datos<br/>SQL Server<br/>─────────<br/>• Products<br/>• Transactions<br/>• Chat Sessions<br/>• Agent Logs)]
        
        CACHE[⚡ Cache/Sesiones<br/>Redis opcional<br/>─────────<br/>• Sesiones activas<br/>• Contexto temporal]
    end
    
    subgraph "CAPA DE INTEGRACIÓN"
        EC[🛒 Plataforma E-commerce<br/>Tienda Online<br/>─────────<br/>• Consulta de stock<br/>• Actualización automática<br/>• API REST]
    end
    
    %% Flujo principal
    V -->|"1. Mensaje de texto"| WA
    WA -->|"2. Webhook POST"| GW
    GW -->|"3. JSON"| MR
    MR -->|"4. Mensaje"| SA
    SA -->|"5. Parse"| NLU
    NLU -->|"6. Comando"| SA
    SA -->|"7. Solicitud"| MR
    MR -->|"8. Operación"| CA
    CA -->|"9. Query/Update"| DB
    DB -->|"10. Resultado"| CA
    CA -->|"11. Respuesta"| MR
    MR -->|"12. Mensaje"| SA
    SA -->|"13. Respuesta"| GW
    GW -->|"14. API Call"| WA
    WA -->|"15. Mensaje"| V
    
    %% Dashboard
    D -->|"HTTP Request"| API
    API -->|"SQL Query"| DB
    DB -->|"Data"| API
    API -->|"JSON Response"| D
    
    %% E-commerce
    CA -->|"Sync Event"| EC
    EC -->|"Stock Query"| API
    API -->|"Current Stock"| EC
    
    %% Cache
    SA -.->|"Sesiones"| CACHE
    
    %% Estilos
    style V fill:#e0e7ff,stroke:#6366f1,stroke-width:2px
    style D fill:#e0e7ff,stroke:#6366f1,stroke-width:2px
    
    style WA fill:#fff7ed,stroke:#f59e0b,stroke-width:2px
    style GW fill:#fff7ed,stroke:#f59e0b,stroke-width:2px
    style API fill:#fff7ed,stroke:#f59e0b,stroke-width:2px
    
    style SA fill:#ddd6fe,stroke:#8b5cf6,stroke-width:3px
    style NLU fill:#fce7f3,stroke:#ec4899,stroke-width:3px
    style CA fill:#ddd6fe,stroke:#7c3aed,stroke-width:3px
    style MR fill:#ddd6fe,stroke:#8b5cf6,stroke-width:2px
    
    style DB fill:#d1fae5,stroke:#10b981,stroke-width:2px
    style CACHE fill:#dbeafe,stroke:#3b82f6,stroke-width:2px
    
    style EC fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
```

### Leyenda de Componentes

| Símbolo | Componente | Descripción |
|---------|-----------|-------------|
| 👤 | Vendedor | Usuario final del sistema |
| 📱 | WhatsApp | Canal de comunicación |
| 🌐 | Gateway | Punto de entrada de mensajes |
| 🏪 | Store Agent | Agente de interfaz con usuario |
| 🧠 | NLU | Procesamiento de lenguaje natural |
| 🔄 | Coordinator | Agente de sincronización |
| 💾 | Database | Almacenamiento persistente |
| 🛒 | E-commerce | Plataforma de venta online |

---

## 3. Diagrama de Secuencia - Flujo de Venta

```mermaid
sequenceDiagram
    autonumber
    actor V as 👤 Vendedor
    participant WA as 📱 WhatsApp
    participant GW as 🌐 Gateway
    participant SA as 🏪 Store Agent
    participant NLU as 🧠 NLU Processor
    participant CA as 🔄 Coordinator
    participant DB as 💾 SQL Server
    participant EC as 🛒 E-commerce
    
    Note over V,EC: Caso de Uso: Registrar Venta de Producto
    
    V->>WA: "Vendí 3 polos rojos talla M"
    activate WA
    WA->>GW: POST /webhooks/whatsapp
    activate GW
    
    GW->>GW: Parsear webhook
    GW->>WA: Marcar como leído ✓
    deactivate WA
    
    GW->>SA: Mensaje parseado
    activate SA
    
    SA->>NLU: parse("Vendí 3 polos rojos talla M")
    activate NLU
    NLU->>NLU: Extraer acción: "sell"
    NLU->>NLU: Extraer cantidad: 3
    NLU->>NLU: Extraer producto: "polo rojo"
    NLU->>NLU: Extraer atributos: {talla: "M", color: "rojo"}
    NLU->>NLU: Calcular confianza: 0.85
    NLU->>SA: ParsedCommand{action: sell, qty: 3, ...}
    deactivate NLU
    
    SA->>DB: SELECT * FROM products WHERE...
    activate DB
    DB->>SA: Product{sku: "POLO-R-M", stock: 15}
    deactivate DB
    
    SA->>CA: {action: "sell", sku: "POLO-R-M", qty: 3}
    activate CA
    
    CA->>CA: Validar operación
    Note over CA: ✓ Stock suficiente (15 >= 3)
    
    CA->>DB: BEGIN TRANSACTION
    activate DB
    CA->>DB: UPDATE products SET stock_physical = 12
    CA->>DB: INSERT INTO transactions (...)
    CA->>DB: COMMIT
    DB->>CA: Operación exitosa
    deactivate DB
    
    CA->>EC: Notificar cambio de stock
    activate EC
    EC->>EC: Actualizar catálogo
    EC->>CA: ACK
    deactivate EC
    
    CA->>SA: {success: true, new_stock: 12}
    deactivate CA
    
    SA->>GW: "✅ Venta registrada. Stock: 12"
    deactivate SA
    
    GW->>WA: send_message(...)
    activate WA
    WA->>V: "✅ Venta registrada..."
    deactivate WA
    deactivate GW
    
    Note over V,EC: Tiempo total: ~500-800ms
```

---

## 4. Diagrama de Estados - Procesamiento de Mensaje

```mermaid
stateDiagram-v2
    [*] --> Recibido: Webhook de WhatsApp
    
    Recibido --> Parseando: Gateway procesa
    
    Parseando --> Validando_NLU: NLU extrae datos
    
    Validando_NLU --> Comando_Válido: Confianza >= 0.7
    Validando_NLU --> Comando_Inválido: Confianza < 0.7
    
    Comando_Inválido --> Solicitando_Clarificación: Pedir más info
    Solicitando_Clarificación --> [*]: Respuesta enviada
    
    Comando_Válido --> Buscando_Producto: Store Agent busca
    
    Buscando_Producto --> Producto_Encontrado: Existe en DB
    Buscando_Producto --> Producto_No_Encontrado: No existe
    
    Producto_No_Encontrado --> Error_Producto: Notificar
    Error_Producto --> [*]: Respuesta enviada
    
    Producto_Encontrado --> Validando_Negocio: Coordinator valida
    
    Validando_Negocio --> Validación_OK: Reglas cumplidas
    Validando_Negocio --> Validación_Falla: Stock insuficiente, etc.
    
    Validación_Falla --> Error_Validación: Notificar error
    Error_Validación --> [*]: Respuesta enviada
    
    Validación_OK --> Ejecutando_Transacción: UPDATE DB
    
    Ejecutando_Transacción --> Transacción_Exitosa: COMMIT
    Ejecutando_Transacción --> Transacción_Fallida: ROLLBACK
    
    Transacción_Fallida --> Error_DB: Notificar error
    Error_DB --> [*]: Respuesta enviada
    
    Transacción_Exitosa --> Sincronizando: Notificar E-commerce
    
    Sincronizando --> Completado: Sync OK
    
    Completado --> [*]: Confirmación enviada
    
    note right of Validando_NLU
        Umbral de confianza: 0.7
        Extrae: acción, cantidad,
        producto, atributos
    end note
    
    note right of Validando_Negocio
        Verifica:
        - Stock suficiente
        - Cantidad válida
        - Producto activo
    end note
```

---

## 5. Diagrama de Clases - Agentes

```mermaid
classDiagram
    class BaseAgent {
        <<abstract>>
        +string agent_id
        +string agent_type
        +AgentStatus status
        +datetime created_at
        +datetime last_activity
        +Logger logger
        +process_message(message)* Dict
        +update_status(status) void
        +log_activity(action, metadata) void
        +handle_error(error, context) void
        +get_info() Dict
    }
    
    class StoreAgent {
        +Dict~string,ChatSession~ sessions
        +process_message(message) Dict
        -_handle_inventory_operation(parsed, phone, session) Dict
        -_handle_query(parsed, phone) Dict
        -_handle_unclear_command(parsed, phone) Dict
        -_find_product(parsed) Product
        -_get_or_create_session(phone) ChatSession
        -_create_response(to, text) Dict
    }
    
    class CoordinatorAgent {
        +InventoryValidator validator
        +process_message(message) Dict
        -_process_sale(sku, qty, phone) Dict
        -_process_addition(sku, qty, phone) Dict
        -_process_update(sku, qty, phone) Dict
        -_process_removal(sku, qty, phone) Dict
        -_log_operation(action, sku, result) void
    }
    
    class NLUProcessor {
        +spacy.Language nlp
        +Dict ACTION_PATTERNS
        +List QUANTITY_PATTERNS
        +List COLORS
        +List SIZES
        +parse(text) ParsedCommand
        -_extract_action(text) string
        -_extract_quantity(text) int
        -_extract_sku(text) string
        -_extract_product_name(text, sku) string
        -_extract_attributes(text) Dict
        -_calculate_confidence(...) float
        +is_valid_command(parsed, threshold) bool
    }
    
    class ParsedCommand {
        +string action
        +int quantity
        +string product_name
        +string product_sku
        +Dict attributes
        +float confidence
        +string raw_text
    }
    
    class WhatsAppGateway {
        +string api_url
        +string phone_number_id
        +string access_token
        +Dict headers
        +send_message(to, message) Dict
        +send_template_message(to, template) Dict
        +mark_as_read(message_id) bool
        +parse_webhook_message(webhook_data) Dict
        +verify_webhook(mode, token, challenge) string
    }
    
    BaseAgent <|-- StoreAgent : extends
    BaseAgent <|-- CoordinatorAgent : extends
    StoreAgent --> NLUProcessor : uses
    StoreAgent --> WhatsAppGateway : uses
    NLUProcessor --> ParsedCommand : creates
    StoreAgent --> CoordinatorAgent : delegates to
```

---

## 6. Diagrama de Despliegue

```mermaid
graph TB
    subgraph "CLOUD - Meta Platform"
        WA_CLOUD[WhatsApp Business<br/>Cloud API<br/>Meta Servers]
    end
    
    subgraph "SERVIDOR DE APLICACIÓN"
        subgraph "Contenedor Python"
            FASTAPI[FastAPI Server<br/>Uvicorn<br/>:8000]
            AGENTS[Sistema de Agentes<br/>Store + Coordinator]
            NLU_SVC[Servicio NLU<br/>spaCy]
        end
        
        subgraph "Servidor Web"
            NGINX[Nginx<br/>Reverse Proxy<br/>:80/:443]
            STATIC[Archivos Estáticos<br/>Dashboard]
        end
    end
    
    subgraph "SERVIDOR DE BASE DE DATOS"
        SQLSERVER[(SQL Server<br/>Puerto 1433<br/>MAS_CIS_DB)]
    end
    
    subgraph "CACHE LAYER - Opcional"
        REDIS[Redis<br/>Puerto 6379<br/>Sesiones]
    end
    
    subgraph "CLIENTE - Vendedor"
        PHONE[📱 Smartphone<br/>WhatsApp App]
    end
    
    subgraph "CLIENTE - Administrador"
        BROWSER[💻 Navegador Web<br/>Dashboard]
    end
    
    subgraph "INTEGRACIÓN EXTERNA"
        ECOMMERCE[🛒 Plataforma<br/>E-commerce<br/>API REST]
    end
    
    %% Conexiones
    PHONE <-->|HTTPS| WA_CLOUD
    WA_CLOUD <-->|Webhook<br/>HTTPS| NGINX
    
    BROWSER <-->|HTTPS| NGINX
    
    NGINX <-->|Proxy Pass| FASTAPI
    NGINX -->|Serve| STATIC
    
    FASTAPI <--> AGENTS
    AGENTS <--> NLU_SVC
    
    AGENTS <-->|pyodbc<br/>TCP 1433| SQLSERVER
    AGENTS -.->|Opcional<br/>TCP 6379| REDIS
    
    AGENTS <-->|REST API<br/>HTTPS| ECOMMERCE
    
    %% Estilos
    style WA_CLOUD fill:#25D366,stroke:#128C7E,color:#fff
    style FASTAPI fill:#009688,stroke:#00695C,color:#fff
    style AGENTS fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style NLU_SVC fill:#ec4899,stroke:#db2777,color:#fff
    style SQLSERVER fill:#CC2927,stroke:#A91E1E,color:#fff
    style NGINX fill:#009639,stroke:#006428,color:#fff
    style REDIS fill:#DC382D,stroke:#A41E11,color:#fff
    style ECOMMERCE fill:#FF9900,stroke:#CC7A00,color:#fff
```

### Especificaciones de Despliegue

| Componente | Tecnología | Puerto | Recursos Mínimos |
|------------|-----------|--------|------------------|
| **FastAPI** | Python 3.10+ | 8000 | 2 CPU, 4GB RAM |
| **SQL Server** | SQL Server 2019+ | 1433 | 4 CPU, 8GB RAM |
| **Nginx** | Nginx 1.20+ | 80, 443 | 1 CPU, 1GB RAM |
| **Redis** | Redis 7.0+ | 6379 | 1 CPU, 2GB RAM |

---

## 7. Diagrama de Modelo de Datos

```mermaid
erDiagram
    PRODUCT ||--o{ TRANSACTION : "registra"
    
    PRODUCT {
        int id PK "Identificador único"
        string sku UK "Código de producto"
        string name "Nombre del producto"
        text description "Descripción"
        decimal price "Precio en soles"
        int stock_physical "Stock en tienda física"
        int stock_virtual "Stock reservado e-commerce"
        int stock_total "Stock total disponible"
        string category "Categoría"
        string size "Talla"
        string color "Color"
        string image_url "URL de imagen"
        datetime created_at "Fecha de creación"
        datetime updated_at "Última actualización"
    }
    
    TRANSACTION {
        int id PK "Identificador único"
        int product_id FK "Referencia a producto"
        enum transaction_type "sell|add|update|remove"
        int quantity "Cantidad operada"
        int previous_stock "Stock anterior"
        int new_stock "Stock nuevo"
        string vendor_phone "Teléfono del vendedor"
        text notes "Notas adicionales"
        datetime created_at "Fecha de transacción"
    }
    
    CHAT_SESSION {
        int id PK "Identificador único"
        string session_id UK "ID de sesión"
        string vendor_phone "Teléfono del vendedor"
        string vendor_name "Nombre del vendedor"
        string status "active|completed|expired"
        text context_data "Contexto JSON"
        datetime last_message_at "Último mensaje"
        datetime created_at "Inicio de sesión"
        datetime expires_at "Expiración"
    }
    
    AGENT_LOG {
        int id PK "Identificador único"
        enum agent_type "store|coordinator|gateway"
        string action "Acción realizada"
        text message "Mensaje de log"
        text metadata "Datos adicionales JSON"
        string status "success|error|warning"
        datetime created_at "Fecha de log"
    }
    
    SYNC_HISTORY {
        int id PK "Identificador único"
        string sync_type "full|partial|product"
        int products_synced "Productos sincronizados"
        string status "pending|success|failed"
        text error_message "Mensaje de error"
        decimal duration_seconds "Duración en segundos"
        datetime started_at "Inicio de sync"
        datetime completed_at "Fin de sync"
    }
```

---

## 8. Diagrama de Casos de Uso

```mermaid
graph TB
    subgraph "Sistema MAS-CIS"
        direction TB
        
        subgraph "Gestión de Inventario"
            CU01[CU-01: Sincronizar<br/>Stock vía Chat]
            CU02[CU-02: Recibir Alertas<br/>de Stock Bajo]
            CU03[CU-03: Corregir<br/>Inventario Manual]
        end
        
        subgraph "Consultas"
            CU04[CU-04: Consultar<br/>Inventario]
            CU05[CU-05: Consultar<br/>Resumen del Día]
            CU06[CU-06: Ver Historial<br/>de Transacciones]
        end
        
        subgraph "Administración"
            CU07[CU-07: Supervisar<br/>Sincronización]
            CU08[CU-08: Registrar Nuevo<br/>Agente de Tienda]
            CU09[CU-09: Monitorear<br/>Estado de Agentes]
        end
    end
    
    VENDEDOR((👤 Vendedor<br/>Emergente))
    ADMIN((👨‍💼 Administrador<br/>Plataforma))
    ECOMM((🛒 Sistema<br/>E-commerce))
    
    VENDEDOR --> CU01
    VENDEDOR --> CU02
    VENDEDOR --> CU03
    VENDEDOR --> CU04
    VENDEDOR --> CU05
    VENDEDOR --> CU06
    
    ADMIN --> CU07
    ADMIN --> CU08
    ADMIN --> CU09
    
    CU01 -.->|notifica| ECOMM
    CU03 -.->|actualiza| ECOMM
    CU07 -.->|consulta| ECOMM
    
    style CU01 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style CU02 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style CU03 fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style CU04 fill:#6366f1,stroke:#4f46e5,color:#fff
    style CU05 fill:#6366f1,stroke:#4f46e5,color:#fff
    style CU06 fill:#6366f1,stroke:#4f46e5,color:#fff
    style CU07 fill:#ec4899,stroke:#db2777,color:#fff
    style CU08 fill:#ec4899,stroke:#db2777,color:#fff
    style CU09 fill:#ec4899,stroke:#db2777,color:#fff
```

---

## Resumen para Asesor de Tesis

### Características Arquitectónicas Clave

✅ **Arquitectura Multiagente (MAS)**
- Agentes autónomos con responsabilidades específicas
- Comunicación asíncrona entre agentes
- Coordinación centralizada para consistencia

✅ **Procesamiento de Lenguaje Natural**
- Extracción de intenciones y entidades
- Soporte para español coloquial
- Sistema de confianza para validación

✅ **Sincronización en Tiempo Real**
- Actualización inmediata de inventario
- Notificación a plataforma e-commerce
- Prevención de "inventario falso"

✅ **Escalabilidad y Mantenibilidad**
- Arquitectura modular y extensible
- Separación clara de capas
- Código documentado y testeado

---

**Preparado para:** Revisión de Asesor de Tesis  
**Sistema:** MAS-CIS v1.0  
**Fecha:** 2025  
**Autor:** Prototipo de Tesis Universitaria
