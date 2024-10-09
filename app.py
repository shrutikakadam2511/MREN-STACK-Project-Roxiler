from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sold = db.Column(db.Boolean, default=False)
    category = db.Column(db.String(100), nullable=False)
    dateOfSale = db.Column(db.DateTime, nullable=False)

# Helper function to extract month from date
def extract_month(date):
    return datetime.strptime(date, '%Y-%m-%d').month

# API to initialize the database and seed data from third-party API
@app.route('/initialize_db', methods=['GET'])
def initialize_db():
    db.create_all()  # Create the database tables
    
    # Fetch data from third-party API
    response = requests.get('https://s3.amazonaws.com/roxiler.com/product_transaction.json')
    data = response.json()

    # Insert data into the database
    for item in data:
        transaction = Transaction(
            title=item['title'],
            description=item['description'],
            price=item['price'],
            sold=item['sold'],
            category=item['category'],
            dateOfSale=datetime.strptime(item['dateOfSale'], '%Y-%m-%d')
        )
        db.session.add(transaction)
    db.session.commit()
    return jsonify({"message": "Database initialized and data seeded"}), 200

# API to list all transactions with pagination and search
@app.route('/transactions', methods=['GET'])
def list_transactions():
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    query = Transaction.query
    if search:
        query = query.filter((Transaction.title.like(f'%{search}%')) |
                             (Transaction.description.like(f'%{search}%')) |
                             (Transaction.price == float(search) if search.isdigit() else False))

    transactions = query.paginate(page, per_page, False).items
    result = [{"id": t.id, "title": t.title, "description": t.description, "price": t.price,
               "sold": t.sold, "category": t.category, "dateOfSale": t.dateOfSale} for t in transactions]
    
    return jsonify(result), 200

# API for statistics (total sale amount, sold, and not sold items)
@app.route('/statistics', methods=['GET'])
def get_statistics():
    month = int(request.args.get('month'))
    
    transactions = Transaction.query.filter(db.extract('month', Transaction.dateOfSale) == month).all()
    
    total_sales = sum(t.price for t in transactions if t.sold)
    sold_items = sum(1 for t in transactions if t.sold)
    not_sold_items = sum(1 for t in transactions if not t.sold)

    return jsonify({
        "total_sale_amount": total_sales,
        "total_sold_items": sold_items,
        "total_not_sold_items": not_sold_items
    }), 200

# API for bar chart data (price ranges for the selected month)
@app.route('/barchart', methods=['GET'])
def bar_chart():
    month = int(request.args.get('month'))

    transactions = Transaction.query.filter(db.extract('month', Transaction.dateOfSale) == month).all()

    price_ranges = {
        "0-100": 0, "101-200": 0, "201-300": 0, "301-400": 0, "401-500": 0,
        "501-600": 0, "601-700": 0, "701-800": 0, "801-900": 0, "901-above": 0
    }

    for t in transactions:
        price = t.price
        if price <= 100:
            price_ranges["0-100"] += 1
        elif price <= 200:
            price_ranges["101-200"] += 1
        elif price <= 300:
            price_ranges["201-300"] += 1
        elif price <= 400:
            price_ranges["301-400"] += 1
        elif price <= 500:
            price_ranges["401-500"] += 1
        elif price <= 600:
            price_ranges["501-600"] += 1
        elif price <= 700:
            price_ranges["601-700"] += 1
        elif price <= 800:
            price_ranges["701-800"] += 1
        elif price <= 900:
            price_ranges["801-900"] += 1
        else:
            price_ranges["901-above"] += 1

    return jsonify(price_ranges), 200

# API for pie chart data (unique categories and item counts for the selected month)
@app.route('/piechart', methods=['GET'])
def pie_chart():
    month = int(request.args.get('month'))

    transactions = Transaction.query.filter(db.extract('month', Transaction.dateOfSale) == month).all()
    
    category_count = {}
    for t in transactions:
        if t.category in category_count:
            category_count[t.category] += 1
        else:
            category_count[t.category] = 1

    return jsonify(category_count), 200

# API to fetch and combine data from statistics, bar chart, and pie chart APIs
@app.route('/combined', methods=['GET'])
def combined_response():
    month = request.args.get('month')

    statistics = get_statistics().get_json()
    barchart = bar_chart().get_json()
    piechart = pie_chart().get_json()

    combined_data = {
        "statistics": statistics,
        "bar_chart": barchart,
        "pie_chart": piechart
    }

    return jsonify(combined_data), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database tables are created when app starts
    app.run(debug=True)
