CREATE DATABASE IF NOT EXISTS restaurant_billing;
USE restaurant_billing;

CREATE TABLE IF NOT EXISTS menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category ENUM('Snacks','Main Course','Drinks','Desserts') NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    gst DECIMAL(5,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    order_type ENUM('Dine-In','Takeaway') NOT NULL DEFAULT 'Dine-In',
    payment_method ENUM('Cash','Card','UPI') NOT NULL DEFAULT 'Cash',
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    tax DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price DECIMAL(10,2) NOT NULL,
    gst DECIMAL(5,2) DEFAULT 0.00,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (menu_item_id) REFERENCES menu(id)
);

INSERT INTO menu (name, category, price, gst) VALUES
('French Fries', 'Snacks', 80.00, 5.00),
('Pizza', 'Snacks', 250.00, 12.00),
('Burger', 'Snacks', 150.00, 8.00),
('Veg Biryani', 'Main Course', 180.00, 5.00),
('Chicken Biryani', 'Main Course', 220.00, 5.00),
('Coke', 'Drinks', 50.00, 18.00),
('Cold Coffee', 'Drinks', 120.00, 18.00),
('Ice Cream', 'Desserts', 100.00, 5.00);

