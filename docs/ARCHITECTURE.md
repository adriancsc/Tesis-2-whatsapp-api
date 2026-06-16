# 🏗️ Arquitectura del Sistema MAS-CIS

## Documentación Técnica Detallada

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Flujo de Datos](#flujo-de-datos)
5. [Patrones de Diseño](#patrones-de-diseño)
6. [Diagramas Técnicos](#diagramas-técnicos)

---

## 🎯 Visión General

El **Sistema MAS-CIS** implementa una arquitectura de **Sistemas Multiagentes (MAS)** para resolver el problema de sincronización de inventario en tiempo real entre ventas físicas y comercio electrónico.

### Principios Arquitectónicos

1. **Separación de Responsabilidades**: Cada agente tiene un propósito específico
2. **Autonomía**: Los agentes toman decisiones independientes
3. **Comunicación Asíncrona**: Mensajes entre componentes
4. **Escalabilidad**: Diseño modular y extensible
5. **Tolerancia a Fallos**: Manejo robusto de errores

---

## 🏛️ Arquitectura de Alto Nivel

### Diagrama de Arquitectura General

```mermaid
graph TB
    subgraph "Capa de Presentación"
        V[Vendedor Emergente]
        D[Dashboard Admin]
    end
    
    subgraph "Capa de Comunicación"
        WA[WhatsApp Business]
        GW[Gateway de Comunicación]
        API[API REST FastAPI]
    end
    
    subgraph "Capa de Agentes MAS (LangGraph)"
        IG[Inventory Graph<br/>StateGraph]
        SA[Store Node<br/>Gestión de Menú FSM]
        CA[Coordinator Node<br/>Transacciones]
    end
    
    subgraph "Capa de Datos"
        DB[(Base de Datos<br/>SQLite/SQL Server)]
        MEM[Memoria<br/>Conversation Manager]
    end
    
    subgraph "Capa de Integración"
        EC[Plataforma<br/>E-commerce]
    end
    
    V -->|Mensaje numérico| WA
    WA -->|Webhook| GW
    GW -->|Agrupa Estado| IG
    IG -->|route| SA
    SA -->|route_after_store| CA
    CA -->|SQL Atómico| DB
    IG -->|Respuesta| GW
    GW -->|API Call| WA
    WA -->|Respuesta Textual| V
    
    D -->|HTTP| API
    API -->|Query| DB
    API -->|Response| D
    
    CA -->|Sync| EC
    EC -->|Stock Query| API
    
    GW -.->|Mantiene current_step| MEM
    
    style IG fill:#4f46e5,stroke:#4338ca,color:#fff
    style SA fill:#6366f1,stroke:#4f46e5,color:#fff
    style CA fill:#10b981,stroke:#059669,color:#fff
    style DB fill:#10b981,stroke:#059669,color:#fff
    style GW fill:#f59e0b,stroke:#d97706,color:#fff
```

### Capas del Sistema

| Capa | Responsabilidad | Tecnologías |
|------|----------------|-------------|
| **Presentación** | Interfaz con usuarios | WhatsApp, HTML/CSS/JS |
| **Comunicación** | Gateway y API | FastAPI, WhatsApp API |
| **Agentes** | Lógica de negocio | Python, spaCy |
| **Datos** | Persistencia | SQL Server, SQLAlchemy |
| **Integración** | Conexión externa | REST### 1. Grafo de Agentes (Inventory Graph)

**Propósito:** Máquina de Estados Finitos (FSM) gestionada por LangGraph que enruta las interacciones del usuario hacia el nodo adecuado.

```mermaid
graph TD
    START((START)) --> store_node["store_node<br/>Procesa input del menú"]
    store_node --> ROUTE{"route_after_store()"}
    ROUTE -->|"transacción pendiente"| coordinator_node["coordinator_node<br/>Transacción Atómica"]
    ROUTE -->|"sin transacción"| END_1((END))
    coordinator_node --> END_2((END))
    
    style store_node fill:#6366f1,color:#fff
    style coordinator_node fill:#10b981,color:#fff
    style ROUTE fill:#f59e0b,color:#000
```

**Código:** `src/agents/inventory_graph.py`

---

### 2. Nodo de Tienda (Store Node)

**Propósito:** Gestionar la navegación del menú numérico y mantener el contexto de la transacción en preparación.

**Características:**
- ✅ Control de estado conversacional (current_step)
- ✅ Generación dinámica de menús desde la base de datos
- ✅ Acumulación de atributos transaccionales en el `AgentState`

---

### 3. Nodo Coordinador (Coordinator Node)

**Propósito:** Orquestar operaciones atómicas de inventario sobre las variantes de producto.

**Responsabilidades:**
- ✅ Validación estricta de reglas de negocio sobre el stock físico
- ✅ Actualización atómica de `ProductVariant`
- ✅ Registro inmutable en el kárdex (`Transaction`)
- ✅ Registro de auditoría (`AgentLog`)

---y para análisis morfológico
- 🎯 Clasificación de intenciones
- 📊 Scoring de confianza

**Código:** [nlu_processor.py](file:///c:/Prototipo%20Tesis%201/src/agents/nlu_processor.py)

---

### 4. Gateway de WhatsApp

**Propósito:** Puente entre WhatsApp Business API y el sistema.

```mermaid
sequenceDiagram
    participant V as Vendedor
    participant WA as WhatsApp
    participant GW as Gateway
    participant SA as Store Agent
    
    V->>WA: Mensaje de texto
    WA->>GW: Webhook POST
    GW->>GW: Parsear webhook
    GW->>WA: Marcar como leído
    GW->>SA: Enviar mensaje
    SA->>SA: Procesar
    SA->>GW: Respuesta
    GW->>WA: Enviar mensaje
    WA->>V: Respuesta
```

**Funcionalidades:**
- 📨 Recepción de webhooks
- 📤 Envío de mensajes
- ✅ Verificación de webhook
- 📎 Soporte para multimedia

**Código:** [whatsapp_gateway.py](file:///c:/Prototipo%20Tesis%201/src/gateway/whatsapp_gateway.py)

---

## 🔄 Flujo de Datos

### Flujo Completo de una Venta

```mermaid
sequenceDiagram
    autonumber
    participant V as Vendedor
    participant WA as WhatsApp
    participant GW as Gateway
    participant IG as LangGraph
    participant DB as Database
    
    V->>WA: (Navega menú y selecciona confirmar cantidad) "1"
    WA->>GW: Webhook
    GW->>IG: inventory_graph.invoke(AgentState)
    IG->>IG: store_node procesa la confirmación
    IG->>IG: route_after_store delega al coordinator_node
    IG->>DB: coordinator_node valida stock en variante
    DB->>IG: OK
    IG->>DB: UPDATE ProductVariant
    IG->>DB: INSERT Transaction (Kárdex)
    IG->>GW: Retorna AgentState modificado (success)
    GW->>WA: Enviar comprobante de texto
    WA->>V: "✅ Operación completada con éxito"
```

### Estados de una Operación

```mermaid
stateDiagram-v2
    [*] --> Recibido: Mensaje llega
    Recibido --> Parseando: NLU procesa
    Parseando --> Validando: Comando válido
    Parseando --> Rechazado: Comando inválido
    Validando --> Ejecutando: Validación OK
    Validando --> Rechazado: Validación falla
    Ejecutando --> Completado: Éxito
    Ejecutando --> Error: Fallo DB
    Completado --> [*]
    Rechazado --> [*]
    Error --> [*]
```

---

## 🎨 Patrones de Diseño

### 1. **Patrón Agente (Agent Pattern)**

Cada agente es autónomo y encapsula su lógica:

```python
class BaseAgent(ABC):
    @abstractmethod
    async def process_message(self, message: Dict) -> Dict:
        pass
```

### 2. **Patrón Strategy (NLU)**

Diferentes estrategias de parsing:

```python
# Regex patterns
# spaCy analysis
# Confidence scoring
```

### 3. **Patrón Repository (Database)**

Abstracción de acceso a datos:

```python
with get_db() as db:
    product = db.query(Product).filter(...).first()
```

### 4. **Patrón Gateway (WhatsApp)**

Encapsulación de API externa:

```python
class WhatsAppGateway:
    def send_message(self, to, message):
        # Abstrae la complejidad de la API
```

### 5. **Patrón Observer (Logging)**

Sistema de logging centralizado:

```python
self.log_activity("action", metadata)
```

---

## 📊 Modelo de Datos

### Diagrama Entidad-Relación

```mermaid
erDiagram
    PRODUCT ||--o{ TRANSACTION : has
    PRODUCT {
        int id PK
        string sku UK
        string name
        float price
        int stock_physical
        int stock_virtual
        int stock_total
        datetime created_at
        datetime updated_at
    }
    
    TRANSACTION {
        int id PK
        int product_id FK
        enum transaction_type
        int quantity
        int previous_stock
        int new_stock
        string vendor_phone
        datetime created_at
    }
    
    CHAT_SESSION {
        int id PK
        string session_id UK
        string vendor_phone
        string status
        text context_data
        datetime last_message_at
        datetime expires_at
    }
    
    AGENT_LOG {
        int id PK
        enum agent_type
        string action
        text message
        text metadata
        string status
        datetime created_at
    }
    
    SYNC_HISTORY {
        int id PK
        string sync_type
        int products_synced
        string status
        text error_message
        datetime started_at
        datetime completed_at
    }
```

### Relaciones Clave

- **Product → Transaction**: Un producto puede tener múltiples transacciones (1:N)
- **ChatSession**: Independiente, gestiona conversaciones
- **AgentLog**: Registro de actividad de agentes
- **SyncHistory**: Historial de sincronizaciones

---

## 🔐 Seguridad y Validación

### Capas de Validación

```mermaid
graph TD
    A[Mensaje de entrada] --> B{Validación NLU}
    B -->|Confianza < 0.7| C[Rechazar]
    B -->|Confianza >= 0.7| D{Validación de Negocio}
    D -->|Stock insuficiente| C
    D -->|Cantidad inválida| C
    D -->|Producto no existe| C
    D -->|Todo OK| E[Ejecutar Operación]
    E --> F{Transacción DB}
    F -->|Error| G[Rollback]
    F -->|Éxito| H[Commit]
    
    style B fill:#f59e0b,color:#fff
    style D fill:#f59e0b,color:#fff
    style E fill:#10b981,color:#fff
    style C fill:#ef4444,color:#fff
    style G fill:#ef4444,color:#fff
    style H fill:#10b981,color:#fff
```

### Validaciones Implementadas

1. **Validación de Menú (Store Node)**
   - Opciones numéricas válidas según estado (FSM)
   - Cantidades son números enteros > 0

2. **Validación de Negocio (Coordinator Node)**
   - Stock suficiente para ventas/mermas
   - Existencia real de la variante en BD
   - Producto existe
   - Operación permitida

3. **Validación de Datos (Database)**
   - Constraints de SQL
   - Tipos de datos
   - Relaciones integridad referencial

---

## 🚀 Escalabilidad

### Estrategias de Escalamiento

```mermaid
graph TB
    subgraph "Escalamiento Horizontal"
        SA1[Store Agent 1]
        SA2[Store Agent 2]
        SA3[Store Agent N]
    end
    
    subgraph "Load Balancer"
        LB[Balanceador de Carga]
    end
    
    subgraph "Coordinadores"
        CA1[Coordinator 1]
        CA2[Coordinator 2]
    end
    
    subgraph "Database Cluster"
        DBM[(DB Master)]
        DBR1[(DB Replica 1)]
        DBR2[(DB Replica 2)]
    end
    
    LB --> SA1
    LB --> SA2
    LB --> SA3
    
    SA1 --> CA1
    SA2 --> CA1
    SA3 --> CA2
    
    CA1 --> DBM
    CA2 --> DBM
    DBM --> DBR1
    DBM --> DBR2
```

### Puntos de Escalamiento

1. **Agentes**: Múltiples instancias por tipo
2. **API**: Load balancing con Nginx
3. **Database**: Replicación master-slave
4. **Cache**: Redis cluster para sesiones

---

## 📈 Monitoreo y Observabilidad

### Métricas Clave

```mermaid
graph LR
    subgraph "Métricas del Sistema"
        M1[Mensajes/segundo]
        M2[Tiempo de respuesta]
        M3[Tasa de error]
        M4[Stock sincronizado]
    end
    
    subgraph "Métricas de Agentes"
        A1[Agentes activos]
        A2[Operaciones/minuto]
        A3[Confianza promedio NLU]
    end
    
    subgraph "Métricas de DB"
        D1[Queries/segundo]
        D2[Conexiones activas]
        D3[Tiempo de transacción]
    end
    
    style M1 fill:#6366f1,color:#fff
    style M2 fill:#6366f1,color:#fff
    style M3 fill:#6366f1,color:#fff
    style M4 fill:#6366f1,color:#fff
```

### Sistema de Logging

- **Nivel INFO**: Operaciones normales
- **Nivel WARNING**: Situaciones anómalas
- **Nivel ERROR**: Fallos recuperables
- **Nivel CRITICAL**: Fallos del sistema

---

## 🎯 Casos de Uso Principales

### CU-01: Sincronizar Stock vía Chat

```mermaid
sequenceDiagram
    actor V as Vendedor
    participant S as Sistema
    participant DB as Base de Datos
    
    V->>S: "Vendí 3 polos rojos M"
    S->>S: Procesar NLU
    S->>DB: Verificar stock
    DB->>S: Stock disponible: 15
    S->>DB: Actualizar stock a 12
    S->>V: "✅ Venta registrada. Stock: 12"
```

### CU-02: Consultar Inventario

```mermaid
sequenceDiagram
    actor V as Vendedor
    participant S as Sistema
    participant DB as Base de Datos
    
    V->>S: "¿Cuánto stock hay de POLO-R-M?"
    S->>DB: SELECT stock
    DB->>S: Stock: 12 físico, 8 virtual
    S->>V: "📦 Stock total: 20<br/>Físico: 12, Virtual: 8"
```

---

## 🔧 Tecnologías y Justificación

| Tecnología | Justificación |
|------------|---------------|
| **Python** | Excelente ecosistema de datos e integración |
| **FastAPI** | Alto rendimiento, documentación automática |
| **SQLAlchemy** | ORM robusto, soporte multi-DB (SQLite/SQL Server) |
| **LangGraph** | Framework nativo de agentes, FSM determinista para UX crítica |
| **WhatsApp API** | Canal preferido de vendedores |

---

## 📝 Conclusiones Arquitectónicas

### Fortalezas

✅ **Modularidad**: Componentes independientes y reutilizables  
✅ **Escalabilidad**: Diseño horizontal y vertical  
✅ **Mantenibilidad**: Código limpio y documentado  
✅ **Extensibilidad**: Fácil agregar nuevos agentes  
✅ **Robustez**: Validación en múltiples capas  

### Áreas de Mejora Futuras

🔄 **Caché distribuido**: Implementar Redis cluster  
🔄 **Message Queue**: Agregar RabbitMQ/Kafka  
🔄 **Microservicios**: Separar en contenedores Docker  
🔄 **CI/CD**: Pipeline automatizado  
🔄 **Autenticación**: JWT para API  

---

**Documento preparado para revisión de asesor de tesis**  
**Sistema MAS-CIS v1.0 - 2025**
