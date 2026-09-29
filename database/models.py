from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    full_name: str
    role: str  # 'admin' or 'caissier'
    is_active: bool = True
    created_at: Optional[str] = None

@dataclass
class Product:
    id: int
    barcode: str
    name: str
    brand: Optional[str]
    category: str
    purchase_price: float
    sale_price: float
    vat_rate: float
    stock_qty: int
    min_stock_alert: int
    expiry_date: Optional[str]
    supplier_id: Optional[int]
    is_active: bool = True
    created_via_po_id: Optional[int] = None
    supplier_name: Optional[str] = None

@dataclass
class StockMovement:
    id: int
    product_id: int
    movement_type: str  # 'reception', 'vente', 'ajustement', 'inventaire', 'perte_casse'
    qty: int
    old_stock: int
    new_stock: int
    unit_price: Optional[float]
    reason: Optional[str]
    user_id: Optional[int]
    created_at: Optional[str] = None

@dataclass
class Supplier:
    id: int
    name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    notes: Optional[str]

@dataclass
class PurchaseOrder:
    id: int
    order_code: str
    supplier_id: int
    status: str  # 'en_attente', 'brouillon', 'recu_complet', 'recu_partiel', 'annule'
    total_amount: float
    notes: Optional[str]
    created_at: Optional[str] = None
    received_at: Optional[str] = None
    supplier_name: Optional[str] = None

@dataclass
class PurchaseOrderItem:
    id: int
    order_id: int
    product_id: Optional[int]
    product_name: str
    barcode: Optional[str]
    qty_ordered: int
    qty_received: int
    unit_cost: float
    total_cost: float
    is_new_product: bool = False
    status: str = "en_attente"

@dataclass
class Sale:
    id: int
    sale_code: str
    session_id: Optional[int]
    user_id: int
    total_ht: float
    total_tva: float
    discount_amount: float
    total_ttc: float
    payment_method: str
    amount_received: float
    change_given: float
    customer_name: str
    created_at: Optional[str] = None
