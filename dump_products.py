from src.database.connection import SessionLocal
from src.database.models import Product, ProductVariant

with open("products_dump_utf8.txt", "w", encoding="utf-8") as f:
    try:
        db = SessionLocal()
        f.write("📋 Checking Product Table...\n")
        products = db.query(Product).all()
        for p in products:
            f.write(f"ID: {p.id} | Name: '{p.name}' | SKU: '{p.sku}' | Color: {getattr(p, 'color', 'N/A')}\n")
            
        f.write("\n📋 Checking ProductVariant Table...\n")
        try:
            variants = db.query(ProductVariant).all()
            for v in variants:
                f.write(f"ID: {v.id} | SKU: '{v.sku}' | Size: '{v.size}' | Parent: {v.product_id}\n")
        except Exception as e:
            f.write(f"Variants Error: {e}\n")

        db.close()
    except Exception as e:
        f.write(f"❌ Error: {e}\n")
