# Currency & Pricing Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.currency import CurrencyRate, PriceListItem
from app.utils.currency_service import (
    update_rates_for_distributor, 
    get_conversion_preview,
    format_price,
    SUPPORTED_CURRENCIES
)
from app.utils.price_catalog import generate_price_catalog_pdf, export_prices_to_excel
from datetime import datetime

bp = Blueprint('currency', __name__, url_prefix='/currency')


@bp.route('/rates')
@login_required
def currency_rates():
    """Döviz kurları yönetimi"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok', 'danger')
        return redirect(url_for('main.dashboard'))
    
    rates = CurrencyRate.query.filter_by(
        distributor_id=current_user.distributor_id
    ).order_by(CurrencyRate.base_currency, CurrencyRate.target_currency).all()
    
    return render_template('currency/rates.html', rates=rates, supported_currencies=SUPPORTED_CURRENCIES)


@bp.route('/rates/update', methods=['POST'])
@login_required
def update_rates():
    """Kurları güncelle"""
    if not current_user.is_admin():
        flash('Bu işlemi yapmaya yetkiniz yok', 'danger')
        return redirect(url_for('currency.currency_rates'))
    
    try:
        from app.models.settings import AppSettings
        settings = AppSettings.get(current_user.distributor_id)
        base = getattr(settings, 'base_currency', 'USD')
        source = getattr(settings, 'currency_api_source', 'exchangerate-api')
        
        count = update_rates_for_distributor(
            current_user.distributor_id,
            source=source,
            base_currency=base
        )
        
        flash(f'{count} kur başarıyla güncellendi', 'success')
        
    except Exception as e:
        flash(f'Kur güncelleme hatası: {str(e)}', 'danger')
    
    return redirect(url_for('currency.currency_rates'))


@bp.route('/rates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_rate(id):
    """Kur düzenle (manuel)"""
    if not current_user.is_admin():
        abort(403)
    
    rate = CurrencyRate.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            new_rate = float(request.form.get('rate'))
            rate.rate = new_rate
            rate.is_manual = True
            rate.last_updated = datetime.utcnow()
            rate.source = 'manual'
            
            db.session.commit()
            flash('Kur güncellendi', 'success')
            return redirect(url_for('currency.currency_rates'))
            
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    
    return render_template('currency/edit_rate.html', rate=rate)


@bp.route('/price-list')
@login_required
def price_list():
    """Fiyat listesi yönetimi"""
    if not current_user.is_admin():
        flash('Bu sayfaya erişim yetkiniz yok', 'danger')
        return redirect(url_for('main.dashboard'))
    
    category = request.args.get('category', '')
    
    query = PriceListItem.query.filter_by(distributor_id=current_user.distributor_id)
    
    if category:
        query = query.filter_by(category=category)
    
    items = query.order_by(PriceListItem.category, PriceListItem.display_order).all()
    
    return render_template('currency/price_list.html', items=items)


@bp.route('/price-list/add', methods=['GET', 'POST'])
@login_required
def add_price_item():
    """Fiyat listesine ürün ekle"""
    if not current_user.is_admin():
        abort(403)
    
    if request.method == 'POST':
        try:
            item = PriceListItem(
                distributor_id=current_user.distributor_id,
                category=request.form.get('category'),
                service_code=request.form.get('service_code'),
                service_name_tr=request.form.get('service_name_tr'),
                service_name_en=request.form.get('service_name_en'),
                service_name_ar=request.form.get('service_name_ar'),
                description=request.form.get('description'),
                base_price=float(request.form.get('base_price')),
                currency=request.form.get('currency', 'USD'),
                is_active=request.form.get('is_active') == 'on',
                is_featured=request.form.get('is_featured') == 'on',
                display_order=int(request.form.get('display_order', 0))
            )
            
            db.session.add(item)
            db.session.commit()
            
            flash('Fiyat listesine eklendi', 'success')
            return redirect(url_for('currency.price_list'))
            
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    
    return render_template('currency/price_item_form.html', item=None, supported_currencies=SUPPORTED_CURRENCIES)


@bp.route('/price-list/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_price_item(id):
    """Fiyat düzenle"""
    if not current_user.is_admin():
        abort(403)
    
    item = PriceListItem.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            item.category = request.form.get('category')
            item.service_code = request.form.get('service_code')
            item.service_name_tr = request.form.get('service_name_tr')
            item.service_name_en = request.form.get('service_name_en')
            item.service_name_ar = request.form.get('service_name_ar')
            item.description = request.form.get('description')
            item.base_price = float(request.form.get('base_price'))
            item.currency = request.form.get('currency', 'USD')
            item.is_active = request.form.get('is_active') == 'on'
            item.is_featured = request.form.get('is_featured') == 'on'
            item.display_order = int(request.form.get('display_order', 0))
            item.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Fiyat güncellendi', 'success')
            return redirect(url_for('currency.price_list'))
            
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    
    return render_template('currency/price_item_form.html', item=item, supported_currencies=SUPPORTED_CURRENCIES)


@bp.route('/catalog/pdf')
@login_required
def generate_catalog_pdf():
    """PDF fiyat kataloğu oluştur"""
    currencies = request.args.getlist('currencies') or ['USD', 'EUR', 'TRY']
    language = request.args.get('language', 'tr')
    
    try:
        pdf_buffer = generate_price_catalog_pdf(
            current_user.distributor,
            currencies=currencies,
            language=language
        )
        
        filename = f'price_catalog_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'PDF oluşturma hatası: {str(e)}', 'danger')
        return redirect(url_for('currency.price_list'))


@bp.route('/catalog/excel')
@login_required
def generate_catalog_excel():
    """Excel fiyat kataloğu oluştur"""
    currencies = request.args.getlist('currencies') or ['USD', 'EUR', 'TRY']
    
    try:
        excel_buffer = export_prices_to_excel(
            current_user.distributor,
            currencies=currencies
        )
        
        if not excel_buffer:
            flash('Excel export için pandas gerekli', 'warning')
            return redirect(url_for('currency.price_list'))
        
        filename = f'price_list_{datetime.now().strftime("%Y%m%d")}.xlsx'
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Excel oluşturma hatası: {str(e)}', 'danger')
        return redirect(url_for('currency.price_list'))


@bp.route('/api/convert', methods=['POST'])
@login_required
def api_convert():
    """AJAX döviz dönüşüm API'si"""
    data = request.get_json()
    
    amount = float(data.get('amount', 0))
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')
    
    converted = CurrencyRate.convert(
        amount,
        from_currency,
        to_currency,
        current_user.distributor_id
    )
    
    return jsonify({
        'success': True,
        'converted': converted,
        'formatted': format_price(converted, to_currency) if converted else None
    })


@bp.route('/api/preview', methods=['POST'])
@login_required
def api_preview():
    """Çoklu para birimi önizleme"""
    data = request.get_json()
    
    amount = float(data.get('amount', 0))
    from_currency = data.get('from_currency')
    to_currencies = data.get('to_currencies', ['USD', 'EUR', 'TRY'])
    
    preview = get_conversion_preview(
        amount,
        from_currency,
        to_currencies,
        current_user.distributor_id
    )
    
    formatted_preview = {}
    for curr, value in preview.items():
        formatted_preview[curr] = {
            'value': value,
            'formatted': format_price(value, curr)
        }
    
    return jsonify({
        'success': True,
        'preview': formatted_preview
    })
