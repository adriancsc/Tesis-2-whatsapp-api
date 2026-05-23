# Diagrama de Arquitectura del Sistema MAS-CIS

## Sistema Multiagente para Sincronización Centralizada de Inventario

---

## Figura 1: Arquitectura General del Sistema

![Arquitectura del Sistema MAS-CIS - Con NLU](C:/Users/adria/.gemini/antigravity/brain/dec6a524-04a5-428a-9856-ab0e16c3e196/diagrama_arquitectura_formal_con_nlu_1764203743639.png)

*Figura 1. Arquitectura del Sistema MAS-CIS. Diagrama formal detallando el flujo de información, destacando el **Motor NLU** como componente central para el procesamiento del lenguaje natural entre el Agente de Tienda y el Agente Coordinador.*

---

## Descripción de la Arquitectura

El Sistema MAS-CIS implementa una **arquitectura por capas** que separa las responsabilidades del sistema en cinco niveles jerárquicos, facilitando el mantenimiento, escalabilidad y comprensión del sistema.

### Capa 1: Presentación

Esta capa representa la interfaz con los usuarios finales del sistema:

- **Vendedor Emergente**: Usuario principal que interactúa con el sistema a través de mensajes de texto en lenguaje natural.
- **WhatsApp Business**: Canal de comunicación elegido por su amplia adopción en el contexto del comercio informal peruano.

### Capa 2: Comunicación

Responsable de gestionar la comunicación bidireccional entre usuarios y el sistema:

- **Gateway de Comunicación**: Componente que recibe webhooks de WhatsApp Business API y enruta los mensajes hacia los agentes correspondientes.
- **API REST**: Interfaz de programación que expone los servicios del sistema para integración con plataformas externas y el dashboard administrativo.

### Capa 3: Agentes (Sistema Multiagente)

**Núcleo del sistema** que implementa la lógica de negocio mediante agentes autónomos:

#### Agente de Tienda
- **Función**: Interfaz inteligente entre el vendedor y el sistema
- **Responsabilidades**:
  - Recepción y validación de mensajes
  - Gestión de sesiones conversacionales
  - Búsqueda de productos en base de datos
  - Generación de respuestas contextuales

#### Procesador NLU (Natural Language Understanding)
- **Función**: Interpretación de comandos en lenguaje natural
- **Responsabilidades**:
  - Extracción de intenciones (vender, agregar, consultar, etc.)
  - Identificación de entidades (productos, cantidades, atributos)
  - Cálculo de nivel de confianza del análisis
  - Normalización de comandos

#### Agente Coordinador
- **Función**: Orquestación de operaciones de inventario
- **Responsabilidades**:
  - Validación de reglas de negocio
  - Actualización atómica de stock
  - Registro de transacciones
  - Sincronización con plataforma e-commerce
  - Detección y resolución de conflictos

### Capa 4: Datos

Capa de persistencia que almacena el estado del sistema:

- **Base de Datos SQL Server**: Almacenamiento relacional de productos, transacciones, sesiones y logs del sistema.
- **Cache (Redis)**: Almacenamiento temporal de sesiones activas y datos de acceso frecuente (opcional).

### Capa 5: Integración

Capa que conecta el sistema con servicios externos:

- **Plataforma E-commerce**: Sistema de comercio electrónico que consume la información de inventario actualizada en tiempo real a través de la API REST.

---

## Flujo de Información

El flujo de datos en el sistema sigue un patrón vertical descendente y ascendente:

### Flujo Descendente (Solicitud)
1. El vendedor envía un mensaje por WhatsApp
2. El Gateway recibe el webhook y parsea el mensaje
3. El Agente de Tienda procesa el mensaje con ayuda del NLU
4. El Agente Coordinador valida y ejecuta la operación
5. La Base de Datos se actualiza
6. La Plataforma E-commerce es notificada

### Flujo Ascendente (Respuesta)
1. El Agente Coordinador confirma la operación
2. El Agente de Tienda genera una respuesta
3. El Gateway envía el mensaje por WhatsApp
4. El vendedor recibe la confirmación

---

## Características Arquitectónicas

### Modularidad
Cada componente tiene responsabilidades bien definidas y puede ser desarrollado, probado y mantenido de forma independiente.

### Escalabilidad
La arquitectura por capas permite escalar componentes específicos según la demanda. Los agentes pueden replicarse horizontalmente.

### Autonomía
Los agentes operan de forma autónoma, tomando decisiones basadas en su conocimiento y reglas de negocio sin intervención externa.

### Tolerancia a Fallos
El sistema implementa validación en múltiples niveles y manejo de errores en cada capa, garantizando robustez operacional.

### Extensibilidad
Nuevos agentes o canales de comunicación pueden agregarse sin modificar la arquitectura existente.

---

## Tecnologías Implementadas

| Capa | Componente | Tecnología |
|------|-----------|-----------|
| Presentación | WhatsApp | Meta Cloud API |
| Comunicación | Gateway | Python + FastAPI |
| Comunicación | API REST | FastAPI + Uvicorn |
| Agentes | Store Agent | Python |
| Agentes | NLU Processor | spaCy 3.7 |
| Agentes | Coordinator | Python + SQLAlchemy |
| Datos | Base de Datos | SQL Server |
| Datos | Cache | Redis (opcional) |
| Integración | E-commerce | REST API |

---

## Justificación del Diseño

### Elección de Arquitectura Multiagente

La arquitectura de sistemas multiagentes (MAS) fue seleccionada por las siguientes razones:

1. **Separación de Responsabilidades**: Cada agente tiene un propósito específico, facilitando el desarrollo y mantenimiento.

2. **Autonomía**: Los agentes pueden tomar decisiones independientes basadas en su conocimiento local.

3. **Escalabilidad**: Los agentes pueden replicarse para manejar mayor carga de trabajo.

4. **Flexibilidad**: Nuevos agentes pueden agregarse para extender funcionalidades sin afectar el sistema existente.

### Elección de WhatsApp como Canal

WhatsApp fue seleccionado como canal de comunicación principal debido a:

- Alta penetración en el mercado peruano (>90% de usuarios de smartphone)
- Familiaridad de los vendedores emergentes con la plataforma
- Interfaz simple que no requiere capacitación adicional
- API oficial de Meta con soporte empresarial

### Elección de SQL Server

SQL Server fue seleccionado como base de datos por:

- Requerimiento del contexto de implementación
- Soporte robusto para transacciones ACID
- Herramientas de administración empresariales
- Escalabilidad vertical y horizontal

---

## Conclusión

La arquitectura propuesta del Sistema MAS-CIS combina los principios de sistemas multiagentes con tecnologías modernas de desarrollo web y procesamiento de lenguaje natural, resultando en una solución escalable, mantenible y extensible para el problema de sincronización de inventario en comercio híbrido.

La separación en capas y la autonomía de los agentes permiten que el sistema sea robusto ante fallos y fácil de extender con nuevas funcionalidades en el futuro.

---

**Figura preparada para:** Documento de Tesis  
**Sistema:** MAS-CIS v1.0  
**Fecha:** 2025
