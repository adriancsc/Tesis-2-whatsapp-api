# Casos de Uso Implementados (MAS-CIS)

Este documento detalla los 11 Casos de Uso (CU) que están actualmente implementados y plenamente funcionales en tu Sistema Multiagente construido con LangGraph, clasificados por su naturaleza operativa.

---

## 1. Operaciones Físicas Interactivas (WhatsApp)
*Iniciadas por el Vendedor de Tienda a través de un canal conversacional. Orquestadas inicialmente por el `store_agent`.*

* **CU-01: Registro de Venta Física**
  * **Flujo:** El vendedor selecciona Producto → Talla → Cantidad.
  * **Agentes Involucrados:** Store → Coordinator (→ Sync → Alert).
  * **Descripción:** Disminuye el stock físico y virtual, registra la salida en el Kárdex, y dispara la sincronización con el E-commerce.

* **CU-02: Registro de Ingreso de Mercadería**
  * **Flujo:** El vendedor reporta la llegada de nuevo inventario.
  * **Agentes Involucrados:** Store → Coordinator (→ Sync).
  * **Descripción:** Aumenta el stock físico y virtual, registra el ingreso, y actualiza la cantidad en la plataforma web.

* **CU-03: Registro de Merma (Daños/Pérdidas)**
  * **Flujo:** El vendedor reporta inventario defectuoso que debe sacarse de circulación.
  * **Agentes Involucrados:** Store → Coordinator (→ Sync).
  * **Descripción:** Disminuye el stock y lo registra con tipología de "remove", alertando a la web de que esas unidades ya no son vendibles.

* **CU-07: Consulta Interactiva de Inventario**
  * **Flujo:** El vendedor presiona la opción "4" para ver el catálogo.
  * **Agentes Involucrados:** Store → Coordinator.
  * **Descripción:** El Coordinador lee la BD en tiempo real y devuelve el stock de todas las tallas. Si hay stock bajo, el sistema inyecta una "Sugerencia Proactiva" recomendando un ingreso.

* **CU-08: Resumen Transaccional del Día**
  * **Flujo:** El vendedor presiona la opción "5".
  * **Agentes Involucrados:** Store → Coordinator.
  * **Descripción:** Realiza consultas agregadas (`SUM`) de todas las entradas, salidas y mermas ocurridas en las últimas 24 horas, emitiendo un balance neto automático.

---

## 2. Operaciones Digitales de Sincronización (E-commerce)
*Iniciadas por Webhooks del E-commerce o como efectos colaterales de operaciones físicas. Orquestadas por el `sync_agent`.*

* **CU-04: Recepción de Orden Web (Inbound)**
  * **Flujo:** Un cliente compra en la web y el webhook dispara el MAS.
  * **Agentes Involucrados:** Sync → Coordinator.
  * **Descripción:** Captura la orden remota y ordena al Coordinador que separe el inventario inmediatamente, reduciendo el stock físico.

* **CU-11: Sincronización Post-Venta (Outbound)**
  * **Flujo:** El Coordinador aprueba una venta física o merma.
  * **Agentes Involucrados:** Coordinator → Sync.
  * **Descripción:** El SyncAgent recibe la notificación de que el stock cambió localmente, y hace una llamada a la API del E-commerce para que el stock en la web sea idéntico al de la tienda física.

---

## 3. Resolución Concurrente y Conflictos (ACID)
*Casos de uso puramente sistémicos que protegen la integridad de los datos.*

* **CU-05: Bloqueo y Detección de Concurrencia**
  * **Flujo:** Dos transacciones intentan comprar la última unidad al mismo exacto milisegundo.
  * **Agentes Involucrados:** Coordinator.
  * **Descripción:** Utiliza un `Lock` con timeout (3 segundos). Si la transacción no puede adquirir el recurso, levanta la bandera de conflicto (`conflict_detected = True`) y protege la base de datos de una sobreventa.

* **CU-06: Resolución de Conflicto y Reembolso Automático**
  * **Flujo:** El Coordinador detecta el CU-05 proveniente de una orden web que chocó con una venta física.
  * **Agentes Involucrados:** Coordinator → Sync.
  * **Descripción:** Al fallar la compra por falta de stock (debido a la colisión), el SyncAgent toma el control para emitir una solicitud de reembolso automático hacia la pasarela de pagos web (Cancelación Inteligente).

---

## 4. Monitoreo Autónomo y Proactividad (MAS puro)
*Casos de uso iniciados **por el propio sistema sin que nadie se lo pida**, demostrando la autonomía de los agentes.*

* **CU-09: Alerta Proactiva de Stock Bajo y Agotado**
  * **Flujo:** Post-venta, si el `new_stock` cae a 2 o a 0.
  * **Agentes Involucrados:** Coordinator → Alert.
  * **Descripción:** El AlertAgent irrumpe en la conversación de WhatsApp con un mensaje 🚨 urgente, informando al vendedor que una talla específica está a punto de agotarse o se agotó por completo.

* **CU-10: Detección Autónoma de Anomalías (Patrón de Mermas)**
  * **Flujo:** Post-merma, el sistema evalúa el historial del día.
  * **Agentes Involucrados:** Coordinator → Alert.
  * **Descripción:** Si las unidades reportadas como dañadas/perdidas igualan o superan el **20%** del stock base en un solo día, el AlertAgent lanza una advertencia sobre comportamiento inusual en la calidad del lote o posible pérdida sospechosa.
