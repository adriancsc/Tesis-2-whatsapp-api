# Manual de Agentes — MAS-CIS (Verificado contra el Código Fuente)

> [!IMPORTANT]
> Este documento fue generado mediante auditoría directa línea por línea de cada archivo fuente del proyecto. Cada cifra, condición y comportamiento aquí descrito tiene referencia exacta al código real.

---

## Arquitectura General del Grafo (mas_orchestrator.py)

El sistema está construido sobre un `StateGraph` de LangGraph con **4 nodos (agentes)** y **4 funciones de enrutamiento condicional**.

### Topología del flujo

```
START → route_by_source → store_agent | sync_agent

store_agent    → route_after_store       → coordinator_agent | END
sync_agent     → route_after_sync        → coordinator_agent | END
coordinator_agent → route_after_coordinator → alert_agent | sync_agent | END
alert_agent    → (arista simple)         → END
```

### Funciones de Enrutamiento Condicional

| Función | Condición evaluada | Destino si True | Destino si False |
|---|---|---|---|
| `route_by_source` | `state["source"] == "ecommerce"` | `sync_agent` | `store_agent` |
| `route_after_store` | `state["requires_coordinator"] == True` | `coordinator_agent` | `END` |
| `route_after_coordinator` | `state["requires_alert"] == True` | `alert_agent` | — |
| `route_after_coordinator` | `state["requires_sync"] == True` ó `state["conflict_detected"] == True` | `sync_agent` | `END` |
| `route_after_sync` | `state["requires_coordinator"] == True` | `coordinator_agent` | `END` |

> [!NOTE]
> `route_after_coordinator` evalúa primero `requires_alert`. Si es True, **no evalúa `requires_sync`**. La alerta tiene prioridad absoluta sobre la sincronización.

---

## Estado Compartido (state.py — MASState)

El `MASState` es el "porta-documentos" que viaja por todos los nodos. Ningún agente modifica el estado de otro directamente: solo devuelven un diccionario con las claves que quieren actualizar.

### Campos del Estado

| Campo | Tipo | Descripción |
|---|---|---|
| `source` | `str` | Canal de origen: `"whatsapp"`, `"ecommerce"`, `"api"`, `"system"` |
| `vendor_phone` | `Optional[str]` | Número del vendedor. Identifica la sesión en MemorySaver |
| `raw_text` | `str` | Texto crudo recibido del usuario o webhook |
| `current_step` | `str` | Paso actual del FSM del StoreAgent |
| `action` | `Optional[str]` | Acción activa: `sell`, `add`, `remove`, `query`, `daily_summary`, `sell_web` |
| `product_sku` | `Optional[str]` | SKU base del producto (ej: `POLO-BLANCO`) |
| `product_name` | `Optional[str]` | Nombre del producto para mostrar |
| `variant_id` | `Optional[int]` | ID de la variante en BD |
| `variant_sku` | `Optional[str]` | SKU de la variante (ej: `POLO-BLANCO-M`) |
| `size` | `Optional[str]` | Talla seleccionada |
| `quantity` | `Optional[int]` | Cantidad ingresada por el vendedor |
| `size_options` | `Optional[dict]` | Mapa temporal de opciones de talla |
| `messages` | `Annotated[list, add]` | Cola **acumulativa** de mensajes inter-agente (nunca se sobrescribe, solo se suma) |
| `response_text` | `str` | Texto de respuesta final que se enviará al vendedor por WhatsApp |
| `operation_success` | `bool` | Resultado de la transacción del Coordinador |
| `requires_coordinator` | `bool` | **Flag de ruteo:** Store/Sync → Coordinator |
| `requires_sync` | `bool` | **Flag de ruteo:** Coordinator → SyncAgent |
| `requires_alert` | `bool` | **Flag de ruteo:** Coordinator → AlertAgent |
| `conflict_detected` | `bool` | Señal de conflicto de concurrencia (CU-05/06) |
| `ecommerce_order_id` | `Optional[str]` | ID de orden web para CU-04 |
| `ecommerce_action` | `Optional[str]` | Acción del e-commerce: `process_order`, `cancel_order`, `sync_stock` |

### Protocolo de Mensajes Inter-Agente (FIPA ACL simplificado)

Cada mensaje tiene la estructura `AgentMessage` con campos: `performative`, `sender`, `receiver`, `content`, `timestamp`.

Los valores válidos de `performative` son:
- `request` — Solicitud de acción (StoreAgent/SyncAgent → CoordinatorAgent)
- `inform` — Notificación de resultado exitoso
- `refuse` — Rechazo con razón
- `alert` — Alerta proactiva sin solicitud previa (AlertAgent → StoreAgent)
- `confirm` — Confirmación de recepción

---

## 1. Agente de Tienda — store_agent_node.py

**Propósito:** Interfaz conversacional **completamente determinista** con el vendedor vía WhatsApp. No usa LLM. Funciona con menús numerados y un FSM estricto de 5 estados. Los únicos inputs que el sistema espera son números.

**Casos de Uso:** CU-01 (Venta Presencial), CU-02 (Ingreso), CU-03 (Merma), CU-07 (Consultar Inventario), CU-08 (Resumen del Día).

### Catálogo de Productos (hardcoded en el código)

| Número | SKU | Nombre |
|---|---|---|
| `1` | `POLO-BLANCO` | Polo Blanco |
| `2` | `POLO-NEGRO` | Polo Negro |
| `3` | `POLO-AZUL` | Polo Azul |

### Mapa de Acciones

| Número | Acción interna | Nombre visible |
|---|---|---|
| `1` | `sell` | VENTA |
| `2` | `add` | INGRESO |
| `3` | `remove` | MERMA |

### Estados del FSM y Transiciones

| Estado actual | Input válido | Siguiente estado |
|---|---|---|
| `MAIN_MENU` | `1`, `2`, `3` | `SELECT_PRODUCT` |
| `MAIN_MENU` | `4` | → CoordinatorAgent (query) |
| `MAIN_MENU` | `5` | → CoordinatorAgent (daily_summary) |
| `SELECT_PRODUCT` | `1`, `2`, `3` | `SELECT_SIZE` |
| `SELECT_SIZE` | número de talla | `ENTER_QUANTITY` |
| `ENTER_QUANTITY` | número entero | `CONFIRM` |
| `CONFIRM` | `1` (confirmar) | → CoordinatorAgent (transacción) |
| `CONFIRM` | `2` (cancelar) | `MAIN_MENU` |
| **Cualquier estado** | `menu`, `menú`, `salir`, `cancelar`, `hola` | `MAIN_MENU` |
| **Cualquier estado** (excepto `ENTER_QUANTITY`) | `0` | `MAIN_MENU` |

### Validaciones y Parámetros (código real)

**1. Bloqueo total por producto agotado (en `_handle_product_selection`):**
```python
total_stock = sum(v["stock"] for v in size_options.values())
if total_stock == 0:  # Solo aplica para acción "sell"
    # → Deniega. Mensaje: "⛔ OPERACIÓN DENEGADA (Agente de Tienda)"
```
*Solo bloquea ventas. Un Ingreso o Merma nunca activa este bloqueo.*

**2. Indicadores visuales de stock en el menú de productos (en `_build_product_menu`):**
```python
if total_stock == 0:     # → muestra " ❌ (Agotado)"
elif total_stock <= 1 * len(p.variants):  # 1 unidad por talla en promedio
    # → muestra " ⚠️ (Stock bajo)"
else:                    # → no muestra indicador
```

**3. Indicadores visuales de stock en el menú de tallas (en `_build_size_menu`):**
```python
if stock > 1:    # → emoji "✅"
elif stock == 1: # → emoji "⚠️"
else:            # → emoji "❌"
```

**4. Validación de cantidad mínima (en `_handle_quantity_input`):**
```python
quantity = int(raw_text)
if quantity <= 0:
    # → Pide ingresar un número mayor a 0. No avanza de estado.
```

**5. Validación de stock en tiempo real — Solo para `sell` y `remove` (en `_handle_quantity_input`):**
```python
variant = product_repository.find_variant(sku=state["variant_sku"])
stock_available = variant.stock_total if variant else 0
if quantity > stock_available:
    # → Regresa a MAIN_MENU. Mensaje: "❌ STOCK INSUFICIENTE"
    # Muestra: stock disponible y cantidad solicitada
```

**6. Advertencia proactiva de movimiento masivo (en `_build_confirmation`):**
```python
# Aplica solo para "sell" y "remove"
if quantity >= (variant.stock_total * 0.5) and variant.stock_total >= 4:
    # → Inserta advertencia en el mensaje de confirmación:
    # "⚠️ ADVERTENCIA (Agente de Tienda): Esta operación consumirá el 50% o más del stock..."
```
*Condición doble: la cantidad debe ser ≥ 50% del stock Y el stock total debe ser ≥ 4 unidades.*

### Comunicación Inter-Agente que genera

| Situación | Performative | Sender | Receiver | Contenido clave |
|---|---|---|---|---|
| Opción 4 (inventario) | `request` | `store_agent` | `coordinator_agent` | `action: "query"` |
| Opción 5 (resumen) | `request` | `store_agent` | `coordinator_agent` | `action: "daily_summary"` |
| Confirma transacción | `request` | `store_agent` | `coordinator_agent` | `action`, `variant_sku`, `variant_id`, `quantity`, `channel: "physical"` |

---

## 2. Agente Coordinador — coordinator_agent_node.py

**Propósito:** Cerebro transaccional del sistema. Único dueño de la base de datos. Recibe mensajes `request` de Store o Sync, ejecuta la operación con bloqueo ACID y responde con `inform` (éxito) o `refuse` (rechazo).

**Casos de Uso:** CU-01, CU-02, CU-03 (transacciones de stock), CU-04 (venta web), CU-07 (consulta inventario), CU-08 (resumen del día).

### Despacho de Acciones

Lee el último mensaje `request` de la cola y evalúa el campo `action`:

| `action` | Handler ejecutado |
|---|---|
| `query` | `_handle_inventory_query()` |
| `daily_summary` | `_handle_daily_summary()` |
| `sell`, `sell_web`, `add`, `remove` | `_handle_stock_transaction()` |
| cualquier otro | Emite `refuse` con razón `unknown_action` |

### Validaciones y Parámetros en Transacciones (código real)

**1. Límite estricto de cantidad (Hard Limit, primera validación):**
```python
if quantity and quantity > 100:
    # → Emite refuse con razón "quantity_limit_exceeded"
    # Mensaje: "⛔ OPERACIÓN RECHAZADA — no se permite más de 100 unidades en una transacción"
    # Muestra: max_allowed=100, requested=<cantidad pedida>
```

**2. Adquisición de Lock de concurrencia (timeout=3.0 segundos):**
```python
with inventory_lock.acquire(variant_sku, timeout=3.0):
    # Si el lock no se obtiene en 3 segundos → lanza TimeoutError
```

**3. Validación de existencia de variante en BD:**
```python
variant = db.query(ProductVariant).filter(sku == variant_sku).first()
if not variant:
    # → Emite refuse con razón "variant_not_found"
```

**4. Validación por InventoryValidator (validators.py):**
Antes de ejecutar la transacción, el Coordinador llama a `InventoryValidator.validate_stock_operation()`. Las reglas del validador son:
```python
if not product_sku or len(product_sku.strip()) == 0:
    errors.append("SKU de producto no puede estar vacío")
if quantity < 0:
    errors.append("La cantidad no puede ser negativa")
if quantity == 0 and operation != "update":
    errors.append("La cantidad debe ser mayor a 0")
if operation not in ["sell", "add", "update", "remove"]:
    errors.append("Operación inválida")
if operation == "sell" and quantity > current_stock:
    errors.append(f"Stock insuficiente. Disponible: {current_stock}, Solicitado: {quantity}")
# Si hay errores → emite refuse con razón "validation_failed"
```

**5. Ejecución atómica (dentro del lock y la sesión de BD):**
```python
if action in ("sell", "sell_web"):   variant.stock_physical -= quantity
elif action == "add":                variant.stock_physical += quantity
elif action == "remove":             variant.stock_physical -= quantity

# Recálculo del stock total
variant.stock_total = variant.stock_physical + variant.stock_virtual
```
*La tabla `Transaction` se usa como **Kárdex append-only** (RF-04): guarda `previous_stock` y `new_stock` de cada operación.*

**6. Evaluación post-transacción — Trigger de alerta:**
```python
if new_stock == 0:         # → requires_alert=True, tipo: "stock_depleted"
elif new_stock <= 2:       # → requires_alert=True, tipo: "low_stock", remaining=new_stock
```

**7. Evaluación post-transacción — Trigger de sincronización:**
```python
requires_sync = action in ("sell", "add", "remove")
# sell_web NO dispara requires_sync (la web ya sabe el stock)
```

**8. Detección de anomalía de mermas — Solo si `action == "remove"` (función `_check_merma_anomaly`):**
```python
removed_today = SUM(Transaction.quantity WHERE type=REMOVE AND date=hoy)
base = stock_total + removed_today  # Stock que había antes de cualquier merma hoy
if base > 0 and removed_today >= (base * 0.2):  # Umbral: 20% del stock base
    # → alert_data["merma_anomaly"] = {"removed_today": X, "threshold_pct": 20, "message": "..."}
```

**9. Manejo de conflicto de concurrencia:**
```python
except TimeoutError:
    # → conflict_detected=True, operation_success=False
    # Mensaje: "⚠️ CONFLICTO DE CONCURRENCIA — intenta de nuevo en unos segundos"
```

### Funcionalidades Adicionales

**Consulta de Inventario (`_handle_inventory_query`):**
- Hace SELECT de todos los productos con `joinedload` de variantes.
- Clasificación visual: `stock > 1` → ✅, `stock == 1` → ⚠️, `stock == 0` → ❌.
- **Sugerencia proactiva:** Si detecta variantes con stock ≤ 1, agrega automáticamente: `"💡 SUGERENCIA DEL AGENTE: Detecté stock bajo en X variante(s). Te sugiero registrar un Ingreso pronto."` — sin que el usuario lo pida.

**Resumen del Día (`_handle_daily_summary`):**
- Ejecuta 3 queries `SUM/COUNT` filtrando por `created_at >= hoy_inicio AND <= hoy_fin`.
- Calcula: `balance_neto = add_qty - sell_qty - remove_qty`
- **Observación automática:** Si `remove_qty > sell_qty and remove_qty > 0` → agrega: `"⚠️ OBSERVACIÓN DEL AGENTE: Las mermas superan a las ventas hoy. Revisa si hay un problema con la calidad del lote."` — sin que el usuario lo pida.

### Comunicación Inter-Agente que genera

| Situación | Performative | Razón en `content` |
|---|---|---|
| Transacción exitosa | `inform` | `success=True`, `new_stock`, `stock_total`, `alert_data` |
| Límite 100 superado | `refuse` | `quantity_limit_exceeded` |
| Variante no encontrada | `refuse` | `variant_not_found` |
| Falla en validador | `refuse` | `validation_failed` |
| Acción desconocida | `refuse` | `unknown_action` |
| Concurrencia | `refuse` | `concurrency_conflict` |
| Error interno | `refuse` | `internal_error` |

---

## 3. Agente de Sincronización — sync_agent_node.py

**Propósito:** Mantener consistencia entre el Kárdex interno y la plataforma e-commerce externa. Opera en 3 modos según las condiciones del estado.

**Casos de Uso:** CU-04 (Procesar Venta Digital), CU-06 (Cancelación por conflicto), CU-11 (Sincronización Reactiva Post-Venta).

### Modos de Operación (evaluados en orden)

**1. Modo Entrada — Webhook Inbound (CU-04):**
```python
if source == "ecommerce" and not state.get("operation_success", False):
    return _process_ecommerce_order(state)
```
- Lee del estado: `ecommerce_order_id`, `variant_sku`, `quantity`.
- **Validación:** Si `variant_sku` es `None` → devuelve error `operation_success=False` con mensaje `"❌ Orden web {order_id}: SKU no proporcionado."`.
- Si es válido: crea mensaje `request` al CoordinatorAgent con `action: "sell_web"` y activa `requires_coordinator=True`.

**2. Modo Salida — Push Post-Transacción (CU-11):**
```python
if requires_sync:
    return _push_stock_update(state)
```
- Busca el último mensaje `inform` del `coordinator_agent` en la cola.
- Lee de ese mensaje: `variant_sku`, `new_stock`, `stock_total`, `action`.
- Si no encuentra el mensaje inform → devuelve `requires_sync=False` sin hacer nada (no-op).
- En producción: aquí se invocaría la API real del e-commerce (WooCommerce, Shopify, etc.). Actualmente **simulado como exitoso** (`sync_success = True`).
- Enriquece el `response_text` actual añadiendo la nota: `"🔄 Sincronización con e-commerce completada."`.

**3. Modo Conflicto — Cancelación/Reembolso (CU-06):**
```python
if state.get("conflict_detected", False) and source == "ecommerce":
    return _process_ecommerce_cancellation(state)
```
- Simula cancelación en e-commerce y reembolso en pasarela de pagos (actualmente `refund_success = True` simulado).
- Devuelve `conflict_detected=False` (marca el conflicto como resuelto).

**4. No-op:**
- Si ninguna condición aplica → devuelve `requires_sync=False` y registra en log `"Sin acción requerida. No-op."`.

### Parámetros Evaluados

| Parámetro | Valor | Acción disparada |
|---|---|---|
| `source == "ecommerce"` AND `operation_success == False` | True | Modo Entrada (CU-04) |
| `requires_sync` | True | Modo Salida Push (CU-11) |
| `conflict_detected` AND `source == "ecommerce"` | True | Modo Cancelación (CU-06) |
| `variant_sku` | `None` (inbound) | Error, rechaza la orden web |

### Comunicación Inter-Agente que genera

| Situación | Performative | Contenido clave |
|---|---|---|
| Orden web válida | `request` → CoordinatorAgent | `action: "sell_web"`, `order_id`, `variant_sku`, `quantity` |
| Stock sincronizado | `inform` → CoordinatorAgent | `action: "sync_stock"`, `synced_stock`, `timestamp` |
| Cancelación procesada | `inform` → CoordinatorAgent | `action: "cancel_order"`, `order_id`, `status: "refunded"` |

---

## 4. Agente de Alertas — alert_agent_node.py

**Propósito:** Emitir alertas proactivas al vendedor por WhatsApp **sin que este las solicite**, en respuesta a condiciones detectadas por el Coordinador post-transacción.

**Casos de Uso:** CU-09 (Alerta de Stock Bajo), CU-10 (Detección de Anomalías en Mermas).

### Constantes Configurables (hardcoded en el archivo)

```python
LOW_STOCK_THRESHOLD = 2     # Unidades para considerar stock bajo
CRITICAL_STOCK_THRESHOLD = 0  # Stock agotado
```

### Flujo de Ejecución

1. Busca el último mensaje con `performative == "inform"` Y `sender == "coordinator_agent"`.
2. Si no encuentra ese mensaje → devuelve `requires_alert=False` (no-op).
3. Lee `content["alert_data"]` del mensaje. Si es `None` → no-op.
4. Evalúa las condiciones de alerta y genera textos.
5. **Concatena** todos los textos de alerta al `response_text` existente del estado.
6. Registra las alertas en la tabla `AgentLog`.
7. Devuelve `requires_alert=False` (marca la alerta como procesada).

### Condiciones de Alerta Evaluadas

**Alerta Crítica — CU-09 (Stock Agotado):**
```python
if alert_data.get("type") == "stock_depleted":
    # severity: "critical"
    # Mensaje: "🚨 ALERTA CRÍTICA (Agente de Alertas): La variante X talla Y se ha agotado completamente.
    #           Registra un Ingreso (opción 2) lo antes posible."
```

**Alerta de Precaución — CU-09 (Stock Bajo):**
```python
elif alert_data.get("type") == "low_stock":
    remaining = alert_data.get("remaining", 0)
    # severity: "warning"
    # Mensaje: "⚠️ ALERTA (Agente de Alertas): Stock bajo en X talla Y.
    #           Solo queda(n) {remaining} unidad(es). Considera registrar un Ingreso pronto."
```
*Nota: `remaining` es el `new_stock` exacto devuelto por el Coordinador.*

**Alerta de Anomalía — CU-10 (Mermas Inusuales):**
```python
merma_anomaly = alert_data.get("merma_anomaly")
if merma_anomaly:  # Puede acumularse con las alertas anteriores (no es un elif)
    # severity: "warning"
    # Mensaje: "⚠️ ANOMALÍA DETECTADA (Agente de Alertas): {merma_anomaly['message']}
    #           Revisa si hay un problema con la calidad del lote."
```
*Esta condición usa `if` (no `elif`), por lo que puede dispararse junto a una alerta de stock en la misma ejecución.*

### Comunicación Inter-Agente que genera

| Tipo de alerta | Performative | Sender | Receiver | `severity` |
|---|---|---|---|---|
| Stock agotado | `alert` | `alert_agent` | `store_agent` | `"critical"` |
| Stock bajo | `alert` | `alert_agent` | `store_agent` | `"warning"` |
| Merma anómala | `alert` | `alert_agent` | `store_agent` | `"warning"` |

---

## Módulo de Validación — validators.py (InventoryValidator)

Usado internamente por el Coordinador. Las reglas en orden de evaluación:

| Regla | Condición | Error generado |
|---|---|---|
| SKU vacío | `not product_sku or len(product_sku.strip()) == 0` | "SKU de producto no puede estar vacío" |
| Cantidad negativa | `quantity < 0` | "La cantidad no puede ser negativa" |
| Cantidad cero | `quantity == 0 and operation != "update"` | "La cantidad debe ser mayor a 0" |
| Operación inválida | `operation not in ["sell", "add", "update", "remove"]` | "Operación inválida. Debe ser una de: ..." |
| Stock insuficiente | `operation == "sell" and quantity > current_stock` | "Stock insuficiente. Disponible: X, Solicitado: Y" |
