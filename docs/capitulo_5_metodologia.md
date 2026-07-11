# CAPÍTULO V: METODOLOGÍA

## 5.1. Diseño de Investigación

La presente investigación es de tipo **aplicada**, dado que tiene como propósito fundamental resolver una problemática práctica y específica: la desincronización de inventarios en las ventas multicanal (WhatsApp y portal web) de los microempresarios. Para abordar este problema, el estudio adopta el enfoque metodológico de **Design Science Research (DSR)**, el cual se centra en la creación y evaluación de un artefacto tecnológico innovador —en este caso, un Sistema Multiagente Inteligente basado en LangGraph— para solucionar el problema identificado.

El diseño de la investigación es **experimental**, específicamente un diseño preexperimental de tipo caso único (pretest/postest), en el cual se observa el comportamiento del inventario y la gestión de ventas antes y después de la implementación del artefacto. 

Gráficamente, la relación de variables se estructura de la siguiente manera:
*   **Variable Independiente (VI):** Implementación del Sistema Multiagente Inteligente con LangGraph.
*   **Variable Dependiente (VD):** Eficiencia en la sincronización del inventario multicanal (medida en latencia de actualización, reducción de quiebres de stock y tasa de concurrencia exitosa).

## 5.2. Unidad de análisis

La unidad de análisis está constituida por los **microempresarios del sector textil**, así como por los procesos transaccionales de venta y gestión de inventario (Kárdex) que estos ejecutan diariamente a través de sus canales digitales (WhatsApp y plataformas e-commerce).

## 5.3. Población de estudio

La población o universo de estudio comprende al conjunto de **microempresarios del Emporio Comercial de Gamarra** (Lima, Perú), dedicados específicamente a la producción y venta textil (rubro de confección y venta de polos), que actualmente utilizan WhatsApp como canal principal de ventas directas y que buscan o poseen integración con un portal de ventas web.

## 5.4. Tamaño de muestra

Debido a la naturaleza de la metodología DSR, la validación del artefacto no requiere una muestra poblacional masiva, sino una muestra representativa que permita someter el sistema a un entorno real de uso. Por razones prácticas y de viabilidad técnica, el tamaño de la muestra para la prueba piloto se ha determinado en un grupo selecto de **[Insertar Número, ej. 3 a 5] microempresas** textiles de Gamarra que cumplan con los criterios de inclusión. Asimismo, a nivel transaccional, la muestra de evaluación del sistema comprenderá un conjunto de **[Insertar Número, ej. 100] transacciones simultáneas** simuladas y reales para validar la concurrencia del software.

## 5.5. Selección de muestra

El procedimiento empleado para la selección de la muestra es el **muestreo no probabilístico por conveniencia e intencional**. Los sujetos de estudio fueron seleccionados bajo los siguientes criterios de inclusión:
1. Pertenecer activamente al Emporio Comercial de Gamarra.
2. Contar con un modelo de ventas híbrido o multicanal (uso activo de WhatsApp Business y operaciones web).
3. Manifestar disposición para participar en la implementación piloto del software y proporcionar retroalimentación sobre su experiencia de uso.

## 5.6. Técnicas de recolección de Datos

La recolección de datos se llevará a cabo en dos dimensiones (técnica y usuaria) durante la fase de evaluación del artefacto, bajo condiciones de entorno de producción (Nube de Railway). Se aplicarán las siguientes técnicas:

**a) Técnicas a emplear:**
*   **Observación directa y análisis de registros (Logs):** Para medir el rendimiento técnico del sistema. Se capturarán automáticamente los tiempos de ejecución de los agentes, la latencia de actualización en la base de datos (PostgreSQL/SQLite) y las tasas de éxito en la concurrencia mediante los logs del sistema FastAPI y LangGraph.
*   **Encuestas y/o entrevistas semiestructuradas:** Dirigidas a los microempresarios seleccionados para evaluar la percepción de usabilidad, adopción tecnológica y satisfacción tras el uso del artefacto.

**b) Pasos a seguir:**
1. Despliegue del Sistema Multiagente en el entorno de la microempresa piloto.
2. Monitoreo pasivo del sistema durante un periodo establecido (ej. 15 días).
3. Extracción de la data técnica alojada en la base de datos.
4. Aplicación del instrumento de encuesta al microempresario al finalizar el periodo de prueba.

## 5.7. Análisis e interpretación de la información

El procesamiento de la información obtenida se realizará de la siguiente manera:
**a) Proceso de clasificación y registro:**
Los datos técnicos (latencia, tiempos de respuesta, bloqueos de concurrencia) serán extraídos de los logs del backend y estructurados en hojas de cálculo. Los datos cualitativos (encuestas) serán tabulados mediante escalas de Likert.

**b) Técnicas analíticas:**
Se utilizará **estadística descriptiva** para analizar los datos cuantitativos obtenidos del software (cálculo de medias, desviación estándar y tiempos máximos/mínimos de latencia). Para comprobar la hipótesis de investigación, se contrastarán las métricas de sincronización manual previa (línea base) frente a los resultados automatizados por el Sistema Multiagente, demostrando la mejora en la coherencia de los datos del Kárdex.

## 5.8. Descripción del Sistema Multiagente

El sistema opera como un middleware autónomo basado en LangGraph que orquesta la lógica de negocio del inventario. Sus funciones principales son las siguientes:

*   **Procesamiento Transaccional Autónomo:** Recibe interacciones conversacionales desde WhatsApp, interpreta la intención del vendedor y ejecuta las operaciones de actualización de inventario directamente en la base de datos sin requerir una interfaz gráfica tradicional.
*   **Control de Concurrencia Centralizado:** Gestiona bloqueos a nivel de producto (SKU) garantizando la integridad de los datos cuando ingresan solicitudes de venta simultáneas desde múltiples canales digitales.
*   **Sincronización Reactiva Multicanal:** Propaga automáticamente cualquier alteración del stock físico en el Kárdex hacia los catálogos virtuales del portal web para prevenir sobreventas.
*   **Emisión Proactiva de Alertas:** Monitorea de forma continua los niveles de inventario resultantes tras cada transacción para enviar notificaciones inmediatas al vendedor si se detectan anomalías o quiebres de stock.

## 5.9. Requisitos del Sistema

### 5.9.1. Requisitos Funcionales

*   **Gestión de inventario vía WhatsApp:** El sistema debe permitir al vendedor registrar ventas, ingresos de mercadería y mermas de productos a través de un flujo conversacional por mensajería instantánea.
*   **Procesamiento de ventas web:** El sistema debe recibir y procesar transacciones de compra originadas desde el portal de ventas web de forma autónoma, sin intervención del vendedor.
*   **Actualización del Kárdex en tiempo real:** El sistema debe actualizar el stock del Kárdex centralizado de forma inmediata tras cada transacción ejecutada desde cualquier canal.
*   **Trazabilidad transaccional:** El sistema debe registrar cada movimiento de inventario con datos completos de tipo de operación, cantidad, stock anterior, stock nuevo, canal de origen, fecha y operador responsable.
*   **Alertas proactivas de stock crítico:** El sistema debe notificar automáticamente al dueño del negocio vía WhatsApp cuando el stock de un producto descienda a niveles críticos o se agote por completo.
*   **Generación de reportes diarios:** El sistema debe consolidar los movimientos del día y presentar un resumen con totales de ventas, ingresos, mermas y balance neto de unidades.
*   **Consulta de inventario actual:** El sistema debe mostrar el estado del inventario por producto y talla, incluyendo indicadores visuales de disponibilidad.
*   **Sincronización con el portal web:** El sistema debe propagar las actualizaciones de stock hacia el catálogo del portal de ventas web tras cada transacción del Kárdex.
*   **Detección de anomalías en mermas:** El sistema debe identificar patrones inusuales en las mermas diarias y generar alertas cuando estas superen umbrales predefinidos.
*   **Validación preventiva de stock:** El sistema debe verificar la disponibilidad de unidades antes de confirmar cualquier operación de salida, rechazando transacciones que excedan el stock disponible.

### 5.9.2. Requisitos No Funcionales

*   **Integridad transaccional:** El sistema debe garantizar propiedades ACID en todas las operaciones de stock, ejecutando rollback automático ante fallos para prevenir inconsistencias en el Kárdex.
*   **Control de concurrencia:** El sistema debe gestionar accesos simultáneos al mismo producto mediante bloqueos a nivel de SKU, previniendo condiciones de carrera entre canales.
*   **Disponibilidad continua:** El sistema debe operar de forma ininterrumpida (24/7), desplegado en una plataforma cloud con mecanismos de reinicio automático.
*   **Latencia máxima de respuesta:** El tiempo de procesamiento de una transacción completa no debe exceder los 5 segundos bajo condiciones normales de operación.
*   **Arquitectura desacoplada:** El diseño del sistema debe permitir escalar o migrar componentes individuales sin necesidad de reescribir la lógica de negocio existente.
*   **Comunicación cifrada:** Todas las comunicaciones con servicios externos deben realizarse exclusivamente mediante protocolo HTTPS con certificados TLS.
*   **Validación de datos de entrada:** El sistema debe rechazar automáticamente operaciones con cantidades negativas, nulas o superiores a 1000 unidades por transacción individual.
*   **Registro de actividad de agentes:** Toda acción ejecutada por los agentes autónomos debe quedar registrada en logs persistentes con tipo de agente, acción, resultado y metadatos asociados.

## 5.10. Ciclo de Vida de Desarrollo de Software (SDLC)

Para operacionalizar la metodología DSR y asegurar la construcción rigurosa del artefacto (Sistema Multiagente), se adoptó un ciclo de vida de desarrollo de software iterativo estructurado en cinco fases principales, adaptadas a las necesidades específicas de integración híbrida (WhatsApp y portales web):

### Fase 1: Análisis de Requerimientos del sistema
*   **1.1. Requerimientos Funcionales:** Definición de la capacidad del sistema para recibir webhooks de Meta, procesar intenciones de compra/actualización y sincronizar el Kárdex centralizado en tiempo real.
*   **1.2. Requerimientos No Funcionales:** Especificación de los umbrales de latencia máxima, manejo de concurrencia de base de datos y requisitos de disponibilidad (24/7) en un entorno PaaS.
*   **1.3. Casos de uso principales:** Modelado de los flujos de interacción del vendedor (recepción de alertas proactivas) y de los sistemas externos (registro de transacciones vía portal web e-commerce).

### Fase 2: Diseño del sistema
*   **2.1. Arquitectura del sistema:** Definición del modelo de software desacoplado utilizando el paradigma de Inteligencia Artificial Agentic (Sistemas Multiagente).
*   **2.2. Diseño de Base de Datos:** Modelado relacional del Kárdex Automatizado (Single Source of Truth) diseñado específicamente para soportar bloqueos pesimistas ante transacciones simultáneas.
*   **2.3. Diseño de flujos de agentes (StateGraph):** Diseño lógico de las transiciones de estado en LangGraph entre los agentes orquestadores: Agente de Tienda, Agente de Sincronización, Agente Coordinador y Agente de Alertas.
*   **2.4. Selección de tecnologías:** Justificación técnica del uso de Python 3.11, FastAPI (gateway HTTP), SQLAlchemy (ORM) y LangGraph (orquestación de flujos).
*   **2.5. Producto:** Especificación de Diseño Técnico (Diagramas de Despliegue UML y Modelado de Infraestructura).

### Fase 3: Implementación y desarrollo
*   **3.1. Configuración de Infraestructura:** Preparación del entorno de contenedores gestionados (Railway PaaS) y definición de variables de entorno de seguridad (.env).
*   **3.2. Integración de APIs:** Desarrollo de la pasarela (*gateway*) para consumir y recibir eventos de la Graph API de Meta (WhatsApp Business Cloud API).
*   **3.3. Desarrollo del Workflow (Grafo de Estado):** Codificación de los nodos y ejes de LangGraph para la toma de decisiones autónoma y la implementación del manejador de bloqueos (*LockManager*) en la base de datos.
*   **3.4. Producto:** Sistema Funcional (Prototipo Alpha).

### Fase 4: Pruebas y Validación
*   **4.1. Pruebas Funcionales:** Verificación en entornos aislados del correcto enrutamiento de los mensajes JSON entrantes y actualización de inventario unitario.
*   **4.2. Pruebas de Integración:** Ejecución de pruebas de carga automatizadas simulando múltiples webhooks concurrentes (concurrencia masiva) para validar la integridad transaccional ACID de la base de datos.
*   **4.3. Validación con usuarios reales:** Despliegue de un piloto controlado con una muestra intencional de microempresarios textiles de Gamarra.
*   **4.4. Producto:** Sistema Validado (Versión Beta estable).

### Fase 5: Implementación en Producción
*   **5.1. Configuración del Número de WhatsApp Business:** Verificación comercial y enlace del número telefónico productivo del microempresario en los servidores de Meta.
*   **5.2. Configuración de Dominio y SSL:** Habilitación del proxy inverso (Load Balancer) y certificados de cifrado TLS en Railway para asegurar la recepción de webhooks públicos.
*   **5.3. Migración de datos de prueba:** Limpieza del Kárdex de prueba y carga del inventario real inicial (productos y variantes) de la microempresa.
*   **5.4. Capacitación de usuarios:** Entrega del "Manual del Sistema Multiagente" y lineamientos operativos de uso al vendedor/dueño del negocio.
*   **5.5. Documentación:** Generación final de manuales técnicos, mapeo teórico y esquemas de red.
*   **5.6. Monitoreo inicial:** Revisión activa de los logs en la consola del backend para descartar anomalías o cuellos de botella en los primeros días de operación real.
*   **5.7. Alertas configuradas:** Activación del módulo autónomo (Agente de Alertas) para notificar proactivamente al celular del dueño ante detección de quiebres de stock.
*   **5.8. Producto:** Sistema en operación (Release Final productivo).
