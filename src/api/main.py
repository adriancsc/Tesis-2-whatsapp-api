"""
API REST principal del sistema MAS-CIS
FastAPI application con endpoints para e-commerce y administración
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, StreamingResponse
import asyncio
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from src.config import settings
from src.database import get_db_session, Product, Transaction, ChatSession, AgentLog
from src.api.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    StockUpdate, StockResponse,
    TransactionResponse,
    SyncStatusResponse,
    AgentInfoResponse,
    DashboardStats,
    InventoryItem
)
from src.gateway import message_router, whatsapp_gateway
from src.agents import (
    get_store_agent_info, get_coordinator_agent_info, 
    get_sync_agent_info, get_alert_agent_info,
    process_api_stock_update, mas_app, MASState
)
from src.utils.events import connected_clients
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema MAS-CIS API",
    description="API REST para Sistema Multiagente de Sincronización de Inventario",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos (frontend)
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except RuntimeError:
    logger.warning("Directorio frontend no encontrado")


# ============= Health Check =============

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz - Health check"""
    return {
        "service": "MAS-CIS API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/fix-images", tags=["Health"])
async def fix_images():
    """Temporary endpoint to update image URLs for existing products"""
    from src.database.connection import get_db
    from src.database.models import Product
    
    try:
        with get_db() as db:
            p1 = db.query(Product).filter(Product.sku == "POLO-BLANCO").first()
            if p1: p1.image_url = "/images/polo-blanco.png"
            p2 = db.query(Product).filter(Product.sku == "POLO-NEGRO").first()
            if p2: p2.image_url = "/images/polo-negro.png"
            p3 = db.query(Product).filter(Product.sku == "POLO-AZUL").first()
            if p3: p3.image_url = "/images/polo-azul.png"
            db.commit()
            return {"success": True, "message": "Images updated"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/store", tags=["Frontend"])
async def store_page():
    """Servir página de la tienda"""
    return FileResponse("frontend/store.html")


@app.get("/product-detail", tags=["Frontend"])
async def product_detail_page():
    """Servir página de detalle del producto"""
    return FileResponse("frontend/product-detail.html")


@app.get("/product-detail.html", tags=["Frontend"])
async def product_detail_page_html():
    """Alias con .html para detalle del producto"""
    return FileResponse("frontend/product-detail.html")


@app.get("/checkout", tags=["Frontend"])
async def checkout_page():
    """Servir página de checkout con pasarela Izipay simulada"""
    return FileResponse("frontend/checkout.html")


@app.get("/checkout.html", tags=["Frontend"])
async def checkout_page_html():
    """Alias con .html para checkout"""
    return FileResponse("frontend/checkout.html")


@app.get("/order-success", tags=["Frontend"])
async def order_success_page():
    """Servir página de confirmación de orden exitosa"""
    return FileResponse("frontend/order-success.html")


@app.get("/order-success.html", tags=["Frontend"])
async def order_success_page_html():
    """Alias con .html para orden exitosa"""
    return FileResponse("frontend/order-success.html")



# ============= Webhook E-Commerce (Izipay Simulado → MAS) =============

@app.post("/webhook/ecommerce", tags=["Webhooks"])
async def webhook_ecommerce(request: Request):
    """
    Endpoint webhook que recibe órdenes del E-Commerce (Izipay simulado).
    
    Activa el flujo MAS:
    START → SyncAgent (Inbound) → CoordinatorAgent → AlertAgent/END
    
    Payload esperado:
        order_id: str
        variant_sku: str
        quantity: int
        payment_status: str ("approved")
        payment_method: str
        customer: dict (opcional)
        total_amount: float (opcional)
    """
    try:
        payload = await request.json()
        logger.info(f"🌐 Webhook E-Commerce recibido | Orden: {payload.get('order_id', 'UNKNOWN')}")

        # Validar campos obligatorios
        order_id = payload.get("order_id")
        variant_sku = payload.get("variant_sku")
        quantity = payload.get("quantity", 1)
        payment_status = payload.get("payment_status", "")

        if not variant_sku:
            raise HTTPException(status_code=400, detail="variant_sku es requerido")

        if payment_status != "approved":
            logger.warning(f"Pago no aprobado para orden {order_id}: {payment_status}")
            return JSONResponse({"status": "ignored", "reason": "payment_not_approved"}, status_code=200)

        # Construir el estado inicial para el MAS
        initial_state: MASState = {
            "source": "ecommerce",
            "vendor_phone": "ECOMMERCE",
            "raw_text": str(quantity),
            "current_step": "ECOMMERCE_ORDER",
            "action": "sell_web",
            "product_sku": None,
            "product_name": None,
            "variant_id": None,
            "variant_sku": variant_sku,
            "size": None,
            "quantity": int(quantity),
            "response_text": "",
            "requires_coordinator": False,
            "requires_sync": False,
            "requires_alert": False,
            "conflict_detected": False,
            "operation_success": False,
            "size_options": None,
            "messages": [],
            "ecommerce_order_id": order_id,
            "ecommerce_action": "sell_web",
        }

        from langchain_core.runnables import RunnableConfig
        config: RunnableConfig = {"configurable": {"thread_id": f"ecom-{order_id}"}}

        # Invocar el grafo MAS de forma asíncrona
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: mas_app.invoke(initial_state, config))

        success = result.get("operation_success", False)
        conflict = result.get("conflict_detected", False)

        if conflict:
            logger.warning(f"⚔️ Conflicto de stock para orden {order_id}")
            return JSONResponse({
                "status": "conflict",
                "order_id": order_id,
                "detail": "Stock insuficiente. El producto fue comprado simultáneamente."
            }, status_code=409)

        if success:
            logger.info(f"✅ Orden {order_id} procesada exitosamente por el MAS")
            
            # Extraer y enviar alertas proactivas al dueño (si existen)
            from src.config import settings
            if settings.ADMIN_PHONE:
                alerts = [msg.get("content", {}) for msg in result.get("messages", []) if isinstance(msg, dict) and msg.get("performative") == "alert"]
                for alert in alerts:
                    # Enviar el texto de la alerta
                    alert_msg = f"🚨 *ALERTA MAS-CIS*\nOrden Web: {order_id}\nProducto: {alert.get('product_name')} ({alert.get('variant_sku')})\nEstado: "
                    if alert.get('alert_type') == 'stock_depleted':
                        alert_msg += "¡STOCK AGOTADO!"
                    elif alert.get('alert_type') == 'low_stock':
                        alert_msg += f"Stock bajo (Quedan {alert.get('remaining')})"
                    
                    try:
                        from src.gateway import whatsapp_gateway
                        whatsapp_gateway.send_message(to=settings.ADMIN_PHONE, message=alert_msg)
                        logger.info(f"📲 Alerta proactiva enviada al admin ({settings.ADMIN_PHONE})")
                    except Exception as e:
                        logger.error(f"Error enviando alerta proactiva por WhatsApp: {e}")

            return JSONResponse({
                "status": "processed",
                "order_id": order_id,
                "message": "Venta web registrada exitosamente"
            }, status_code=200)

        logger.error(f"❌ El MAS no pudo procesar la orden {order_id}")
        return JSONResponse({
            "status": "error",
            "order_id": order_id,
            "detail": result.get("response_text", "Error interno del sistema")
        }, status_code=422)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en webhook ecommerce: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check detallado"""
    return {
        "status": "healthy",
        "database": "connected",
        "agents": {
            "store": get_store_agent_info(),
            "coordinator": get_coordinator_agent_info()
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ============= Products Endpoints =============

@app.get("/api/products", tags=["Products"])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Obtener lista de productos con sus variantes"""
    from src.database.models import ProductVariant
    
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    
    # Convertir a formato JSON compatible con el frontend
    return {
        "products": [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "description": p.description,
                "base_price": p.base_price,
                "category": p.category,
                "color": p.color,
                "image_url": p.image_url,
                "variants": [
                    {
                        "id": v.id,
                        "sku": v.sku,
                        "size": v.size,
                        "stock_physical": v.stock_physical,
                        "stock_virtual": v.stock_virtual,
                        "stock_total": v.stock_total,
                        "price_adjustment": v.price_adjustment
                    }
                    for v in sorted(p.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))
                ],
                "total_stock": sum(v.stock_total for v in sorted(p.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))),
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in products
        ],
        "total": query.count()
    }


@app.get("/api/products/{sku}", tags=["Products"])
async def get_product(sku: str, db: Session = Depends(get_db_session)):
    """Obtener un producto específico por SKU (puede ser SKU base o SKU de variante)"""
    from src.database.models import ProductVariant
    
    # Primero intentar buscar como producto padre
    product = db.query(Product).filter(Product.sku == sku).first()
    
    if product:
        # Retornar producto con todas sus variantes
        return {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "description": product.description,
            "base_price": product.base_price,
            "category": product.category,
            "color": product.color,
            "image_url": product.image_url,
            "variants": [
                {
                    "id": v.id,
                    "sku": v.sku,
                    "size": v.size,
                    "stock_physical": v.stock_physical,
                    "stock_virtual": v.stock_virtual,
                    "stock_total": v.stock_total,
                    "price_adjustment": v.price_adjustment
                }
                for v in sorted(product.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))
            ],
            "total_stock": sum(v.stock_total for v in sorted(product.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))),
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None
        }
    
    # Si no se encuentra como producto padre, buscar como variante
    variant = db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
    
    if variant:
        # Retornar el producto padre con todas sus variantes
        return {
            "id": variant.product.id,
            "sku": variant.product.sku,
            "name": variant.product.name,
            "description": variant.product.description,
            "base_price": variant.product.base_price,
            "category": variant.product.category,
            "color": variant.product.color,
            "image_url": variant.product.image_url,
            "variants": [
                {
                    "id": v.id,
                    "sku": v.sku,
                    "size": v.size,
                    "stock_physical": v.stock_physical,
                    "stock_virtual": v.stock_virtual,
                    "stock_total": v.stock_total,
                    "price_adjustment": v.price_adjustment
                }
                for v in sorted(variant.product.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))
            ],
            "total_stock": sum(v.stock_total for v in sorted(variant.product.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))),
            "created_at": variant.product.created_at.isoformat() if variant.product.created_at else None,
            "updated_at": variant.product.updated_at.isoformat() if variant.product.updated_at else None
        }
    
    raise HTTPException(status_code=404, detail=f"Producto no encontrado: {sku}")


@app.post("/api/products", response_model=ProductResponse, status_code=201, tags=["Products"])
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db_session)
):
    """Crear un nuevo producto"""
    # Verificar si el SKU ya existe
    existing = db.query(Product).filter(Product.sku == product_data.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU ya existe: {product_data.sku}")
    
    # Crear producto
    product = Product(
        **product_data.model_dump(),
        stock_total=product_data.stock_physical + product_data.stock_virtual
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    logger.info(f"✅ Producto creado: {product.sku}")
    
    return product


@app.put("/api/products/{sku}", response_model=ProductResponse, tags=["Products"])
async def update_product(
    sku: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db_session)
):
    """Actualizar un producto"""
    product = db.query(Product).filter(Product.sku == sku).first()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto no encontrado: {sku}")
    
    # Actualizar campos
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(product)
    
    logger.info(f"✅ Producto actualizado: {sku}")
    
    return product


@app.delete("/api/products/{sku}", status_code=204, tags=["Products"])
async def delete_product(sku: str, db: Session = Depends(get_db_session)):
    """Eliminar un producto"""
    product = db.query(Product).filter(Product.sku == sku).first()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto no encontrado: {sku}")
    
    db.delete(product)
    db.commit()
    
    logger.info(f"✅ Producto eliminado: {sku}")
    
    return None


# ============= Stock Endpoints =============

@app.put("/api/products/{sku}/stock", response_model=StockResponse, tags=["Stock"])
async def update_stock(
    sku: str,
    stock_update: StockUpdate,
    db: Session = Depends(get_db_session)
):
    """Actualizar stock de un producto"""
    # Verificar que el producto existe
    product = db.query(Product).filter(Product.sku == sku).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto no encontrado: {sku}")
    
    # Enviar actualización al grafo de LangGraph
    result = process_api_stock_update(
        action=stock_update.action,
        variant_sku=sku,
        quantity=stock_update.quantity,
        vendor_phone=stock_update.vendor_phone or "API"
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    # Refrescar producto
    db.refresh(product)
    
    return StockResponse(
        success=True,
        product=product,
        transaction_id=result.get("transaction_id"),
        timestamp=datetime.utcnow()
    )


# ============= Transactions Endpoints =============

@app.get("/api/transactions", response_model=List[TransactionResponse], tags=["Transactions"])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    product_sku: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Obtener historial de transacciones"""
    query = db.query(Transaction)
    
    if product_sku:
        product = db.query(Product).filter(Product.sku == product_sku).first()
        if product:
            query = query.filter(Transaction.product_id == product.id)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return transactions


# ============= E-Commerce Webhook =============

@app.post("/webhooks/ecommerce", tags=["Webhooks"])
async def ecommerce_webhook(request: Request, db: Session = Depends(get_db_session)):
    """Recibir órdenes de compra desde E-commerce (CU-04)"""
    try:
        webhook_data = await request.json()
        logger.info(f"🛒 Webhook recibido de E-Commerce: {webhook_data}")
        
        order_id = webhook_data.get("order_id", f"WEB-{int(datetime.utcnow().timestamp())}")
        items = webhook_data.get("items", [])
        
        if not items:
            return JSONResponse(content={"status": "ignored", "reason": "no_items"}, status_code=200)
            
        item = items[0]
        variant_sku = item.get("sku")
        quantity = item.get("quantity", 1)
        
        from langchain_core.runnables import RunnableConfig
        
        initial_state: MASState = {
            "source": "ecommerce",
            "vendor_phone": None,
            "raw_text": "",
            "current_step": "CONFIRM",
            "action": "sell_web",
            "product_sku": None,
            "product_name": None,
            "variant_id": None,
            "variant_sku": variant_sku,
            "size": None,
            "quantity": quantity,
            "response_text": "",
            "requires_coordinator": True,
            "requires_sync": False,
            "requires_alert": False,
            "conflict_detected": False,
            "operation_success": False,
            "size_options": None,
            "messages": [],
            "ecommerce_order_id": order_id,
            "ecommerce_action": "process_order",
        }
        
        config: RunnableConfig = {"configurable": {"thread_id": f"web_{order_id}"}}
        result = mas_app.invoke(initial_state, config)
        
        if result.get("operation_success"):
            return JSONResponse(content={"status": "confirmed", "order_id": order_id}, status_code=200)
        else:
            return JSONResponse(content={"status": "cancelled", "reason": "stock_insuficiente"}, status_code=400)
            
    except Exception as e:
        logger.error(f"Error procesando webhook e-commerce: {e}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


# ============= WhatsApp Webhook =============

@app.get("/webhooks/whatsapp", tags=["Webhooks"])
async def verify_webhook(
    request: Request,
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """Verificar webhook de WhatsApp"""
    result = whatsapp_gateway.verify_webhook(mode, token, challenge)
    
    if result:
        return PlainTextResponse(content=result)
    else:
        raise HTTPException(status_code=403, detail="Verificación fallida")


@app.post("/webhooks/whatsapp", tags=["Webhooks"])
async def whatsapp_webhook(request: Request):
    """Recibir mensajes de WhatsApp"""
    try:
        webhook_data = await request.json()
        
        logger.info("📩 Webhook recibido de WhatsApp")
        
        # Enrutar mensaje
        result = await message_router.route_whatsapp_message(webhook_data)
        
        return JSONResponse(content={"status": "received"}, status_code=200)
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}", exc_info=True)
        return JSONResponse(content={"status": "error"}, status_code=200)


# ============= Compatibility Endpoints =============
# Para soportar la URL sugerida en la guía (/api/whatsapp/webhook) además de la estándar (/webhooks/whatsapp)

@app.get("/api/whatsapp/webhook", tags=["Webhooks"])
async def verify_webhook_alias(
    request: Request,
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """Alias para verificación de webhook"""
    return await verify_webhook(request, mode, token, challenge)


@app.post("/api/whatsapp/webhook", tags=["Webhooks"])
async def whatsapp_webhook_alias(request: Request):
    """Alias para recibir mensajes de WhatsApp"""
    return await whatsapp_webhook(request)


# ============= Store Products Endpoint =============

@app.get("/api/products", tags=["Store"])
async def get_products(
    db: Session = Depends(get_db_session),
    category: Optional[str] = None
):
    """Obtener productos con variantes para la tienda online"""
    from src.database.models import ProductVariant
    
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    
    products = query.all()
    
    result = []
    for p in products:
        variants = [
            {
                "id": v.id,
                "sku": v.sku,
                "size": v.size,
                "stock_physical": v.stock_physical,
                "stock_virtual": v.stock_virtual if hasattr(v, 'stock_virtual') else 0,
                "stock_total": v.stock_total,
            }
            for v in sorted(p.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))
        ]
        
        result.append({
            "id": p.id,
            "sku": p.sku,
            "name": p.name,
            "description": p.description,
            "base_price": p.base_price,
            "category": p.category,
            "color": getattr(p, 'color', None),
            "image_url": getattr(p, 'image_url', None),
            "variants": variants,
            "total_stock": sum(v["stock_total"] for v in variants),
        })
    
    return {"products": result, "total": len(result)}


@app.get("/api/products/{sku}", tags=["Store"])
async def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db_session)
):
    """Obtener un producto específico por SKU"""
    product = db.query(Product).filter(Product.sku == sku).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    variants = [
        {
            "id": v.id,
            "sku": v.sku,
            "size": v.size,
            "stock_physical": v.stock_physical,
            "stock_virtual": v.stock_virtual if hasattr(v, 'stock_virtual') else 0,
            "stock_total": v.stock_total,
        }
        for v in sorted(product.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))
    ]
    
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "base_price": product.base_price,
        "category": product.category,
        "color": getattr(product, 'color', None),
        "image_url": getattr(product, 'image_url', None),
        "variants": variants,
        "total_stock": sum(v["stock_total"] for v in variants),
    }


# ============= Dashboard Endpoints =============

@app.get("/api/dashboard/stats", response_model=DashboardStats, tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db_session)):
    """Obtener estadísticas para el dashboard"""
    from src.database.models import ProductVariant
    
    total_products = db.query(Product).count()
    total_stock = db.query(func.sum(ProductVariant.stock_total)).scalar() or 0
    
    low_stock_products = db.query(ProductVariant).filter(ProductVariant.stock_total < 5).count()
    
    today = datetime.utcnow().date()
    transactions_today = db.query(Transaction).filter(
        func.date(Transaction.created_at) == today
    ).count()
    
    active_sessions = db.query(ChatSession).filter(
        ChatSession.status == "active"
    ).count()
    
    return DashboardStats(
        total_products=total_products,
        total_stock=int(total_stock),
        low_stock_products=low_stock_products,
        transactions_today=transactions_today,
        active_sessions=active_sessions
    )


@app.get("/api/dashboard/inventory", response_model=List[InventoryItem], tags=["Dashboard"])
async def get_inventory_summary(
    db: Session = Depends(get_db_session),
    limit: int = Query(50, ge=1, le=200)
):
    """Obtener resumen de inventario para dashboard"""
    products = db.query(Product).order_by(Product.updated_at.desc()).limit(limit).all()
    
    return [
        InventoryItem(
            sku=p.sku,
            name=p.name,
            stock_physical=sum(v.stock_physical for v in sorted(p.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))) if p.variants else 0,
            stock_virtual=0,  # Ya no usamos stock virtual
            stock_total=sum(v.stock_total for v in sorted(p.variants, key=lambda x: {"S":1, "M":2, "L":3, "XL":4, "XXL":5}.get(x.size.upper(), 99))) if p.variants else 0,
            price=p.base_price,
            category=p.category,
            last_updated=p.updated_at
        )
        for p in products
    ]


@app.get("/api/dashboard/agents", response_model=List[AgentInfoResponse], tags=["Dashboard"])
async def get_agents_info():
    """Obtener información de los agentes"""
    return [
        AgentInfoResponse(**get_store_agent_info()),
        AgentInfoResponse(**get_coordinator_agent_info()),
        AgentInfoResponse(**get_sync_agent_info()),
        AgentInfoResponse(**get_alert_agent_info())
    ]


# ============= Sync Status =============

@app.get("/api/stream/stock", tags=["Sync"])
async def stream_stock(request: Request):
    """Server-Sent Events endpoint para actualizaciones de stock en tiempo real (CU-11)"""
    queue = asyncio.Queue()
    connected_clients.add(queue)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Esperar nueva actualización
                data = await queue.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            connected_clients.remove(queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/sync/status", response_model=SyncStatusResponse, tags=["Sync"])
async def get_sync_status(db: Session = Depends(get_db_session)):
    """Obtener estado de sincronización"""
    # Por ahora, retornar estado básico
    return SyncStatusResponse(
        status="active",
        last_sync=datetime.utcnow(),
        products_synced=db.query(Product).count(),
        pending_operations=0
    )


# ============= Error Handlers =============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de excepciones generales"""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG_MODE
    )
