# Fichas Técnicas de Casos de Uso — Sistema Multiagente

---

## CU-01: Registrar Venta Presencial vía WhatsApp

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-01: Registrar Venta Presencial vía WhatsApp |
| **Actor Primario** | Vendedor (Microempresario) |
| **Actores Secundarios** | Agente de Tienda, Agente Coordinador |
| **Descripción** | El vendedor registra la salida de mercadería por una venta presencial realizada en su stand, seleccionando el producto, talla y cantidad a través de un menú conversacional en WhatsApp. El sistema descuenta el stock físico del Kárdex centralizado. |
| **Precondiciones** | 1. El vendedor tiene WhatsApp activo y su número está registrado en el sistema. 2. Existen productos con variantes y stock disponible en la base de datos. 3. El sistema multiagente está desplegado y operativo. |
| **Flujo Principal (Nominal)** | 1. El vendedor envía un mensaje al número de WhatsApp Business del sistema. 2. El Agente de Tienda presenta el menú principal con cinco opciones. 3. El vendedor selecciona la opción "1 - Registrar Venta". 4. El Agente de Tienda consulta la base de datos y muestra el catálogo de productos con advertencias visuales de inventario (⚠️ Stock bajo / ❌ Agotado) si aplica. 5. El vendedor selecciona el producto (ej. "1" para Polo Blanco). 6. El Agente de Tienda consulta las variantes del producto y muestra las tallas con su stock actual (✅/⚠️/❌). 7. El vendedor selecciona la talla. 8. El Agente de Tienda solicita la cantidad de unidades vendidas. 9. El vendedor ingresa la cantidad. 10. El Agente de Tienda presenta un resumen de confirmación con los datos de la operación. 11. El vendedor confirma enviando el número "1". 12. El Agente de Tienda crea un mensaje de solicitud dirigido al Agente Coordinador con los datos de la venta. 13. El Agente Coordinador adquiere el bloqueo del producto mediante el Administrador de Bloqueos, valida la operación contra las reglas de negocio, y ejecuta el descuento en la base de datos. 14. El Agente Coordinador registra la transacción en el Kárdex y responde con un mensaje de éxito. 15. El sistema presenta la confirmación al vendedor con el stock anterior, el stock nuevo y el stock total actualizado. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si el producto seleccionado está agotado en todas sus tallas, el Agente de Tienda deniega la operación autónomamente con un mensaje de "OPERACIÓN DENEGADA" y regresa al menú principal. **FA-02:** Si la cantidad ingresada excede el stock disponible de la talla, el Agente de Tienda rechaza la operación mostrando el stock actual y regresa al menú principal. **FA-03:** Si la cantidad supera las 1000 unidades por transacción, el Agente Coordinador rechaza la solicitud. **FA-04:** Si otro proceso está actualizando el mismo producto simultáneamente, el Agente Coordinador informa del conflicto de concurrencia y solicita reintentar. **FA-05:** Si el vendedor escribe "0", "menu", "salir" o "cancelar" en cualquier paso, el Agente de Tienda reinicia el flujo al menú principal. **FA-06:** Si el vendedor selecciona "2 - Cancelar" en la pantalla de confirmación, la operación se cancela y se regresa al menú principal. |
| **Postcondiciones** | 1. El stock físico de la talla seleccionada ha sido decrementado en la cantidad indicada. 2. Se ha registrado una entrada en el historial de transacciones con trazabilidad completa (stock anterior, stock nuevo, canal, teléfono del vendedor, fecha/hora). 3. Se ha registrado la actividad del Agente Coordinador en la bitácora de logs. 4. Si el stock resultante es muy bajo o se agota, se desencadena el proceso de alerta (CU-09 o CU-10). 5. Se desencadena el proceso de sincronización con la web (CU-12). |

---

## CU-02: Registrar Abastecimiento de Mercadería vía WhatsApp

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-02: Registrar Abastecimiento de Mercadería vía WhatsApp |
| **Actor Primario** | Vendedor (Microempresario) |
| **Actores Secundarios** | Agente de Tienda, Agente Coordinador |
| **Descripción** | El vendedor registra la entrada de nuevos productos provenientes del taller o proveedor, incrementando el stock físico de la talla seleccionada en el Kárdex centralizado. |
| **Precondiciones** | 1. El vendedor tiene acceso al sistema vía WhatsApp. 2. El producto y sus tallas están registrados en la base de datos. |
| **Flujo Principal (Nominal)** | 1. El vendedor accede al menú principal del sistema. 2. El vendedor selecciona la opción "2 - Registrar Ingreso". 3. El Agente de Tienda muestra el catálogo de productos con indicadores de stock. 4. El vendedor selecciona el producto. 5. El Agente de Tienda muestra las tallas disponibles con su stock actual. 6. El vendedor selecciona la talla. 7. El Agente de Tienda solicita la cantidad de unidades que ingresaron. 8. El vendedor ingresa la cantidad. 9. El Agente de Tienda presenta el resumen de confirmación. 10. El vendedor confirma la operación. 11. El Agente de Tienda envía un mensaje de solicitud de ingreso al Agente Coordinador. 12. El Agente Coordinador adquiere el bloqueo del producto, valida la operación, incrementa el stock físico de la talla, recalcula el stock total y registra la entrada en el Kárdex. 13. El sistema presenta la confirmación con el stock actualizado. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si la cantidad ingresada no es numérica o es menor o igual a cero, el Agente de Tienda solicita un valor válido. **FA-02:** Si la cantidad supera las 1000 unidades, el Agente Coordinador rechaza la solicitud. **FA-03:** El vendedor puede cancelar la operación en cualquier paso escribiendo "0" o "cancelar". |
| **Postcondiciones** | 1. El stock físico de la talla ha sido incrementado en la cantidad indicada. 2. Se ha registrado una transacción de ingreso en el Kárdex. 3. Se desencadena el proceso de sincronización web (CU-12). |

---

## CU-03: Registrar Merma vía WhatsApp

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-03: Registrar Merma vía WhatsApp |
| **Actor Primario** | Vendedor (Microempresario) |
| **Actores Secundarios** | Agente de Tienda, Agente Coordinador |
| **Descripción** | El vendedor reporta prendas dañadas, falladas o defectuosas, descontando las unidades afectadas del inventario y registrando la operación como merma en el historial transaccional del Kárdex. |
| **Precondiciones** | 1. El vendedor tiene acceso al sistema vía WhatsApp. 2. Existen unidades disponibles en el stock de la talla a reportar. |
| **Flujo Principal (Nominal)** | 1. El vendedor accede al menú principal. 2. El vendedor selecciona la opción "3 - Registrar Merma". 3. El Agente de Tienda muestra el catálogo de productos. 4. El vendedor selecciona el producto afectado. 5. El Agente de Tienda muestra las tallas con stock disponible. 6. El vendedor selecciona la talla. 7. El Agente de Tienda solicita la cantidad de unidades con falla. 8. El vendedor ingresa la cantidad. 9. El Agente de Tienda presenta el resumen de confirmación. 10. El vendedor confirma la operación. 11. El Agente Coordinador adquiere el bloqueo del producto, ejecuta el descuento del stock físico y registra la transacción como merma. 12. El Agente Coordinador invoca la función de detección de anomalías evaluando las mermas del día para dicho producto. 13. El sistema presenta la confirmación con el stock actualizado. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si la cantidad de merma excede el stock disponible, el Agente de Tienda rechaza la operación y muestra el stock actual. **FA-02:** Si el Agente Coordinador detecta que las mermas del día superan el umbral de seguridad, se desencadena el CU-11 (detección de anomalía). **FA-03:** Si el stock resultante es crítico o agotado, se activan los procesos de alerta (CU-09 o CU-10). |
| **Postcondiciones** | 1. El stock físico ha sido decrementado por la merma reportada. 2. Se ha registrado una transacción de merma en el Kárdex. 3. Si aplica, se emiten alertas de anomalía o stock crítico de manera autónoma. |

---

## CU-04: Recepción de Orden Web

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-04: Recepción de Orden Web |
| **Actor Primario** | Comprador (Cliente Web) |
| **Actores Secundarios** | Agente de Sincronización, Agente Coordinador, Portal de Ventas Web |
| **Descripción** | Un comprador realiza una compra a través del portal de ventas web. El portal envía los datos de la orden al sistema multiagente. El Agente de Sincronización recibe el evento y delega la ejecución de la transacción al Agente Coordinador de forma autónoma, sin intervención del vendedor. |
| **Precondiciones** | 1. El portal de ventas web está operativo y conectado al sistema. 2. El producto y la talla solicitados existen en la base de datos. 3. Existe stock disponible para la talla solicitada. |
| **Flujo Principal (Nominal)** | 1. El comprador completa el proceso de compra en el portal web. 2. El portal notifica al sistema multiagente sobre la nueva orden. 3. El Agente de Sincronización valida los datos de la compra y envía una solicitud de venta al Agente Coordinador. 4. El Agente de Sincronización registra la recepción de la orden en la bitácora de actividad. 5. El Agente Coordinador adquiere el bloqueo del producto, valida el stock disponible y ejecuta el descuento en la base de datos. 6. El Agente Coordinador registra la transacción en el Kárdex indicando que el canal es "web" y confirma el éxito al Agente de Sincronización. 7. El sistema retorna una respuesta afirmativa al portal web. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si el producto no existe en la base de datos, el Agente Coordinador rechaza la operación. **FA-02:** Si el stock es insuficiente para cubrir la venta web, el Agente Coordinador rechaza la operación y se activa el CU-06 (cancelación con devolución). **FA-03:** Si existe un conflicto de concurrencia inmanejable, el Agente Coordinador rechaza la orden y se activa el CU-06. |
| **Postcondiciones** | 1. El stock físico ha sido decrementado por la venta web. 2. La transacción ha sido registrada en el Kárdex con canal "web". 3. Si el stock resultante es crítico, se desencadenan las alertas para notificar al vendedor. |

---

## CU-05: Se vende en ambos canales al mismo tiempo

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-05: Se vende en ambos canales al mismo tiempo |
| **Actor Primario** | Vendedor (vía WhatsApp) y Comprador (vía Portal Web) simultáneamente |
| **Actores Secundarios** | Agente de Tienda, Agente de Sincronización, Agente Coordinador, Administrador de Bloqueos |
| **Descripción** | Una venta presencial (WhatsApp) y una venta digital (portal web) intentan descontar stock de la misma talla de producto en el mismo instante. El sistema debe garantizar la integridad del dato mediante un mecanismo de bloqueos, procesando una transacción a la vez y evitando condiciones de carrera. |
| **Precondiciones** | 1. El producto tiene stock disponible. 2. El sistema multiagente recibe peticiones de venta para el mismo artículo de forma simultánea desde distintos canales. |
| **Flujo Principal (Nominal)** | 1. El vendedor confirma una venta presencial vía WhatsApp, mientras el portal web envía simultáneamente una orden de compra para el mismo artículo. 2. Ambas peticiones llegan al Agente Coordinador, el cual solicita el bloqueo exclusivo del artículo al Administrador de Bloqueos. 3. El Administrador concede el acceso al primer proceso en llegar. 4. El primer proceso ejecuta la transacción (valida stock, descuenta, y registra) y luego libera el artículo. 5. El segundo proceso, que esperaba su turno, toma el control del artículo. 6. El segundo proceso verifica el stock actualizado por la primera venta, confirma que aún hay unidades y ejecuta su propia transacción. 7. Ambas ventas se completan exitosamente sin corromper los datos. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si el segundo proceso no logra acceder al artículo dentro de un tiempo de gracia, el sistema reporta un conflicto de concurrencia y pide al usuario reintentar. **FA-02:** Si la primera venta consumió todo el stock, el segundo proceso detectará la falta de inventario y rechazará la operación. Si la segunda era una venta web, se activa el CU-06 (devolución). |
| **Postcondiciones** | 1. Ambas transacciones (o al menos la primera) han sido procesadas con datos íntegros, sin generar sobreventas ni stock negativo. 2. Cada movimiento tiene su propio registro ordenado en el Kárdex. |

---

## CU-06: Devolución de dinero por cancelación de pedido

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-06: Devolución de dinero por cancelación de pedido |
| **Actor Primario** | Sistema Multiagente (Autónomo — Agente de Sincronización) |
| **Actores Secundarios** | Agente Coordinador, Portal de Ventas Web |
| **Descripción** | Cuando una orden web es rechazada (por falta de stock tras una venta presencial o conflicto de concurrencia), el Agente de Sincronización inicia autónomamente el proceso de cancelación y solicita el reembolso a través de la API del portal de ventas web. |
| **Precondiciones** | 1. Se ha recibido una orden de compra web. 2. El Agente Coordinador ha rechazado procesarla y ha alertado de un conflicto. |
| **Flujo Principal (Nominal)** | 1. El Agente Coordinador rechaza la orden web y activa la señal de conflicto. 2. El sistema detecta el problema y delega la mitigación al Agente de Sincronización. 3. El Agente de Sincronización invoca la API del portal de ventas web solicitando la cancelación de la orden y el reembolso al cliente. 4. El portal confirma la cancelación. 5. Se registra la cancelación en la bitácora de actividad. 6. El Agente de Sincronización confirma al Coordinador que el conflicto fue resuelto. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si la API del portal web no responde o rechaza el reembolso, la operación queda en estado "pendiente" en los registros para que el vendedor lo procese manualmente luego. |
| **Postcondiciones** | 1. La orden figura como cancelada en la plataforma web. 2. El reembolso ha sido procesado exitosamente (o marcado como pendiente). 3. El incidente queda registrado en la bitácora de logs. |

---

## CU-07: Consultar Inventario

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-07: Consultar Inventario |
| **Actor Primario** | Vendedor (Microempresario) |
| **Actores Secundarios** | Agente de Tienda, Agente Coordinador |
| **Descripción** | El vendedor solicita un reporte del estado actual de todos los productos, visualizando el stock disponible por talla junto a indicadores visuales de disponibilidad. |
| **Precondiciones** | 1. El vendedor tiene acceso al sistema vía WhatsApp. 2. Existen productos registrados. |
| **Flujo Principal (Nominal)** | 1. El vendedor accede al menú principal. 2. El vendedor selecciona la opción "4 - Ver Inventario". 3. El Agente de Tienda delega la petición de consulta al Agente Coordinador. 4. El Agente Coordinador ejecuta una lectura segura sobre la base de datos asegurándose de no interferir con ventas en curso. 5. Se genera un reporte formateado que incluye cada producto, sus tallas y su respectivo stock, marcándolos visualmente (✅ disponible, ⚠️ bajo, ❌ agotado). 6. Si hay productos con escasez, el Agente Coordinador añade una sugerencia proactiva recomendando un abastecimiento. 7. El sistema presenta el inventario completo al vendedor por WhatsApp. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si el inventario está totalmente vacío, el sistema informa "No hay productos registrados en el inventario". |
| **Postcondiciones** | 1. El vendedor recibe la información en su dispositivo. 2. La consulta queda registrada en la bitácora del sistema. |

---

## CU-08: Resumen Transaccional del Día

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-08: Resumen Transaccional del Día |
| **Actor Primario** | Vendedor (Microempresario) |
| **Actores Secundarios** | Agente de Tienda, Agente Coordinador |
| **Descripción** | El vendedor solicita un consolidado de los movimientos de inventario ocurridos en el día en curso, obteniendo las cantidades totales de ventas, ingresos, mermas y el balance neto de unidades. |
| **Precondiciones** | 1. El vendedor tiene acceso al sistema vía WhatsApp. |
| **Flujo Principal (Nominal)** | 1. El vendedor accede al menú principal. 2. El vendedor selecciona la opción "5 - Resumen del Día". 3. El Agente de Tienda solicita la información al Agente Coordinador. 4. El Agente Coordinador calcula el rango de horas del día actual y extrae los totales agrupados por tipo de operación (ventas, ingresos, mermas) del Kárdex. 5. Se calcula el balance neto de mercadería. 6. El Agente genera un reporte amigable resumiendo estas métricas. 7. El resumen se envía al WhatsApp del vendedor. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si no hubo movimientos en el día, el sistema aclara que no hay registros aún. **FA-02:** Si el número de unidades mermadas supera a las unidades vendidas en el día, el Agente Coordinador emite una advertencia al vendedor instándole a revisar la calidad del lote. |
| **Postcondiciones** | 1. El vendedor se informa del desempeño operativo del día. 2. La petición de reporte queda guardada en la bitácora. |

---

## CU-09: Alerta Proactiva de Stock Bajo

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-09: Alerta Proactiva de Stock Bajo |
| **Actor Primario** | Sistema Multiagente (Autónomo — Agente de Alertas) |
| **Actores Secundarios** | Agente Coordinador, Vendedor (receptor de la alerta) |
| **Descripción** | Tras concretar una venta o reportar una merma, si las existencias de la talla descienden a un umbral crítico (1 o 2 unidades), el Agente de Alertas envía autónomamente una advertencia al vendedor, fomentando el reabastecimiento temprano. |
| **Precondiciones** | 1. Se concretó una transacción que redujo el inventario. 2. El stock restante del producto quedó en niveles bajos (≤ 2). |
| **Flujo Principal (Nominal)** | 1. El Agente Coordinador finaliza la transacción y evalúa que el stock ha caído al umbral de advertencia. 2. El sistema notifica internamente al Agente de Alertas sobre la situación. 3. El Agente de Alertas construye un mensaje preventivo sugiriendo registrar un ingreso a la brevedad. 4. La alerta se anexa automáticamente al final del mensaje de confirmación de la venta que se le entrega al vendedor. 5. El vendedor lee la alerta preventiva directamente en su WhatsApp. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si el stock no es considerado bajo, la alerta simplemente no se genera. |
| **Postcondiciones** | 1. El vendedor queda notificado del riesgo de desabastecimiento inminente. 2. El envío de la alerta proactiva se registra en la bitácora del sistema. |

---

## CU-10: Alerta Proactiva de Stock Agotado

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-10: Alerta Proactiva de Stock Agotado |
| **Actor Primario** | Sistema Multiagente (Autónomo — Agente de Alertas) |
| **Actores Secundarios** | Agente Coordinador, Vendedor (receptor de la alerta) |
| **Descripción** | Tras una transacción de salida (venta/merma), si las existencias de un producto llegan exactamente a cero, el Agente de Alertas reacciona de inmediato enviando una notificación crítica al vendedor. |
| **Precondiciones** | 1. Se concretó una transacción de reducción de inventario. 2. El stock restante es cero unidades (agotamiento total). |
| **Flujo Principal (Nominal)** | 1. El Agente Coordinador procesa la salida de mercadería y detecta que el producto se ha quedado sin unidades. 2. El sistema activa al Agente de Alertas de forma urgente. 3. El Agente de Alertas redacta una notificación crítica destacando que el producto está 100% agotado e insta a reabastecerlo de urgencia para evitar pérdida de ventas. 4. La alerta crítica se añade al reporte de transacción y se envía al vendedor. |
| **Flujos Alternativos / Excepciones** | **FA-01:** No hay flujo alternativo; esta acción es completamente reactiva al llegar a cero unidades. |
| **Postcondiciones** | 1. El vendedor es consciente del quiebre total de stock al instante. 2. La alerta crítica queda registrada en el sistema. |

---

## CU-11: Detección Autónoma de Anomalías (Mermas)

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-11: Detección Autónoma de Anomalías (Mermas) |
| **Actor Primario** | Sistema Multiagente (Autónomo — Agente Coordinador + Agente de Alertas) |
| **Actores Secundarios** | Vendedor (receptor de la alerta) |
| **Descripción** | Cada vez que el vendedor reporta prendas falladas (merma), el Agente Coordinador evalúa si el acumulado de fallas del día supera el 30% del stock base. De ser así, deduce un problema de calidad sistémico y el Agente de Alertas previene al vendedor. |
| **Precondiciones** | 1. El vendedor registró una nueva merma. 2. Existen mermas previas reportadas para el mismo artículo durante el mismo día. |
| **Flujo Principal (Nominal)** | 1. El Agente Coordinador guarda el registro de la nueva merma en la base de datos. 2. Autónomamente, analiza el historial del día y comprueba que la suma de mermas supera el 30% del inventario original del día para ese producto. 3. Identifica esta situación como una anomalía e informa al Agente de Alertas. 4. El Agente de Alertas redacta una advertencia sobre la cantidad inusualmente alta de fallas, sugiriendo una inspección de calidad al lote. 5. La advertencia es despachada al vendedor por WhatsApp. |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si la proporción de mermas se mantiene debajo del 30%, el sistema no detecta anomalías de calidad y no emite advertencias. |
| **Postcondiciones** | 1. El vendedor recibe información crucial para la toma de decisiones sobre su proveedor o producción. 2. El patrón anómalo se documenta en los registros para futuras auditorías. |

---

## CU-12: Sincronización post venta

| Campo | Detalle |
|---|---|
| **Ficha Técnica de Caso de Uso** | CU-12: Sincronización post venta |
| **Actor Primario** | Sistema Multiagente (Autónomo — Agente de Sincronización) |
| **Actores Secundarios** | Agente Coordinador, Portal de Ventas Web |
| **Descripción** | Cada vez que ocurre un cambio en el inventario local (ya sea por venta, ingreso o merma), el Agente de Sincronización replica de inmediato este nuevo saldo en la tienda online para mantener la coherencia multicanal e impedir la venta de productos sin existencias reales. |
| **Precondiciones** | 1. Se procesó un cambio de stock exitoso en la base de datos centralizada. |
| **Flujo Principal (Nominal)** | 1. El Agente Coordinador finaliza una modificación de inventario y activa el proceso de sincronización. 2. El Agente de Sincronización toma la posta, lee el nuevo total de unidades disponibles y el código del artículo. 3. El Agente invoca de fondo los servicios del portal web para actualizar la disponibilidad del catálogo online. 4. Al recibir la confirmación de la tienda web, el Agente registra que ambos mundos (físico y digital) están alineados. 5. Añade una pequeña nota de éxito en el mensaje que recibe el vendedor ("🔄 Sincronización web completada"). |
| **Flujos Alternativos / Excepciones** | **FA-01:** Si la tienda web se encuentra caída o hay problemas de red, el Agente de Sincronización registra un error en la bitácora y programa un reintento futuro para restaurar la coherencia. |
| **Postcondiciones** | 1. El stock exhibido a los clientes en la página web es idéntico al Kárdex de la microempresa. 2. La exitosa sincronización queda registrada con fecha y hora exacta. |
