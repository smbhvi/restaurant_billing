# 🍽️ Restaurant Billing System  

A full-featured **Restaurant Billing System** built using Python (Tkinter) and SQL.  
This POS system helps manage menu items, take customer orders, apply discounts, calculate taxes, and record payments.  

---

## 🚀 Features  
- 📋 Menu Management – View menu items with categories, prices, and GST.  
- 🧾 Order Management– Create and view customer orders with real-time calculations.  
- 💳 Payment System – Supports Cash, Card, and UPI payments.  
- 📊 Billing Summary– Shows subtotal, tax, discount, and final total.  
- 🛠️ Database-Driven – Uses MySQL for storing menu, orders, and order items.  
- 🎨 User-Friendly GUI– Clean and modern interface with tabs for Menu & Orders.  

---

## 🛠️ Tech Stack  
- Python 3(Tkinter for GUI)  
- MySQL (Database)  

---

## 📂 Database Schema  

### Database: `restaurant_billing`  
- menu → Stores menu items (id, name, category, price, gst, is_active)  
- orders → Stores order details (id, customer, subtotal, tax, discount, total, payment method, etc.)  
- order_items → Stores items per order (order_id, menu_item_id, quantity, price, gst)  

