"""
PDF Price Catalog Generator
Fiyat kataloğu PDF üretimi - çoklu dil ve para birimi desteği
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os


def generate_price_catalog_pdf(distributor, currencies=['USD', 'EUR', 'TRY'], language='tr'):
    """
    Fiyat kataloğu PDF oluştur
    
    Args:
        distributor: Distributor nesnesi
        currencies: Gösterilecek para birimleri listesi
        language: Katalog dili ('tr', 'en', 'ar')
        
    Returns:
        BytesIO: PDF buffer
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#7a001d'),
        spaceAfter=20,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#7a001d'),
        spaceAfter=10
    )
    
    # Title
    title_text = {
        'tr': f'{distributor.name} - Fiyat Listesi',
        'en': f'{distributor.name} - Price List',
        'ar': f'{distributor.name} - قائمة الأسعار'
    }.get(language, 'Price List')
    
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Date
    date_text = {
        'tr': f'Tarih: {datetime.now().strftime("%d.%m.%Y")}',
        'en': f'Date: {datetime.now().strftime("%d.%m.%Y")}',
        'ar': f'التاريخ: {datetime.now().strftime("%d.%m.%Y")}'
    }.get(language, f'Date: {datetime.now().strftime("%d.%m.%Y")}')
    
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Get price list items by category
    from app.models.currency import PriceListItem
    categories = PriceListItem.query.filter_by(
        distributor_id=distributor.id,
        is_active=True
    ).with_entities(PriceListItem.category).distinct().all()
    
    for (category,) in categories:
        # Category heading
        category_names = {
            'hair': {'tr': 'Saç Ekimi', 'en': 'Hair Transplant', 'ar': 'زراعة الشعر'},
            'dental': {'tr': 'Diş Tedavisi', 'en': 'Dental Treatment', 'ar': 'علاج الأسنان'},
            'eye': {'tr': 'Göz Ameliyatları', 'en': 'Eye Surgery', 'ar': 'جراحة العيون'},
            'aesthetic': {'tr': 'Estetik', 'en': 'Aesthetic', 'ar': 'التجميل'},
            'bariatric': {'tr': 'Bariatrik Cerrahi', 'en': 'Bariatric Surgery', 'ar': 'جراحة السمنة'},
            'ivf': {'tr': 'Tüp Bebek', 'en': 'IVF Treatment', 'ar': 'علاج أطفال الأنابيب'},
            'checkup': {'tr': 'Check-Up Paketleri', 'en': 'Check-Up Packages', 'ar': 'باقات الفحص'}
        }
        
        category_name = category_names.get(category, {}).get(language, category.title())
        elements.append(Paragraph(category_name, heading_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Get items for this category
        items = PriceListItem.query.filter_by(
            distributor_id=distributor.id,
            category=category,
            is_active=True
        ).order_by(PriceListItem.display_order.asc()).all()
        
        if not items:
            continue
        
        # Build table data
        header_labels = {
            'tr': 'Hizmet',
            'en': 'Service',
            'ar': 'الخدمة'
        }
        
        table_data = [[header_labels.get(language, 'Service')] + [f'{curr}' for curr in currencies]]
        
        for item in items:
            # Service name
            service_name = getattr(item, f'service_name_{language}', None) or item.service_name_tr
            
            # Prices in each currency
            row = [service_name]
            for curr in currencies:
                price = item.get_price_in_currency(curr)
                if price:
                    from app.utils.currency_service import format_price
                    formatted = format_price(price, curr, language)
                    row.append(formatted)
                else:
                    row.append('-')
            
            table_data.append(row)
        
        # Create table
        col_widths = [8*cm] + [3*cm] * len(currencies)
        table = Table(table_data, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7a001d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
    
    # Footer notes
    footer_text = {
        'tr': 'Not: Fiyatlar güncel döviz kurlarına göre hesaplanmıştır. Detaylı bilgi için lütfen bizimle iletişime geçin.',
        'en': 'Note: Prices are calculated according to current exchange rates. Please contact us for detailed information.',
        'ar': 'ملاحظة: الأسعار محسوبة وفقاً لأسعار الصرف الحالية. يرجى الاتصال بنا للحصول على معلومات مفصلة.'
    }.get(language, 'Note: Prices are subject to change.')
    
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(footer_text, styles['Italic']))
    
    # Contact info
    if distributor.phone or distributor.email:
        contact_text = []
        if distributor.phone:
            contact_text.append(f'Tel: {distributor.phone}')
        if distributor.email:
            contact_text.append(f'Email: {distributor.email}')
        
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(' | '.join(contact_text), styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer


def export_prices_to_excel(distributor, currencies=['USD', 'EUR', 'TRY']):
    """
    Fiyat listesini Excel olarak dışa aktar
    
    Args:
        distributor: Distributor nesnesi
        currencies: Para birimleri
        
    Returns:
        BytesIO: Excel buffer
    """
    try:
        import pandas as pd
        from io import BytesIO
        
        from app.models.currency import PriceListItem
        
        items = PriceListItem.query.filter_by(
            distributor_id=distributor.id,
            is_active=True
        ).order_by(PriceListItem.category, PriceListItem.display_order).all()
        
        data = []
        for item in items:
            row = {
                'Kategori': item.category,
                'Hizmet Kodu': item.service_code,
                'Hizmet (TR)': item.service_name_tr,
                'Hizmet (EN)': item.service_name_en or '',
                'Hizmet (AR)': item.service_name_ar or '',
            }
            
            for curr in currencies:
                price = item.get_price_in_currency(curr)
                row[curr] = price if price else 0
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Fiyat Listesi', index=False)
        
        buffer.seek(0)
        return buffer
        
    except ImportError:
        # Pandas/openpyxl not installed
        return None
