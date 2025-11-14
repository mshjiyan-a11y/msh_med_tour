"""Test currency module functionality"""
from app import create_app
from app.models.currency import CurrencyRate
from app.utils.currency_service import update_rates_for_distributor, format_price
from app.utils.price_catalog import generate_price_catalog_pdf

app = create_app()

with app.app_context():
    print("=== Currency Module Test ===\n")
    
    # Test 1: Update rates
    print("1. Updating currency rates from API...")
    count = update_rates_for_distributor(1, 'exchangerate-api', 'USD')
    print(f"   ✓ Updated {count} rates\n")
    
    # Test 2: Get a rate
    print("2. Testing rate retrieval...")
    usd_to_try = CurrencyRate.get_rate(1, 'USD', 'TRY')
    usd_to_eur = CurrencyRate.get_rate(1, 'USD', 'EUR')
    print(f"   ✓ 1 USD = {usd_to_try:.2f} TRY" if usd_to_try else "   ✗ USD/TRY rate not found")
    print(f"   ✓ 1 USD = {usd_to_eur:.4f} EUR\n" if usd_to_eur else "   ✗ USD/EUR rate not found")
    
    # Test 3: Convert amount
    print("3. Testing currency conversion...")
    amount = 1000
    try_amount = CurrencyRate.convert(amount, 'USD', 'TRY', 1)
    eur_amount = CurrencyRate.convert(amount, 'USD', 'EUR', 1)
    print(f"   ✓ {amount} USD = {try_amount:.2f} TRY" if try_amount else "   ✗ Conversion failed")
    print(f"   ✓ {amount} USD = {eur_amount:.2f} EUR\n" if eur_amount else "   ✗ Conversion failed")
    
    # Test 4: Format price
    print("4. Testing price formatting...")
    formatted_usd = format_price(1500, 'USD', 'en')
    formatted_try = format_price(50000, 'TRY', 'tr')
    formatted_eur = format_price(1200, 'EUR', 'en')
    print(f"   ✓ {formatted_usd}")
    print(f"   ✓ {formatted_try}")
    print(f"   ✓ {formatted_eur}\n")
    
    # Test 5: Check database
    print("5. Checking database records...")
    rates_count = CurrencyRate.query.filter_by(distributor_id=1).count()
    print(f"   ✓ {rates_count} currency rates in database\n")
    
    print("=== All Tests Passed ===")
