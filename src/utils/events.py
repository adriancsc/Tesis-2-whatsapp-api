import asyncio
import json

connected_clients = set()

def broadcast_stock_update(variant_sku: str, new_stock: int):
    data = json.dumps({'variant_sku': variant_sku, 'new_stock': new_stock})
    for q in list(connected_clients):
        q.put_nowait(data)
