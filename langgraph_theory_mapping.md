# Mapeo Teórico de LangGraph vs. Implementación Real

Este documento contrasta los elementos teóricos oficiales del framework LangGraph con su aplicación exacta en el código fuente de tu Sistema Multiagente (MAS). Es una herramienta ideal para justificar decisiones arquitectónicas durante la sustentación.

---

## 1. Elementos Teóricos SÍ Aplicados en el Proyecto

### 1.1. StateGraph (Grafo de Estado)
- **Teoría:** Es la clase principal que orquesta el flujo de ejecución. Define un autómata donde el estado muta a medida que pasa por los nodos.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Línea 211).
  - **Evidencia:** `workflow = StateGraph(MASState)`

### 1.2. State (Estado Compartido)
- **Teoría:** Un esquema (generalmente `TypedDict` o `Pydantic`) que define la estructura de datos que fluye entre los nodos.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `state.py` (Línea 83).
  - **Evidencia:** `class MASState(TypedDict):` define los 21 campos que componen la memoria del sistema.

### 1.3. Nodes (Nodos)
- **Teoría:** Funciones de Python o "Runnables" que contienen la lógica. Reciben el estado actual y devuelven un diccionario con las claves a actualizar.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Líneas 214-217).
  - **Evidencia:** `workflow.add_node("store_agent", store_agent_node)`. Se aplican 4 nodos (`store`, `coordinator`, `sync`, `alert`).

### 1.4. Reducers (Operadores de Reducción)
- **Teoría:** Por defecto, si un nodo devuelve una clave (ej. `x: 2`), LangGraph sobrescribe el valor anterior. Los "Reducers" le dicen a LangGraph cómo *combinar* los valores en lugar de sobrescribirlos (ej. sumar a una lista).
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `state.py` (Línea 119).
  - **Evidencia:** `messages: Annotated[list, add]`. Utiliza el reducer `operator.add` para asegurar que los mensajes inter-agente se acumulen en una cola histórica y nunca se borren.

### 1.5. Conditional Edges (Aristas Condicionales y Funciones de Ruteo)
- **Teoría:** Caminos dinámicos donde una función evalúa el estado y decide cuál es el siguiente nodo a ejecutar.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Líneas 220, 230, 240, 250).
  - **Evidencia:** `workflow.add_conditional_edges(START, route_by_source, ...)` usando funciones de ruteo personalizadas como `route_after_coordinator`.

### 1.6. Normal Edges (Aristas Simples)
- **Teoría:** Un camino determinista y obligatorio de un nodo a otro (A siempre va a B).
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Línea 261).
  - **Evidencia:** `workflow.add_edge("alert_agent", END)`. El agente de alertas siempre termina el flujo, sin condiciones.

### 1.7. START y END Nodes (Nodos Especiales)
- **Teoría:** Constantes nativas de LangGraph que definen el punto de entrada al grafo y el punto de terminación del flujo.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Líneas 220 y 261).
  - **Evidencia:** Se importan de `langgraph.graph` y se usan explícitamente en el enrutamiento.

### 1.8. Checkpointer (Memoria a Largo Plazo / Hilos)
- **Teoría:** Mecanismo para persistir el estado del grafo entre múltiples interacciones. Permite que el sistema recuerde una conversación basándose en un `thread_id`.
- **En tu código:** ✅ **APLICADO**.
  - **Ubicación:** `mas_orchestrator.py` (Líneas 187 y 268).
  - **Evidencia:** `memory_saver = MemorySaver()` inyectado al compilar el grafo. El `thread_id` se asigna al número de teléfono del vendedor: `config = {"configurable": {"thread_id": vendor_phone}}`.

---

## 2. Elementos Teóricos NO Aplicados (Ausentes)

Existen características avanzadas de LangGraph que no están implementadas en tu código. Si el jurado pregunta por ellas, aquí tienes la justificación técnica de por qué no se usaron.

### 2.1. Human-in-the-loop / Interrupts (Pausas de Grafo)
- **Teoría:** LangGraph permite pausar la ejecución del grafo a la mitad (usando `interrupt_before` o `interrupt_after` en el `compile()`) para esperar la aprobación humana antes de seguir.
- **En tu código:** ❌ **NO APLICADO**.
  - **Justificación:** Tu sistema no pausa el grafo en memoria. En su lugar, el grafo arranca y termina en microsegundos tras cada input numérico del usuario. La "pausa" ocurre fuera de LangGraph (en WhatsApp) y el estado se recupera gracias al `Checkpointer`. Esta decisión arquitectónica ahorra memoria RAM en el servidor, ya que no se mantienen procesos colgados esperando que el usuario de WhatsApp responda.

### 2.2. Tool Nodes (Llamadas automáticas a herramientas externas)
- **Teoría:** LangGraph incluye el componente `ToolNode`, que permite a un LLM decidir autónomamente invocar herramientas (ej. buscar en Google, ejecutar código) usando `bind_tools()`.
- **En tu código:** ❌ **NO APLICADO**.
  - **Justificación:** Tu arquitectura utiliza agentes deterministas y validaciones de negocio estrictas en lugar de agentes LLM probabilísticos. El Coordinador interactúa con la base de datos PostgreSQL de forma directa y estructurada (ACID) mediante SQLAlchemy, no a través de una "Tool" invocada por un LLM, garantizando un 100% de precisión matemática.

### 2.3. Subgraphs (Sub-grafos anidados)
- **Teoría:** Un nodo en LangGraph puede ser, internamente, otro grafo compilado entero (un grafo dentro de un grafo).
- **En tu código:** ❌ **NO APLICADO**.
  - **Justificación:** La complejidad de tu dominio (4 agentes) es manejable en un grafo plano. Introducir sub-grafos añadiría una capa innecesaria de ofuscación y haría más difícil trazar el historial de la Máquina de Estados Finitos.

### 2.4. Streaming de Eventos (Event Streaming)
- **Teoría:** LangGraph permite emitir flujos de eventos en tiempo real usando `.stream()` para mostrar a un usuario los pasos que está tomando el agente (al estilo de cómo escribe ChatGPT letra por letra).
- **En tu código:** ❌ **NO APLICADO**.
  - **Justificación:** La interacción es vía WhatsApp o REST API. Los clientes esperan una respuesta final consolidada, no un stream de eventos parciales. Por ello, en `mas_orchestrator.py` (Línea 190) se utiliza `.invoke()` en lugar de `.stream()`, devolviendo el estado final de una sola vez.

---

## 3. Librerías de LangGraph y Dependencias Utilizadas

Para materializar esta teoría, tu código importa y utiliza clases específicas del ecosistema de LangChain/LangGraph. Aquí tienes el detalle exacto de las librerías instaladas que estás invocando:

### 3.1. `from langgraph.graph import StateGraph, START, END`
- **Ubicación:** `mas_orchestrator.py` (Línea 19)
- **Función en el proyecto:** 
  - `StateGraph`: Es la clase constructora base. Se instancia pasándole el esquema de estado (`StateGraph(MASState)`). Ofrece los métodos fundamentales `.add_node()`, `.add_edge()` y `.add_conditional_edges()`.
  - `START` / `END`: Son constantes (tipos protegidos internos de LangGraph) que le indican al motor de ejecución dónde debe comenzar a enrutar el estado inicial y cuándo debe dar por finalizada la ejecución y retornar el diccionario resultante.

### 3.2. `from langgraph.checkpoint.memory import MemorySaver`
- **Ubicación:** `mas_orchestrator.py` (Línea 20)
- **Función en el proyecto:** Es una implementación nativa de *Checkpointer* en memoria RAM (in-memory sqlite). Toma "fotografías" automáticas del `MASState` después de cada paso. Es la librería que permite que tu sistema separe a distintos vendedores de WhatsApp usando su número de teléfono como clave, guardando y recuperando el contexto de su conversación al instante sin mezclar variables.

### 3.3. `from langchain_core.runnables import RunnableConfig`
- **Ubicación:** `mas_orchestrator.py` (Línea 21)
- **Función en el proyecto:** LangGraph está construido por debajo sobre "LangChain Expression Language (LCEL)". Un grafo compilado es técnicamente un `Runnable`. Esta clase `RunnableConfig` te permite tipar fuertemente el diccionario de configuración que le pasas al grafo cuando lo invocas.
  - **Uso:** `config: RunnableConfig = {"configurable": {"thread_id": vendor_phone}}`. Esto le dice al `MemorySaver` qué hilo de conversación específico debe cargar.

### 3.4. `from operator import add`
- **Ubicación:** `state.py` (Línea 22)
- **Función en el proyecto:** Aunque es una librería nativa estándar de Python (no exclusiva de LangChain), es un requerimiento técnico estricto de LangGraph para funcionar como un **Reducer**. Al anotar la lista de mensajes como `Annotated[list, add]`, LangGraph inyecta la función `add` bajo el capó cada vez que un agente devuelve nuevos mensajes, logrando la concatenación en lugar de la sobrescritura.
