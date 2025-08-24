import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import random

# ===================== DB =====================
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",                
        password="yourpassword",     
        database="restaurant_billing"
    )

# ===================== PRICES =====================
PRICES = {
    "paneer": 120,
    "dal": 100,
    "roti": 20,
    "biryani": 150,          
    "dosa": 80,
    "drinks": 50,
    "chicken_biryani": 180,
    "chicken": 200,
    "naan": 25,
    "rasgulla": 40,
}

# ===================== APP =====================
class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Billing System")
        self.root.geometry("1060x680")
        self.root.configure(bg="#fdf6e3") 

        self.customer_name = tk.StringVar()
        self.customer_mobile = tk.StringVar()
        self.order_type = tk.StringVar(value="Dine-In")
        self.reference_no = tk.StringVar(value=str(random.randint(10000, 99999)))

        self.qty_vars = {k: tk.StringVar(value="") for k in PRICES.keys()}

        self.subtotal = 0.0
        self.tax = 0.0
        self.service_charge = 0.0
        self.discount = 0.0
        self.total = 0.0

        # ---------- layout ----------
        self.build_header()
        self.build_body()
        self.build_bill_area()
        self.build_buttons()

        self.print_bill(preview_only=True)

    # ---------- UI sections ----------
    def build_header(self):
        header = tk.Frame(self.root, bg="#0f4c81", height=64) 
        header.pack(fill="x", side="top")

        title = tk.Label(
            header, text="Restaurant Billing System",
            fg="white", bg="#0f4c81",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=10)

    def build_body(self):
        body = tk.Frame(self.root, bg="#fdf6e3")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(body, bg="#fdf6e3")
        left.pack(side="left", fill="y")

        self.build_customer(left)
        self.build_menu(left)

    def build_customer(self, parent):
        frame = tk.LabelFrame(
            parent, text="Customer Details", bg="#eaf4ff", fg="#1e293b",
            labelanchor="nw", font=("Segoe UI", 10, "bold"), padx=12, pady=12
        )
        frame.pack(fill="x", padx=2, pady=(0, 10))

        ttk.Label(frame, text="Customer Name *").grid(row=0, column=0, sticky="w", padx=2, pady=4)
        self.ent_name = ttk.Entry(frame, textvariable=self.customer_name, width=32)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=2, pady=4)

        ttk.Label(frame, text="Mobile Number").grid(row=1, column=0, sticky="w", padx=2, pady=4)
        ttk.Entry(frame, textvariable=self.customer_mobile, width=32).grid(row=1, column=1, sticky="w", padx=2, pady=4)

        ttk.Label(frame, text="Order Type").grid(row=2, column=0, sticky="w", padx=2, pady=(8, 2))
        combo = ttk.Combobox(frame, textvariable=self.order_type, state="readonly", width=29,
                             values=["Dine-In", "Takeaway"])
        combo.grid(row=2, column=1, sticky="w", padx=2, pady=(8, 2))
        combo.current(0)

        ttk.Label(frame, text="Reference No").grid(row=3, column=0, sticky="w", padx=2, pady=4)
        ref_ent = ttk.Entry(frame, textvariable=self.reference_no, width=32, state="readonly")
        ref_ent.grid(row=3, column=1, sticky="w", padx=2, pady=4)

    def build_menu(self, parent):
 
        wrap = tk.LabelFrame(
            parent, text="Menu", bg="#fdf6e3", fg="#1e293b",
            labelanchor="nw", font=("Segoe UI", 10, "bold"), padx=8, pady=8
        )
        wrap.pack(fill="x", padx=2, pady=2)

        left_col = tk.LabelFrame(wrap, text="Main Course", bg="#dbeafe", fg="#0f172a",
                                 font=("Segoe UI", 10, "bold"), padx=8, pady=8)
        right_col = tk.LabelFrame(wrap, text="Breads & Others", bg="#fde2e4", fg="#0f172a",
                                  font=("Segoe UI", 10, "bold"), padx=8, pady=8)
        left_col.grid(row=0, column=0, sticky="n", padx=(0, 8))
        right_col.grid(row=0, column=1, sticky="n")

        self.add_menu_row(left_col, "Paneer Butter Masala", "paneer", row=0)
        self.add_menu_row(left_col, "Dal Tadka", "dal", row=1)
        self.add_menu_row(left_col, "Veg Biryani", "biryani", row=2)
        self.add_menu_row(left_col, "Chicken Biryani", "chicken_biryani", row=3)
        self.add_menu_row(left_col, "Chicken Curry", "chicken", row=4)

        self.add_menu_row(right_col, "Roti", "roti", row=0)
        self.add_menu_row(right_col, "Naan", "naan", row=1)
        self.add_menu_row(right_col, "Masala Dosa", "dosa", row=2)
        self.add_menu_row(right_col, "Rasgulla", "rasgulla", row=3)
        self.add_menu_row(right_col, "Cold Drinks", "drinks", row=4)

    def add_menu_row(self, parent, label, key, row):
      
        tk.Label(parent, text=f"{label}  (₹{PRICES[key]})", bg=parent["bg"], font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky="w", pady=3
        )
        ent = ttk.Entry(parent, width=8, textvariable=self.qty_vars[key])
        ent.grid(row=row, column=1, padx=(10, 0), pady=3)

    def build_bill_area(self):

        right = tk.Frame(self.root, bg="#fdf6e3")
        right.place(relx=0.5, rely=0.16, relwidth=0.48, relheight=0.78)

        title = tk.Label(
            right, text="🧾 Billing Preview", bg="#10b981", fg="white",  # teal bar
            font=("Segoe UI", 12, "bold")
        )
        title.pack(fill="x", pady=(0, 6))

        container = tk.Frame(right, bg="#eafff3", bd=1, relief="solid")
        container.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.bill_text = tk.Text(container, font=("Consolas", 11), bg="#f8fffb", relief="flat")
        self.bill_text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(container, command=self.bill_text.yview)
        scroll.pack(side="right", fill="y")
        self.bill_text["yscrollcommand"] = scroll.set

    def build_buttons(self):
        bar = tk.Frame(self.root, bg="#fdf6e3")
        bar.pack(side="bottom", fill="x", padx=10, pady=8)

        self.btn_calc = tk.Button(bar, text="Calculate Total", width=16, bg="#22c55e", fg="white",
                                  font=("Segoe UI", 10, "bold"), command=self.calculate_totals)
        self.btn_save = tk.Button(bar, text="Save to Database", width=16, bg="#f59e0b", fg="white",
                                  font=("Segoe UI", 10, "bold"), command=self.save_to_db)
        self.btn_reset = tk.Button(bar, text="Reset", width=12, bg="#6366f1", fg="white",
                                   font=("Segoe UI", 10, "bold"), command=self.reset_all)
        self.btn_exit = tk.Button(bar, text="Exit", width=12, bg="#ef4444", fg="white",
                                  font=("Segoe UI", 10, "bold"), command=self.root.quit)

        self.btn_calc.pack(side="left", padx=6)
        self.btn_save.pack(side="left", padx=6)
        self.btn_reset.pack(side="left", padx=6)
        self.btn_exit.pack(side="right", padx=6)

        self.add_hover(self.btn_calc, normal="#22c55e", hover="#16a34a")
        self.add_hover(self.btn_save, normal="#f59e0b", hover="#d97706")
        self.add_hover(self.btn_reset, normal="#6366f1", hover="#4f46e5")
        self.add_hover(self.btn_exit, normal="#ef4444", hover="#dc2626")

    def add_hover(self, widget, normal, hover):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal))

    # ---------- logic ----------
    def get_quantities(self):
        q = {}
        for k, var in self.qty_vars.items():
            val = var.get().strip()
            if val == "":
                q[k] = 0
            else:
                try:
                    q[k] = int(val)
                except ValueError:
                    raise ValueError(f"Invalid quantity for '{k}'. Use numbers only.")
        return q

    def calculate_totals(self):
        if not self.customer_name.get().strip():
            messagebox.showerror("Missing Name", "Customer Name is required.")
            self.ent_name.focus_set()
            return

        try:
            q = self.get_quantities()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        self.subtotal = sum(q[k] * PRICES[k] for k in PRICES.keys())
        self.service_charge = self.subtotal * 0.02
        self.tax = self.subtotal * 0.18
        self.discount = self.subtotal * 0.10 if self.subtotal > 1000 else 0.0
        self.total = self.subtotal + self.service_charge + self.tax - self.discount

        self.print_bill(preview_only=True)

    def print_bill(self, preview_only=False):
        self.bill_text.delete(1.0, tk.END)
        now = datetime.now()
        self.bill_text.insert(tk.END, f"Bill Ref: {self.reference_no.get()}\n")
        self.bill_text.insert(tk.END, f"Order Type: {self.order_type.get()}\n")
        self.bill_text.insert(tk.END, f"Customer: {self.customer_name.get().strip()}\n")
        self.bill_text.insert(tk.END, f"Mobile: {self.customer_mobile.get().strip()}\n")
        self.bill_text.insert(tk.END, f"Date: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.bill_text.insert(tk.END, "-" * 48 + "\n")

    
        q = {}
        try:
            q = self.get_quantities()
        except Exception:
            pass

        def line(name, qty, price):
            self.bill_text.insert(tk.END, f"{name:<20} x {qty:<3} = ₹{qty*price:>6}\n")

        mapping = [
            ("Paneer", "paneer"),
            ("Dal", "dal"),
            ("Veg Biryani", "biryani"),
            ("Chicken Biryani", "chicken_biryani"),
            ("Chicken Curry", "chicken"),
            ("Roti", "roti"),
            ("Naan", "naan"),
            ("Masala Dosa", "dosa"),
            ("Rasgulla", "rasgulla"),
            ("Drinks", "drinks"),
        ]
        for label, key in mapping:
            if q.get(key, 0):
                line(label, q[key], PRICES[key])

        self.bill_text.insert(tk.END, "-" * 48 + "\n")
        self.bill_text.insert(tk.END, f"Subtotal             : ₹{self.subtotal:.2f}\n")
        self.bill_text.insert(tk.END, f"Service Charge (2%)  : ₹{self.service_charge:.2f}\n")
        self.bill_text.insert(tk.END, f"Tax (18%)            : ₹{self.tax:.2f}\n")
        self.bill_text.insert(tk.END, f"Discount             : -₹{self.discount:.2f}\n")
        self.bill_text.insert(tk.END, f"TOTAL                : ₹{self.total:.2f}\n")
        if preview_only:
            self.bill_text.insert(tk.END, "\n(Click 'Calculate Total' to refresh. 'Save to Database' to store.)\n")

    def save_to_db(self):
  
        if self.subtotal == 0 and self.total == 0:
            self.calculate_totals()
            if self.subtotal == 0 and self.total == 0:
                messagebox.showwarning("Nothing to Save", "Add some quantities before saving.")
                return

        name = self.customer_name.get().strip()
        if not name:
            messagebox.showerror("Missing Name", "Customer Name is required.")
            return

        try:
            q = self.get_quantities()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        data = (
            self.order_type.get(),
            float(self.subtotal),
            float(self.tax),
            float(self.discount),
            float(self.total),
            name,
            self.customer_mobile.get().strip(),
            datetime.now(),
            self.reference_no.get(),
            q["paneer"], q["dal"], q["roti"], q["biryani"], q["dosa"], q["drinks"],
            q["chicken_biryani"], q["chicken"], q["naan"], q["rasgulla"],
            float(self.service_charge),
        )

        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO orders 
                (order_type, subtotal, tax, discount, total, customer_name, customer_mobile, order_date, reference_no,
                 paneer, dal, roti, biryani, dosa, drinks, chicken_biryani, chicken, naan, rasgulla, service_charge)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                data
            )
            conn.commit()
            conn.close()
            messagebox.showinfo("Saved", "Order saved to database successfully ✅")

            self.reference_no.set(str(random.randint(10000, 99999)))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error: {err}")

    def reset_all(self):
        self.customer_name.set("")
        self.customer_mobile.set("")
        self.order_type.set("Dine-In")
        for v in self.qty_vars.values():
            v.set("")
        self.subtotal = self.tax = self.service_charge = self.discount = self.total = 0.0
        self.reference_no.set(str(random.randint(10000, 99999)))
        self.print_bill(preview_only=True)

# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
