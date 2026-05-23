"""
Script para listar productos con sus variantes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_db
from src.database.models import Product, ProductVariant

def list_products_with_variants():
    """Listar todos los productos con sus variantes"""
    with get_db() as db:
        products = db.query(Product).all()
        
        print("\n" + "=" * 70)
        print(f"📦 PRODUCTOS EN BASE DE DATOS: {len(products)}")
        print("=" * 70)
        
        total_variants = 0
        total_stock = 0
        
        for product in products:
            print(f"\n🏷️  {product.name} ({product.sku})")
            print(f"   Categoría: {product.category}")
            print(f"   Color: {product.color}")
            print(f"   Precio base: S/ {product.base_price:.2f}")
            print(f"   Variantes:")
            
            product_total_stock = 0
            for variant in product.variants:
                total_variants += 1
                total_stock += variant.stock_total
                product_total_stock += variant.stock_total
                
                print(f"      - Talla {variant.size:5s}: {variant.stock_total:3d} unidades "
                      f"({variant.stock_physical} físico, {variant.stock_virtual} virtual) "
                      f"[{variant.sku}]")
            
            print(f"   📊 Stock total del producto: {product_total_stock} unidades")
        
        print("\n" + "=" * 70)
        print(f"📊 RESUMEN GENERAL:")
        print(f"   Total productos: {len(products)}")
        print(f"   Total variantes: {total_variants}")
        print(f"   Stock total: {total_stock} unidades")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    list_products_with_variants()
