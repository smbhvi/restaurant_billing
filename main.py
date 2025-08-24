import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import mysql.connector
import csv
import json

try:
    from fpdf import FPDF
    PDF_ENABLED = True
except Exception:
    PDF_ENABLED = False

# ------------------------- DB CONFIG -------------------------
DB_CONFIG = dict(
    host="localhost",
    user="root",          
    password=" ",  
    database="restaurant_billing"
)

# ------------------------- DB UTILS --------------------------
def db_conn():
    return mysql.connector.connect(**DB_CONFIG)

# ------------------------- APP -------------------------------
class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍴 Restaurant Billing System")
        self.root.geometry("1280x820")
        self.root.configure(bg="#f6f8fb")

        self.cart = [] 
        self.discount_pct = tk.DoubleVar(value=0.0)
        self.service_pct = tk.DoubleVar(value=0.0)  
        self.order_type = tk.StringVar(value="Dine-In")
        self.payment_method = tk.StringVar(value="Cash")
        self.customer_name = tk.StringVar()
        self.customer_mobile = tk.StringVar()

        self.search_text = tk.StringVar()
        self.filter_category = tk.StringVar(value="All")

        self._style()
        self._build_tabs()
        self._build_pos_tab()
        self._build_admin_tab()
        self._build_history_tab()
        self._build_reports_tab()

        try:
            self._ensure_menu_seed()
        except Exception as e:
            messagebox.showwarning("Menu", f"Could not seed menu (will continue):{e}")

        self.refresh_menu_tree()

    # --------------------- THEME ---------------------
    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TLabel", background="#f6f8fb", font=("Segoe UI", 11))
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("Primary.TButton", foreground="#fff", background="#2563eb")
        style.map("Primary.TButton", background=[("active", "#1d4ed8")])
        style.configure("Danger.TButton", foreground="#fff", background="#dc2626")
        style.map("Danger.TButton", background=[("active", "#b91c1c")])
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

    # --------------------- TABS ----------------------
    def _build_tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_pos = ttk.Frame(self.nb)
        self.tab_admin = ttk.Frame(self.nb)
        self.tab_history = ttk.Frame(self.nb)
        self.tab_reports = ttk.Frame(self.nb)

        self.nb.add(self.tab_pos, text="🧾 POS")
        self.nb.add(self.tab_admin, text="🛠️ Menu Admin")
        self.nb.add(self.tab_history, text="📚 Order History")
        self.nb.add(self.tab_reports, text="📈 Reports")

    # --------------------- POS TAB --------------------
    def _build_pos_tab(self):
        left = ttk.Frame(self.tab_pos)
        left.pack(side="left", fill="both", expand=True, padx=(10,5), pady=10)

        ttk.Label(left, text="Menu", style="Header.TLabel").pack(anchor="w")
        filt = ttk.Frame(left)
        filt.pack(fill="x", pady=6)
        ttk.Entry(filt, textvariable=self.search_text, width=28).pack(side="left")
        ttk.Button(filt, text="Search", command=self.refresh_menu_tree).pack(side="left", padx=6)
        ttk.Label(filt, text="Category:").pack(side="left", padx=(10,4))
        self.category_combo = ttk.Combobox(filt, textvariable=self.filter_category, state="readonly", width=16)
        self.category_combo.pack(side="left")
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_menu_tree())

        cols = ("ID", "Item", "Category", "Price", "GST%")
        self.menu_tree = ttk.Treeview(left, columns=cols, show="headings")
        for c in cols:
            self.menu_tree.heading(c, text=c)
            width = 70 if c in ("ID", "GST%") else (100 if c == "Price" else 240)
            self.menu_tree.column(c, width=width, anchor="center")
        self.menu_tree.pack(fill="both", expand=True)

        addbar = ttk.Frame(left)
        addbar.pack(fill="x", pady=8)
        ttk.Button(addbar, text="➕ Add to Cart", command=self.add_selected_to_cart, style="Primary.TButton").pack(side="left")
        ttk.Button(addbar, text="🔄 Refresh", command=self.refresh_menu_tree).pack(side="left", padx=6)

        right = ttk.Frame(self.tab_pos)
        right.pack(side="right", fill="both", expand=True, padx=(5,10), pady=10)

        ttk.Label(right, text="Cart", style="Header.TLabel").pack(anchor="w")
        ccols = ("Item", "Qty", "Price", "GST%", "Line Total")
        self.cart_tree = ttk.Treeview(right, columns=ccols, show="headings")
        for c in ccols:
            self.cart_tree.heading(c, text=c)
            width = 80 if c in ("Qty", "GST%") else (110 if c in ("Price",) else 240)
            self.cart_tree.column(c, width=width, anchor="center")
        self.cart_tree.pack(fill="both", expand=True)

        ctrls = ttk.Frame(right)
        ctrls.pack(fill="x", pady=6)
        ttk.Button(ctrls, text="➖ Remove", command=self.remove_selected_cart, style="Danger.TButton").pack(side="left")
        ttk.Button(ctrls, text="✏️ Edit Qty", command=self.edit_cart_qty).pack(side="left", padx=6)
        ttk.Button(ctrls, text="🧹 Clear Cart", command=self.clear_cart).pack(side="left")

        bill = ttk.LabelFrame(right, text="Billing")
        bill.pack(fill="x", pady=8)

        row = 0
        ttk.Label(bill, text="Order Type:").grid(row=row, column=0, sticky="w", padx=8, pady=6)
        ttk.Combobox(bill, textvariable=self.order_type, values=["Dine-In", "Takeaway"], state="readonly", width=12).grid(row=row, column=1, sticky="w")
        ttk.Label(bill, text="Payment:").grid(row=row, column=2, sticky="w", padx=8)
        ttk.Combobox(bill, textvariable=self.payment_method, values=["Cash", "Card", "UPI"], state="readonly", width=12).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(bill, text="Customer Name:").grid(row=row, column=0, sticky="w", padx=8)
        ttk.Entry(bill, textvariable=self.customer_name, width=22).grid(row=row, column=1, sticky="w")
        ttk.Label(bill, text="Mobile:").grid(row=row, column=2, sticky="w", padx=8)
        ttk.Entry(bill, textvariable=self.customer_mobile, width=18).grid(row=row, column=3, sticky="w")

        row += 1
        ttk.Label(bill, text="Discount %:").grid(row=row, column=0, sticky="w", padx=8)
        ttk.Entry(bill, textvariable=self.discount_pct, width=8).grid(row=row, column=1, sticky="w")
        ttk.Label(bill, text="Service %:").grid(row=row, column=2, sticky="w", padx=8)
        ttk.Entry(bill, textvariable=self.service_pct, width=8).grid(row=row, column=3, sticky="w")

        row += 1
        self.totals_lbl = ttk.Label(bill, text="Subtotal: ₹0.00 | GST: ₹0.00 | Discount: ₹0.00 | Service: ₹0.00 | Total: ₹0.00", font=("Segoe UI", 11, "bold"))
        self.totals_lbl.grid(row=row, column=0, columnspan=4, sticky="w", padx=8, pady=6)

        row += 1
        ttk.Button(bill, text="🧮 Calculate", command=self.recompute_totals).grid(row=row, column=0, padx=8, pady=6, sticky="we")
        ttk.Button(bill, text="✅ Confirm Payment", command=self.save_order, style="Primary.TButton").grid(row=row, column=1, padx=8, pady=6, sticky="we")
        ttk.Button(bill, text="📄 Export Bill", command=self.export_current_bill).grid(row=row, column=2, padx=8, pady=6, sticky="we")

    # --------------------- ADMIN TAB ------------------
    def _build_admin_tab(self):
        top = ttk.Frame(self.tab_admin)
        top.pack(fill="x", pady=6)
        ttk.Label(top, text="Manage Menu", style="Header.TLabel").pack(side="left", padx=10)
        ttk.Button(top, text="➕ Add", command=self.admin_add).pack(side="left", padx=5)
        ttk.Button(top, text="✏️ Edit", command=self.admin_edit).pack(side="left", padx=5)
        ttk.Button(top, text="🗑 Delete", command=self.admin_delete, style="Danger.TButton").pack(side="left", padx=5)
        ttk.Button(top, text="⬆️ Import CSV", command=self.import_menu_csv).pack(side="left", padx=5)
        ttk.Button(top, text="🔄 Refresh", command=self.refresh_admin_tree).pack(side="left", padx=5)

        cols = ("ID", "Item", "Category", "Price", "GST%", "Active")
        self.admin_tree = ttk.Treeview(self.tab_admin, columns=cols, show="headings")
        for c in cols:
            self.admin_tree.heading(c, text=c)
            self.admin_tree.column(c, width=100 if c in ("ID", "GST%", "Active") else 220, anchor="center")
        self.admin_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_admin_tree()

    # --------------------- HISTORY TAB ----------------
    def _build_history_tab(self):
        top = ttk.Frame(self.tab_history)
        top.pack(fill="x", pady=6)
        ttk.Label(top, text="Orders", style="Header.TLabel").pack(side="left", padx=10)
        ttk.Button(top, text="🔄 Refresh", command=self.refresh_orders_tree).pack(side="left", padx=5)
        ttk.Button(top, text="📄 Export Selected Bill", command=self.export_selected_history_bill).pack(side="left", padx=5)

        cols = ("ID", "Ref", "Date", "Type", "Payment", "Subtotal", "GST", "Discount", "Service", "Total", "Customer")
        self.orders_tree = ttk.Treeview(self.tab_history, columns=cols, show="headings")
        for c in cols:
            self.orders_tree.heading(c, text=c)
            self.orders_tree.column(c, width=90 if c in ("ID", "Type", "Payment") else 120, anchor="center")
        self.orders_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_orders_tree()

    # --------------------- REPORTS TAB ---------------
    def _build_reports_tab(self):
        top = ttk.Frame(self.tab_reports)
        top.pack(fill="x", pady=6)
        ttk.Label(top, text="Sales Reports", style="Header.TLabel").pack(side="left", padx=10)
        ttk.Button(top, text="📅 Daily CSV", command=lambda: self.export_sales("daily")).pack(side="left", padx=5)
        ttk.Button(top, text="🗓 Weekly CSV", command=lambda: self.export_sales("weekly")).pack(side="left", padx=5)
        ttk.Button(top, text="📆 Monthly CSV", command=lambda: self.export_sales("monthly")).pack(side="left", padx=5)
        ttk.Button(top, text="🏆 Top Items CSV", command=self.export_top_items).pack(side="left", padx=5)

    # ===================== MENU SEED ==========================
    def _ensure_menu_seed(self):
        """Insert our agreed sample items if menu is empty."""
        conn = db_conn(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM menu")
        count = cur.fetchone()[0]
        if count and int(count) > 0:
            conn.close(); return

        items = [
            ("Paneer Tikka", "Starters", 220.00, 5.0, 1),
            ("Chicken Tikka", "Starters", 260.00, 5.0, 1),
            ("Hara Bhara Kebab", "Starters", 180.00, 5.0, 1),
    
            ("Veg Burger", "Snacks", 120.00, 5.0, 1),
            ("Chicken Burger", "Snacks", 150.00, 5.0, 1),
            ("Margherita Pizza", "Snacks", 299.00, 5.0, 1),
            ("Farmhouse Pizza", "Snacks", 399.00, 5.0, 1),
   
            ("Veg Biryani", "Main Course", 240.00, 5.0, 1),
            ("Chicken Biryani", "Main Course", 290.00, 5.0, 1),
            ("Dal Tadka", "Main Course", 180.00, 5.0, 1),
            ("Butter Chicken", "Main Course", 320.00, 5.0, 1),
            ("Paneer Butter Masala", "Main Course", 280.00, 5.0, 1),
      
            ("Tandoori Roti", "Breads", 25.00, 5.0, 1),
            ("Butter Naan", "Breads", 45.00, 5.0, 1),
          
            ("Rasgulla", "Desserts", 120.00, 5.0, 1),
            ("Gulab Jamun", "Desserts", 120.00, 5.0, 1),
          
            ("Cola (300ml)", "Drinks", 40.00, 5.0, 1),
            ("Mineral Water", "Drinks", 30.00, 5.0, 1),
        ]
        cur.executemany(
            "INSERT INTO menu (item_name, category, price, gst, is_active) VALUES (%s,%s,%s,%s,%s)",
            items
        )
        conn.commit(); conn.close()

    # ===================== MENU LOAD/FILTER =====================
    def refresh_menu_tree(self):
   
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category FROM menu WHERE is_active=1 ORDER BY category")
        cats = [r[0] for r in cur.fetchall() if r[0]]
        cats = ["All"] + cats
        self.category_combo["values"] = cats
        if self.filter_category.get() not in cats:
            self.filter_category.set("All")

        q = "SELECT id, item_name, category, price, gst FROM menu WHERE is_active=1"
        params = []
        if self.filter_category.get() != "All":
            q += " AND category=%s"
            params.append(self.filter_category.get())
        if self.search_text.get().strip():
            q += " AND item_name LIKE %s"
            params.append(f"%{self.search_text.get().strip()}%")
        q += " ORDER BY category, item_name"

        cur.execute(q, tuple(params))
        rows = cur.fetchall()
        conn.close()

        for i in self.menu_tree.get_children():
            self.menu_tree.delete(i)
        for r in rows:
            self.menu_tree.insert("", "end", values=r)

    # ===================== CART OPS ============================
    def add_selected_to_cart(self):
        sel = self.menu_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a menu item.")
            return
        row = self.menu_tree.item(sel[0], "values")
        item_id, name, cat, price, gst = row

        for it in self.cart:
            if it["id"] == int(item_id):
                it["qty"] += 1
                self.refresh_cart_tree()
                self.recompute_totals()
                return
        self.cart.append({"id": int(item_id), "name": name, "price": float(price), "gst": float(gst), "qty": 1})
        self.refresh_cart_tree()
        self.recompute_totals()

    def refresh_cart_tree(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        for it in self.cart:
            line_total = it["price"] * it["qty"] * (1 + it["gst"]/100)
            self.cart_tree.insert("", "end", values=(it["name"], it["qty"], f"{it['price']:.2f}", f"{it['gst']:.2f}", f"{line_total:.2f}"))

    def remove_selected_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = self.cart_tree.index(sel[0])
        del self.cart[idx]
        self.refresh_cart_tree()
        self.recompute_totals()

    def edit_cart_qty(self):
        sel = self.cart_tree.selection()
        if not sel:
            messagebox.showinfo("Edit Quantity", "Select a cart row first.")
            return
        idx = self.cart_tree.index(sel[0])
        it = self.cart[idx]

        win = tk.Toplevel(self.root)
        win.title("Edit Quantity")
        win.resizable(False, False)
        ttk.Label(win, text=f"{it['name']} quantity:").grid(row=0, column=0, padx=10, pady=10)
        qv = tk.IntVar(value=it["qty"]) 
        ttk.Spinbox(win, from_=1, to=999, textvariable=qv, width=8).grid(row=0, column=1, padx=10)
        def apply():
            it["qty"] = max(1, int(qv.get()))
            self.refresh_cart_tree()
            self.recompute_totals()
            win.destroy()
        ttk.Button(win, text="Apply", command=apply).grid(row=1, column=0, columnspan=2, pady=10, sticky="we")

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart_tree()
        self.recompute_totals()

    # ===================== TOTALS & SAVE =======================
    def recompute_totals(self):
        subtotal = sum(it["price"] * it["qty"] for it in self.cart)
        gst_total = sum(it["price"] * it["qty"] * (it["gst"]/100) for it in self.cart)
        disc_val = subtotal * (self.discount_pct.get()/100.0)
        service_val = subtotal * (self.service_pct.get()/100.0)
        total = subtotal + gst_total + service_val - disc_val
        self.totals_lbl.config(
            text=f"Subtotal: ₹{subtotal:.2f} | GST: ₹{gst_total:.2f} | Discount: ₹{disc_val:.2f} | Service: ₹{service_val:.2f} | Total: ₹{total:.2f}"
        )
        return subtotal, gst_total, disc_val, service_val, total

    def _validate_customer(self):
        name = self.customer_name.get().strip()
        mobile = self.customer_mobile.get().strip()
        if not name:
            messagebox.showerror("Missing info", "Customer name is required.")
            return False
        if mobile and not mobile.isdigit():
            messagebox.showerror("Invalid mobile", "Mobile must be digits only.")
            return False
        return True

    def _gen_reference(self, order_id: int) -> str:
        ts = datetime.now().strftime("%y%m%d%H%M")
        return f"RB{ts}{order_id:05d}"

    def save_order(self):
        if not self.cart:
            messagebox.showerror("Empty cart", "Add items before saving.")
            return
        if not self._validate_customer():
            return

        subtotal, gst_total, disc_val, service_val, total = self.recompute_totals()
        try:
            conn = db_conn()
            cur = conn.cursor()
  
            try:
                cur.execute(
                    """
                    INSERT INTO orders (order_type, payment_method, subtotal, tax, discount, service_charge, total, 
                                        customer_name, customer_mobile, order_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (self.order_type.get(), self.payment_method.get(), subtotal, gst_total, disc_val, service_val, total,
                     self.customer_name.get().strip(), self.customer_mobile.get().strip(), datetime.now())
                )
            except Exception:
                
                cur.execute(
                    """
                    INSERT INTO orders (order_type, payment_method, subtotal, tax, discount, total, 
                                        customer_name, customer_mobile, order_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (self.order_type.get(), self.payment_method.get(), subtotal, gst_total, disc_val, total,
                     self.customer_name.get().strip(), self.customer_mobile.get().strip(), datetime.now())
                )
            order_id = cur.lastrowid

            for it in self.cart:
                cur.execute(
                    """
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price, gst)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (order_id, it["id"], it["qty"], it["price"], it["gst"]))

            try:
                ref_no = self._gen_reference(order_id)
                cur.execute("UPDATE orders SET reference_no=%s WHERE id=%s", (ref_no, order_id))
            except Exception:
                ref_no = str(order_id)

            conn.commit()
            conn.close()

            self._last_saved = dict(order_id=order_id, reference_no=ref_no, subtotal=subtotal,
                                    gst=gst_total, discount=disc_val, service=service_val, total=total,
                                    items=[dict(**it) for it in self.cart],
                                    order_type=self.order_type.get(), payment=self.payment_method.get(),
                                    customer=self.customer_name.get().strip(), mobile=self.customer_mobile.get().strip(),
                                    date=str(datetime.now()))

            self._show_receipt_popup(self._last_saved)

            self.clear_cart()
            self.refresh_orders_tree()
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save order: {e}")

    def _show_receipt_popup(self, data: dict):
        win = tk.Toplevel(self.root)
        win.title(f"Receipt – {data['reference_no']}")
        win.geometry("520x520")
        txt = tk.Text(win, font=("Consolas", 10))
        txt.pack(fill="both", expand=True)
        txt.insert("end", "*** Restaurant Bill ***")
        txt.insert("end", f"Ref: {data['reference_no']}")
        txt.insert("end", f"Date: {data['date']}")
        txt.insert("end", f"Customer: {data['customer']}  Mobile: {data['mobile']}")
        txt.insert("end", "Items:")
        txt.insert("end", "---------------------------------------------")
        for it in data["items"]:
            line_total = it["price"] * it["qty"] * (1 + it["gst"]/100)
            txt.insert("end", f"{it['name']:<25} x{it['qty']:<3} ₹{it['price']:.2f}  GST {it['gst']:.1f}%  = ₹{line_total:.2f}")
        txt.insert("end", "---------------------------------------------")
        txt.insert("end", f"Subtotal:      ₹{data['subtotal']:.2f}")
        txt.insert("end", f"GST:           ₹{data['gst']:.2f}")
        txt.insert("end", f"Discount:      ₹{data['discount']:.2f}")
        if 'service' in data:
            txt.insert("end", f"Service:       ₹{data['service']:.2f}")
        txt.insert("end", f"TOTAL:         ₹{data['total']:.2f}")
        txt.configure(state="disabled")

    # ===================== BILL EXPORT ========================
    def export_current_bill(self):
        if not hasattr(self, "_last_saved"):
            messagebox.showinfo("Export", "Save an order first.")
            return
        data = self._last_saved
        base = f"bill_{data['reference_no']}"

        with open(base + ".json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Item", "Qty", "Price", "GST%", "Line Total"])
            for it in data["items"]:
                line_total = it["price"] * it["qty"] * (1 + it["gst"]/100)
                w.writerow([it["name"], it["qty"], f"{it['price']:.2f}", f"{it['gst']:.2f}", f"{line_total:.2f}"])
            w.writerow([])
            w.writerow(["Subtotal", f"{data['subtotal']:.2f}"])
            w.writerow(["GST", f"{data['gst']:.2f}"])
            w.writerow(["Discount", f"{data['discount']:.2f}"])
            if 'service' in data:
                w.writerow(["Service", f"{data['service']:.2f}"])
            w.writerow(["Total", f"{data['total']:.2f}"])
  
        if PDF_ENABLED:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Restaurant Bill", ln=True, align="C")
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 8, f"Ref: {data['reference_no']}", ln=True)
            pdf.cell(0, 8, f"Date: {data['date']}", ln=True)
            pdf.cell(0, 8, f"Customer: {data['customer']}  Mobile: {data['mobile']}", ln=True)
            pdf.ln(4)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(90, 8, "Item", 1)
            pdf.cell(20, 8, "Qty", 1)
            pdf.cell(30, 8, "Price", 1)
            pdf.cell(20, 8, "GST%", 1)
            pdf.cell(30, 8, "Total", 1, ln=True)
            pdf.set_font("Arial", size=12)
            for it in data["items"]:
                line_total = it["price"] * it["qty"] * (1 + it["gst"]/100)
                pdf.cell(90, 8, it["name"], 1)
                pdf.cell(20, 8, str(it["qty"]), 1)
                pdf.cell(30, 8, f"{it['price']:.2f}", 1)
                pdf.cell(20, 8, f"{it['gst']:.2f}", 1)
                pdf.cell(30, 8, f"{line_total:.2f}", 1, ln=True)
            pdf.ln(4)
            pdf.cell(0, 8, f"Subtotal: ₹{data['subtotal']:.2f}", ln=True)
            pdf.cell(0, 8, f"GST: ₹{data['gst']:.2f}", ln=True)
            pdf.cell(0, 8, f"Discount: ₹{data['discount']:.2f}", ln=True)
            if 'service' in data:
                pdf.cell(0, 8, f"Service: ₹{data['service']:.2f}", ln=True)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Total: ₹{data['total']:.2f}", ln=True)
            pdf.output(base + ".pdf")
        messagebox.showinfo("Export", f"Saved {base}.json / .csv" + (" / .pdf" if PDF_ENABLED else ""))

    # ===================== ADMIN CRUD =========================
    def refresh_admin_tree(self):
        conn = db_conn(); cur = conn.cursor()
        cur.execute("SELECT id, item_name, category, price, gst, is_active FROM menu ORDER BY item_name")
        rows = cur.fetchall(); conn.close()
        for i in self.admin_tree.get_children():
            self.admin_tree.delete(i)
        for r in rows:
            self.admin_tree.insert("", "end", values=r)

    def admin_add(self):
        self._menu_form()

    def admin_edit(self):
        sel = self.admin_tree.selection()
        if not sel:
            messagebox.showinfo("Edit", "Select a row first.")
            return
        vals = self.admin_tree.item(sel[0], "values")
        self._menu_form(prefill=vals)

    def admin_delete(self):
        sel = self.admin_tree.selection()
        if not sel:
            return
        vals = self.admin_tree.item(sel[0], "values")
        mid = int(vals[0])
        if not messagebox.askyesno("Delete", f"Delete '{vals[1]}'?"):
            return
        conn = db_conn(); cur = conn.cursor()
        cur.execute("DELETE FROM menu WHERE id=%s", (mid,))
        conn.commit(); conn.close()
        self.refresh_admin_tree(); self.refresh_menu_tree()

    def _menu_form(self, prefill=None):
        win = tk.Toplevel(self.root); win.title("Menu Item"); win.resizable(False, False)
        ttk.Label(win, text="Item Name:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        ttk.Label(win, text="Category:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        ttk.Label(win, text="Price:").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        ttk.Label(win, text="GST %:").grid(row=3, column=0, padx=10, pady=8, sticky="e")
        ttk.Label(win, text="Active (1/0):").grid(row=4, column=0, padx=10, pady=8, sticky="e")

        namev = tk.StringVar(); catv = tk.StringVar(); pricev = tk.DoubleVar(value=0.0); gstv = tk.DoubleVar(value=5.0); actv = tk.IntVar(value=1)
        if prefill:
            _id, nm, cat, pr, gst, act = prefill
            namev.set(nm); catv.set(cat); pricev.set(float(pr)); gstv.set(float(gst)); actv.set(int(act))

        ttk.Entry(win, textvariable=namev, width=28).grid(row=0, column=1, padx=10)
        ttk.Entry(win, textvariable=catv, width=28).grid(row=1, column=1, padx=10)
        ttk.Entry(win, textvariable=pricev, width=12).grid(row=2, column=1, padx=10, sticky="w")
        ttk.Entry(win, textvariable=gstv, width=12).grid(row=3, column=1, padx=10, sticky="w")
        ttk.Entry(win, textvariable=actv, width=12).grid(row=4, column=1, padx=10, sticky="w")

        def save():
            name = namev.get().strip()
            if not name:
                messagebox.showerror("Validation", "Item name required.")
                return
            conn = db_conn(); cur = conn.cursor()
            if prefill:
                mid = int(prefill[0])
                cur.execute("UPDATE menu SET item_name=%s, category=%s, price=%s, gst=%s, is_active=%s WHERE id=%s",
                            (name, catv.get().strip(), pricev.get(), gstv.get(), actv.get(), mid))
            else:
                cur.execute("INSERT INTO menu (item_name, category, price, gst, is_active) VALUES (%s,%s,%s,%s,%s)",
                            (name, catv.get().strip(), pricev.get(), gstv.get(), actv.get()))
            conn.commit(); conn.close()
            self.refresh_admin_tree(); self.refresh_menu_tree(); win.destroy()

        ttk.Button(win, text="Save", command=save, style="Primary.TButton").grid(row=5, column=0, columnspan=2, pady=10, sticky="we")

    def import_menu_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        cnt = 0
        conn = db_conn(); cur = conn.cursor()
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    cur.execute(
                        "INSERT INTO menu (item_name, category, price, gst, is_active) VALUES (%s,%s,%s,%s,%s)",
                        (r.get('item_name') or r.get('name'), r.get('category'), float(r.get('price', 0)), float(r.get('gst', 0)), int(r.get('is_active', 1)))
                    ); cnt += 1
                except Exception:
                    pass
        conn.commit(); conn.close()
        messagebox.showinfo("Import", f"Imported {cnt} items.")
        self.refresh_admin_tree(); self.refresh_menu_tree()

    # ===================== HISTORY & EXPORT ================
    def refresh_orders_tree(self):
        conn = db_conn(); cur = conn.cursor()
    
        try:
            cur.execute(
                """
                SELECT id, COALESCE(reference_no,''), order_date, order_type, payment_method,
                       subtotal, tax, discount, COALESCE(service_charge,0), total, customer_name
                FROM orders ORDER BY id DESC LIMIT 200
                """
            )
        except Exception:
            cur.execute(
                """
                SELECT id, '' as ref, order_date, order_type, payment_method,
                       subtotal, tax, discount, 0, total, customer_name
                FROM orders ORDER BY id DESC LIMIT 200
                """
            )
        rows = cur.fetchall(); conn.close()
        for i in self.orders_tree.get_children():
            self.orders_tree.delete(i)
        for r in rows:
            dt = r[2].strftime("%Y-%m-%d %H:%M") if hasattr(r[2], 'strftime') else str(r[2])
            self.orders_tree.insert("", "end", values=(r[0], r[1], dt, r[3], r[4], f"{float(r[5]):.2f}", f"{float(r[6]):.2f}", f"{float(r[7]):.2f}", f"{float(r[8]):.2f}", f"{float(r[9]):.2f}", r[10]))

    def export_selected_history_bill(self):
        sel = self.orders_tree.selection()
        if not sel:
            return
        order_id = int(self.orders_tree.item(sel[0], "values")[0])
        self._export_order_by_id(order_id)

    def _export_order_by_id(self, order_id: int):
        conn = db_conn(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        order = cur.fetchone()
        cur.execute(
            """
            SELECT oi.quantity, oi.price, oi.gst, m.item_name
            FROM order_items oi JOIN menu m ON oi.menu_item_id=m.id
            WHERE oi.order_id=%s
            """, (order_id,)
        )
        items = cur.fetchall(); conn.close()
        ref = order.get('reference_no') or f"{order_id}"
        data = dict(
            order_id=order_id,
            reference_no=ref,
            date=str(order.get('order_date')),
            order_type=order.get('order_type'),
            payment=order.get('payment_method'),
            subtotal=float(order.get('subtotal') or 0),
            gst=float(order.get('tax') or 0),
            discount=float(order.get('discount') or 0),
            service=float(order.get('service_charge') or 0),
            total=float(order.get('total') or 0),
            customer=order.get('customer_name'),
            mobile=order.get('customer_mobile'),
            items=[dict(name=i['item_name'], qty=int(i['quantity']), price=float(i['price']), gst=float(i['gst'])) for i in items]
        )
        self._last_saved = data
        self.export_current_bill()

    # ===================== REPORTS ===========================
    def export_sales(self, period: str):
        conn = db_conn(); cur = conn.cursor()
        if period == "daily":
            cur.execute("SELECT DATE(order_date) as day, SUM(total) FROM orders GROUP BY DATE(order_date) ORDER BY day DESC")
            fname = "sales_daily.csv"
        elif period == "weekly":
            cur.execute("SELECT YEARWEEK(order_date,1) as week, SUM(total) FROM orders GROUP BY YEARWEEK(order_date,1) ORDER BY week DESC")
            fname = "sales_weekly.csv"
        else:
            cur.execute("SELECT DATE_FORMAT(order_date,'%Y-%m') as month, SUM(total) FROM orders GROUP BY DATE_FORMAT(order_date,'%Y-%m') ORDER BY month DESC")
            fname = "sales_monthly.csv"
        rows = cur.fetchall(); conn.close()
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Period", "Total Sales"])
            for r in rows:
                w.writerow([r[0], f"{float(r[1] or 0):.2f}"])
        messagebox.showinfo("Reports", f"Exported {fname}")

    def export_top_items(self):
        conn = db_conn(); cur = conn.cursor()
        cur.execute(
            """
            SELECT m.item_name, SUM(oi.quantity) as qty, SUM(oi.quantity*oi.price) as revenue
            FROM order_items oi JOIN menu m ON oi.menu_item_id=m.id
            GROUP BY m.item_name ORDER BY qty DESC LIMIT 50
            """
        )
        rows = cur.fetchall(); conn.close()
        fname = "top_items.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Item", "Quantity Sold", "Revenue"])
            for r in rows:
                w.writerow([r[0], int(r[1] or 0), f"{float(r[2] or 0):.2f}"])
        messagebox.showinfo("Reports", f"Exported {fname}")

# ------------------------- MAIN -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
