CREATE DATABASE restaurant_billing;
USE restaurant_billing;

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_type VARCHAR(20),
    subtotal FLOAT,
    tax FLOAT,
    discount FLOAT,
    total FLOAT,
    customer_name VARCHAR(100) NOT NULL,
    customer_mobile VARCHAR(20),
    order_date DATETIME,
    reference_no VARCHAR(50),
    paneer INT DEFAULT 0,
    dal INT DEFAULT 0,
    roti INT DEFAULT 0,
    biryani INT DEFAULT 0,
    dosa INT DEFAULT 0,
    drinks INT DEFAULT 0,
    chicken_biryani INT DEFAULT 0,
    chicken INT DEFAULT 0,
    naan INT DEFAULT 0,
    rasgulla INT DEFAULT 0,
    service_charge FLOAT
);
