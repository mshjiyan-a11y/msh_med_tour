from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Rect, Line, String
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os

# Global font registration to support Turkish characters (Unicode)
_FONTS_REGISTERED = False
BASE_FONT_NAME = 'Arial'
BOLD_FONT_NAME = 'Arial-Bold'

def _ensure_fonts_registered():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return BASE_FONT_NAME, BOLD_FONT_NAME
    try:
        # Prefer Windows Arial (available on this system) for full Turkish glyph support
        if os.name == 'nt':
            arial = r"C:\\Windows\\Fonts\\arial.ttf"
            arial_bold = r"C:\\Windows\\Fonts\\arialbd.ttf"
            if os.path.exists(arial) and os.path.exists(arial_bold):
                pdfmetrics.registerFont(TTFont(BASE_FONT_NAME, arial))
                pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, arial_bold))
            else:
                # Fallback to DejaVu if available
                djv = r"C:\\Windows\\Fonts\\DejaVuSans.ttf"
                djv_b = r"C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf"
                pdfmetrics.registerFont(TTFont('DejaVuSans', djv))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', djv_b))
                globals()['BASE_FONT_NAME'] = 'DejaVuSans'
                globals()['BOLD_FONT_NAME'] = 'DejaVuSans-Bold'
        else:
            # Common Linux paths for DejaVu
            djv = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            djv_b = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            if os.path.exists(djv) and os.path.exists(djv_b):
                pdfmetrics.registerFont(TTFont('DejaVuSans', djv))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', djv_b))
                globals()['BASE_FONT_NAME'] = 'DejaVuSans'
                globals()['BOLD_FONT_NAME'] = 'DejaVuSans-Bold'
            else:
                # Best-effort fallback to Arial names if installed
                pdfmetrics.registerFont(TTFont(BASE_FONT_NAME, 'arial.ttf'))
                pdfmetrics.registerFont(TTFont(BOLD_FONT_NAME, 'arialbd.ttf'))
        _FONTS_REGISTERED = True
    except Exception:
        # As a last resort, keep defaults; ReportLab base fonts may drop Turkish glyphs
        _FONTS_REGISTERED = True
    return BASE_FONT_NAME, BOLD_FONT_NAME


def get_currency_symbol(currency_code):
    """Convert currency code to symbol"""
    symbols = {'EUR': '€', 'USD': '$', 'TRY': '₺', 'GBP': '£'}
    return symbols.get(currency_code, currency_code)

class EncounterPDFGenerator:
    def __init__(self, encounter, distributor):
        self.encounter = encounter
        self.distributor = distributor
        self.patient = encounter.patient
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        # Ensure Unicode-capable fonts are available
        self.base_font_name, self.bold_font_name = _ensure_fonts_registered()
        # Apply default font to common styles
        try:
            self.styles['Normal'].fontName = self.base_font_name
            self.styles['Heading1'].fontName = self.bold_font_name
            self.styles['Heading2'].fontName = self.bold_font_name
        except Exception:
            pass
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName=self.bold_font_name
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'),
            spaceAfter=12,
            spaceBefore=12,
            fontName=self.bold_font_name
        )
        
    def generate(self):
        """Generate complete PDF report"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header with logo and distributor info
        story.append(self._create_header())
        story.append(Spacer(1, 20))
        
        # Title
        title = Paragraph(f"MUAYİNE RAPORU", self.title_style)
        story.append(title)
        story.append(Spacer(1, 10))
        
        # Patient Info
        story.append(self._create_patient_info())
        story.append(Spacer(1, 20))
        
        # Hair Module - Manuel sorgu kullan
        from app.models import HairAnnotation, HairPatternSelection
        hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
        hair_patterns = HairPatternSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if hair_patterns or hair_annotations:
            story.append(Paragraph("SAÇ EKİMİ", self.heading_style))
            story.extend(self._create_hair_section())
            story.append(Spacer(1, 20))
        
        # Dental Module - Manuel sorgu kullan
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        
        if dental_procedures:
            story.append(Paragraph("DİŞ TEDAVİSİ", self.heading_style))
            story.extend(self._create_dental_section())
            story.append(Spacer(1, 20))
        
        # Eye Module
        # Debug: Manuel sorgu ile kontrol et
        from app.models import EyeRefraction, EyeTreatmentSelection
        eye_refraction_manual = EyeRefraction.query.filter_by(encounter_id=self.encounter.id).first()
        eye_treatments_manual = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if eye_refraction_manual or eye_treatments_manual:
            story.append(Paragraph("GÖZ AMELİYATI", self.heading_style))
            story.extend(self._create_eye_section())
            story.append(Spacer(1, 20))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(self._create_footer())
        
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer
    
    def _create_header(self):
        """Create header with logo and contact info"""
        data = []
        
        # Logo and distributor name
        logo_cell = ""
        try:
            from flask import current_app
            logo_path = None
            # 1) Try uploaded logo (distributor-specific)
            if getattr(self.distributor, 'logo_path', None):
                up_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.distributor.logo_path)
                if os.path.exists(up_path):
                    logo_path = up_path
            # 2) Fallback to global logo from AppSettings
            if not logo_path:
                from app.models.settings import AppSettings
                app_settings = AppSettings.get()
                if app_settings and app_settings.logo_path:
                    global_logo = os.path.join(current_app.config['UPLOAD_FOLDER'], app_settings.logo_path)
                    if os.path.exists(global_logo):
                        logo_path = global_logo
            # 3) Fallback to static logo file if present
            if not logo_path:
                static_logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo.png')
                if os.path.exists(static_logo):
                    logo_path = static_logo
            # 4) Use if any found
            if logo_path:
                logo_cell = Image(logo_path, width=60, height=60)
        except Exception:
            # No logo available or path resolution failed; continue without logo
            pass
        
        contact_info = f"""
        <b>{self.distributor.name}</b><br/>
        {self.distributor.address or ''}<br/>
        {self.distributor.city or ''} {self.distributor.country or ''}<br/>
        Tel: {self.distributor.phone or '-'} | Email: {self.distributor.email}<br/>
        {f'Web: {self.distributor.website}' if self.distributor.website else ''}
        """
        
        contact_para = Paragraph(contact_info, self.styles['Normal'])
        
        header_table = Table(
            [[logo_cell, contact_para]],
            colWidths=[70, None]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        return header_table
    
    def _create_patient_info(self):
        """Create patient information table"""
        data = [
            ['Hasta Adı:', self.patient.full_name, 'Muayene Tarihi:', self.encounter.date.strftime('%d.%m.%Y')],
            ['Telefon:', self.patient.phone or '-', 'Durum:', self.encounter.status.upper()],
            ['Email:', self.patient.email or '-', 'Rapor No:', f'#{self.encounter.id}'],
        ]
        
        table = Table(data, colWidths=[3*cm, 6*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font_name),
            ('FONTNAME', (2, 0), (2, -1), self.bold_font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        return table
    
    def _create_hair_section(self):
        """Create hair transplant section with region diagram"""
        elements = []
        
        # Collect hair regions - Manuel sorgu kullan
        from app.models import HairAnnotation
        hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
        
        regions_data = {}
        total_grafts = 0
        
        for anno in hair_annotations:
            if anno.region_id and anno.region_id != 'general':
                # Extract grafts from label
                try:
                    grafts = int(anno.label.split(':')[1].strip().split()[0]) if ':' in anno.label else 0
                    regions_data[anno.region_id] = {
                        'name': anno.label.split(':')[0] if ':' in anno.label else anno.region_id,
                        'grafts': grafts,
                        'note': anno.note
                    }
                    total_grafts += grafts
                except:
                    pass
        # Create scalp diagram
        if regions_data:
            drawing = self._draw_hair_diagram(regions_data)
            elements.append(drawing)
            elements.append(Spacer(1, 10))
        
        # Create table with region details
        if regions_data:
            table_data = [['Bölge', 'Greft Sayısı', 'Not']]
            
            for region_id, data in regions_data.items():
                table_data.append([
                    data['name'],
                    str(data['grafts']),
                    data.get('note', '-')[:50]
                ])
            
            table_data.append(['TOPLAM', str(total_grafts), ''])
            
            table = Table(table_data, colWidths=[5*cm, 3*cm, 8*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.distributor.color_hex or '#7a001d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
                ('FONTNAME', (0, -1), (-1, -1), self.bold_font_name),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            elements.append(table)
        
        # Hair pattern
        # Manuel sorgu kullan
        from app.models import HairPatternSelection
        hair_patterns = HairPatternSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        for pattern in hair_patterns:
            pattern_text = f"<b>Saç Dökülme Paterni:</b> {pattern.pattern_key}"
            if pattern.note:
                pattern_text += f"<br/><i>{pattern.note}</i>"
            elements.append(Paragraph(pattern_text, self.styles['Normal']))
        
        return elements
    
    def _draw_hair_diagram(self, regions_data):
        """Draw scalp diagram with highlighted regions"""
        drawing = Drawing(400, 200)
        
        # Define region coordinates (simplified top view of scalp)
        region_coords = {
            'frontal': (200, 150, 60, 40, 'Ön'),
            'midscalp': (200, 110, 60, 30, 'Orta'),
            'crown': (200, 70, 50, 50, 'Tepe'),
            'temporal_left': (130, 130, 40, 30, 'Sol Şakak'),
            'temporal_right': (270, 130, 40, 30, 'Sağ Şakak'),
            'vertex': (200, 30, 40, 30, 'Arka'),
        }

        drawing.add(Circle(200, 100, 90, fillColor=colors.HexColor('#f5f5f5'), strokeColor=colors.grey))
        
        # Draw and highlight selected regions
        for region_id, (x, y, w, h, label) in region_coords.items():
            if region_id in regions_data:
                # Highlighted region
                color = colors.HexColor(self.distributor.color_hex or '#7a001d')
                drawing.add(Rect(x-w/2, y-h/2, w, h, 
                                fillColor=color, 
                                strokeColor=colors.black, 
                                strokeWidth=2,
                                fillOpacity=0.6))
                # Grafts count
                drawing.add(String(x, y-5, 
                                  f"{regions_data[region_id]['grafts']}", 
                                  fontSize=10, 
                                  fillColor=colors.white,
                                  textAnchor='middle'))
            else:
                # Non-selected region (outline only)
                drawing.add(Rect(x-w/2, y-h/2, w, h, 
                                fillColor=None, 
                                strokeColor=colors.lightgrey, 
                                strokeWidth=1,
                                strokeDashArray=[2, 2]))
            
            # Label
            drawing.add(String(x, y-h/2-12, label, 
                              fontSize=8, 
                              fillColor=colors.grey,
                              textAnchor='middle',
                              fontName=self.base_font_name))
        
        return drawing
    
    def _create_dental_section(self):
        """Create dental section with tooth diagram"""
        elements = []
        
        # Collect treated teeth
        treated_teeth = {}
        total_price = 0
        
        # Manuel sorgu kullan
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        
        for proc in dental_procedures:
            if proc.tooth_no not in treated_teeth:
                treated_teeth[proc.tooth_no] = []
            treated_teeth[proc.tooth_no].append({
                'treatment': proc.treatment_type,
                'price': proc.price,
                'note': proc.note
            })
            total_price += proc.price or 0
        
        # Draw tooth diagram
        drawing = self._draw_dental_diagram(treated_teeth)
        elements.append(drawing)
        elements.append(Spacer(1, 15))
        
        # Treatment details table
        table_data = [['Diş No', 'Tedavi', 'Fiyat', 'Not']]
        
        for tooth_no in sorted(treated_teeth.keys()):
            for proc in treated_teeth[tooth_no]:
                table_data.append([
                    str(tooth_no),
                    proc['treatment'],
                    f"{proc['price']:.2f} TL" if proc['price'] else '-',
                    proc.get('note', '-')[:40]
                ])
        
        table_data.append(['', 'TOPLAM', f"{total_price:.2f} TL", ''])
        
        table = Table(table_data, colWidths=[2*cm, 6*cm, 3*cm, 5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.distributor.color_hex or '#7a001d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, -1), (2, -1), self.bold_font_name),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _draw_dental_diagram(self, treated_teeth):
        """Draw dental chart with highlighted teeth"""
        drawing = Drawing(500, 250)
        
        # Tooth positions (FDI notation)
        upper_right = list(range(18, 10, -1))  # 18-11
        upper_left = list(range(21, 29))       # 21-28
        lower_right = list(range(48, 40, -1))  # 48-41
        lower_left = list(range(31, 39))       # 31-38
        
        tooth_width = 25
        tooth_height = 35
        gap = 3
        
        def draw_tooth_row(teeth, start_x, start_y, label_top=True):
            x = start_x
            for tooth_no in teeth:
                # Check if tooth is treated
                if tooth_no in treated_teeth:
                    fill_color = colors.HexColor(self.distributor.color_hex or '#7a001d')
                    stroke_width = 2
                else:
                    fill_color = colors.white
                    stroke_width = 0.5
                
                # Draw tooth
                drawing.add(Rect(x, start_y, tooth_width, tooth_height,
                                fillColor=fill_color,
                                strokeColor=colors.black,
                                strokeWidth=stroke_width))
                
                # Tooth number
                label_y = start_y + tooth_height + 5 if label_top else start_y - 10
                drawing.add(String(x + tooth_width/2, label_y,
                                  str(tooth_no),
                                  fontSize=8,
                                  fillColor=colors.black,
                                  textAnchor='middle'))
                
                x += tooth_width + gap
        
        # Draw all quadrants
        start_x = 50
        
        # Upper jaw
        draw_tooth_row(upper_right, start_x, 150, label_top=True)
        draw_tooth_row(upper_left, start_x + len(upper_right) * (tooth_width + gap) + 10, 150, label_top=True)
        
        # Lower jaw
        draw_tooth_row(lower_right, start_x, 100, label_top=False)
        draw_tooth_row(lower_left, start_x + len(lower_right) * (tooth_width + gap) + 10, 100, label_top=False)
        
        # Labels
        drawing.add(String(250, 210, 'ÜST ÇENE', fontSize=10, fillColor=colors.grey, textAnchor='middle', fontName=self.bold_font_name))
        drawing.add(String(250, 80, 'ALT ÇENE', fontSize=10, fillColor=colors.grey, textAnchor='middle', fontName=self.bold_font_name))
        
        return drawing
    
    def _create_eye_section(self):
        """Create eye surgery section with refraction data"""
        elements = []
        
        # Refraction data - Manuel sorgu kullan
        from app.models import EyeRefraction
        ref = EyeRefraction.query.filter_by(encounter_id=self.encounter.id).first()
        
        if ref:
            
            elements.append(Paragraph("<b>Göz Muayene Sonuçları (Refraksiyon Değerleri)</b>", self.styles['Normal']))
            elements.append(Spacer(1, 8))
            
            refraction_data = [
                ['', 'SPH (Küre)', 'CYL (Silindir)', 'AXIS (Eksen)', 'Planlanan Prosedür'],
                ['Sağ Göz (OD)', 
                 f"{ref.od_sph:+.2f}" if ref.od_sph is not None else '-',
                 f"{ref.od_cyl:+.2f}" if ref.od_cyl is not None else '-',
                 f"{ref.od_ax}°" if ref.od_ax is not None else '-',
                 ref.planned_procedure or '-'],
                ['Sol Göz (OS)',
                 f"{ref.os_sph:+.2f}" if ref.os_sph is not None else '-',
                 f"{ref.os_cyl:+.2f}" if ref.os_cyl is not None else '-',
                 f"{ref.os_ax}°" if ref.os_ax is not None else '-',
                 ref.planned_procedure or '-']
            ]
            
            table = Table(refraction_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2.5*cm, 5.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.distributor.color_hex or '#7a001d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
                ('FONTNAME', (0, 1), (0, -1), self.bold_font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 12))
            
            # Refraksiyon notları varsa göster
            if ref.note:
                elements.append(Paragraph(f"<b>Muayene Notları:</b> {ref.note}", self.styles['Normal']))
                elements.append(Spacer(1, 10))
        
        # Eye treatments - Manuel sorgu kullan
        from app.models import EyeTreatmentSelection
        eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if eye_treatments:
            elements.append(Paragraph("<b>Önerilen Tedavi ve Fiyatlandırma:</b>", self.styles['Normal']))
            elements.append(Spacer(1, 8))
            
            treatment_data = [['Tedavi', 'Göz', 'Fiyat', 'Not']]
            
            for treatment in eye_treatments:
                side_map = {'OD': 'Sağ Göz', 'OS': 'Sol Göz', 'OU': 'Her İki Göz'}
                side_text = side_map.get(treatment.side, treatment.side or '-')
                
                price_text = '-'
                if treatment.price:
                    currency_symbol = {'EUR': '€', 'USD': '$', 'TRY': '₺', 'GBP': '£'}.get(treatment.currency, treatment.currency)
                    if treatment.discount_enabled and treatment.discounted_price:
                        price_text = f"{treatment.discounted_price:.2f} {currency_symbol}"
                    else:
                        price_text = f"{treatment.price:.2f} {currency_symbol}"
                
                treatment_data.append([
                    treatment.title or '-',
                    side_text,
                    price_text,
                    treatment.note[:30] + '...' if treatment.note and len(treatment.note) > 30 else (treatment.note or '-')
                ])
            
            treatment_table = Table(treatment_data, colWidths=[6*cm, 3*cm, 3*cm, 4*cm])
            treatment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.distributor.color_hex or '#7a001d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(treatment_table)
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_footer(self):
        """Create footer with distributor info and social media"""
        footer_text = ""
        
        if self.distributor.pdf_footer_text:
            footer_text += f"{self.distributor.pdf_footer_text}<br/>"
        
        # Contact info
        contacts = []
        if self.distributor.phone:
            contacts.append(f"☎ {self.distributor.phone}")
        if self.distributor.whatsapp:
            contacts.append(f"WhatsApp: {self.distributor.whatsapp}")
        if self.distributor.email:
            contacts.append(f"✉ {self.distributor.email}")
        
        if contacts:
            footer_text += " | ".join(contacts) + "<br/>"
        
        # Social media
        social = []
        if self.distributor.facebook:
            social.append(f"Facebook: {self.distributor.facebook.split('/')[-1]}")
        if self.distributor.instagram:
            social.append(f"Instagram: {self.distributor.instagram}")
        if self.distributor.website:
            social.append(f"🌐 {self.distributor.website}")
        
        if social:
            footer_text += " | ".join(social) + "<br/>"
        
        # Legal info
        legal = []
        if self.distributor.hospital_license:
            legal.append(f"Ruhsat No: {self.distributor.hospital_license}")
        if self.distributor.tax_number:
            legal.append(f"Vergi No: {self.distributor.tax_number}")
        
        if legal:
            footer_text += "<br/>" + " | ".join(legal)
        
        footer_text += f"<br/><br/><i>Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        return Paragraph(footer_text, footer_style)


class HotelReservationPDFGenerator:
    def __init__(self, reservation, distributor):
        from app.models import HotelReservation
        self.reservation = reservation
        self.distributor = distributor
        self.patient = reservation.patient
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        # Ensure Unicode-capable fonts are available
        self.base_font_name, self.bold_font_name = _ensure_fonts_registered()
        self.styles['Normal'].fontName = self.base_font_name
        self.styles['Heading1'].fontName = self.bold_font_name
        self.styles['Heading2'].fontName = self.bold_font_name

        self.title_style = ParagraphStyle(
            'ReservationTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=self.bold_font_name
        )
        self.heading_style = ParagraphStyle(
            'ReservationHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'),
            spaceAfter=10,
            spaceBefore=10,
            fontName=self.bold_font_name
        )

    def generate(self):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        story = []
        # Header
        story.append(self._create_header())
        story.append(Spacer(1, 15))
        # Title
        story.append(Paragraph('OTEL REZERVASYON ONAYI', self.title_style))
        story.append(Spacer(1, 10))
        # Patient info
        story.append(self._patient_info())
        story.append(Spacer(1, 12))
        # Reservation details
        story.append(Paragraph('Rezervasyon Bilgileri', self.heading_style))
        story.append(self._reservation_info())
        story.append(Spacer(1, 12))
        # Flight/transfer
        story.append(Paragraph('Ulaşım Bilgileri', self.heading_style))
        story.append(self._transfer_info())
        story.append(Spacer(1, 20))
        # Footer
        story.append(self._footer())
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer

    def _create_header(self):
        # Reuse from EncounterPDFGenerator
        enc_like = EncounterPDFGenerator.__dict__
        return EncounterPDFGenerator._create_header(self)

    def _patient_info(self):
        data = [
            ['Hasta:', self.patient.full_name, 'Pasaport:', self.patient.passport_number or '-'],
            ['Telefon:', self.patient.phone or '-', 'E-posta:', self.patient.email or '-'],
        ]
        table = Table(data, colWidths=[3*cm, 6*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font_name),
            ('FONTNAME', (2, 0), (2, -1), self.bold_font_name),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _reservation_info(self):
        r = self.reservation
        data = [
            ['Otel Adı', r.hotel_name, 'Yıldız', str(r.hotel_stars or '-')],
            ['Giriş', r.check_in.strftime('%d.%m.%Y'), 'Çıkış', r.check_out.strftime('%d.%m.%Y')],
            ['Gece Sayısı', str(r.nights or '-'), 'Oda Tipi', r.room_type or '-'],
            ['Gecelik Fiyat', f"{(r.price_per_night or 0):.2f} €", 'Otel Toplam', f"{(r.total_hotel_cost or 0):.2f} €"],
            ['Transfer Ücreti', f"{(r.transfer_cost or 0):.2f} €", 'Genel Toplam', f"{r.total_cost:.2f} €"],
            ['Durum', r.status.capitalize(), 'Onay No', r.confirmation_number or '-'],
        ]
        table = Table(data, colWidths=[4*cm, 6*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return table

    def _transfer_info(self):
        r = self.reservation
        rows = [
            ['Transfer Dahil', 'Evet' if r.transfer_included else 'Hayır', 'Transfer Tipi', (r.transfer_type or '-').replace('_',' ').title()],
            ['Havaalanı', f"{r.airport_code or '-'} {r.airport_name or ''}", 'Uçuş No', r.flight_number or '-'],
            ['Varış', r.arrival_time.strftime('%d.%m.%Y %H:%M') if r.arrival_time else '-', 'Dönüş', r.departure_time.strftime('%d.%m.%Y %H:%M') if r.departure_time else '-'],
            ['Kahvaltı', 'Dahil' if r.breakfast_included else 'Hariç', 'WiFi', 'Dahil' if r.wifi_included else 'Hariç'],
        ]
        table = Table(rows, colWidths=[4*cm, 6*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _footer(self):
        return EncounterPDFGenerator._create_footer(self)


class QuotePDFGenerator:
    """Professional price quote PDF for an encounter"""
    def __init__(self, encounter, distributor):
        self.encounter = encounter
        self.distributor = distributor
        self.patient = encounter.patient
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        # Ensure Unicode-capable fonts
        self.base_font_name, self.bold_font_name = _ensure_fonts_registered()
        self.styles['Normal'].fontName = self.base_font_name
        self.styles['Heading1'].fontName = self.bold_font_name
        self.styles['Heading2'].fontName = self.bold_font_name
        self.title_style = ParagraphStyle(
            'QuoteTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=self.bold_font_name
        )
        self.section_style = ParagraphStyle(
            'QuoteSection', parent=self.styles['Heading2'], fontSize=14,
            textColor=colors.HexColor(distributor.color_hex or '#7a001d'), spaceAfter=10, spaceBefore=10,
            fontName=self.bold_font_name
        )

    def generate(self):
        doc = SimpleDocTemplate(
            self.buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
        )
        story = []
        story.append(self._header())
        story.append(Spacer(1, 10))
        story.append(Paragraph('FİYAT TEKLİFİ', self.title_style))
        story.append(Spacer(1, 8))
        story.append(self._patient_and_quote_info())
        story.append(Spacer(1, 12))
        items, subtotal = self._collect_items()
        story.append(self._items_table(items, subtotal))
        story.append(Spacer(1, 12))
        story.append(self._notes())
        story.append(Spacer(1, 16))
        story.append(self._footer())
        doc.build(story)
        self.buffer.seek(0)
        return self.buffer

    def _header(self):
        return EncounterPDFGenerator._create_header(self)

    def _footer(self):
        return EncounterPDFGenerator._create_footer(self)

    def _patient_and_quote_info(self):
        data = [
            ['Hasta', self.patient.full_name, 'Tarih', (self.encounter.date or self.encounter.created_at).strftime('%d.%m.%Y')],
            ['Telefon', self.patient.phone or '-', 'E-posta', self.patient.email or '-'],
            ['Teklif No', f"Q-{self.encounter.id}", 'Geçerlilik', '30 gün'],
        ]
        table = Table(data, colWidths=[3*cm, 6*cm, 3*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font_name),
            ('FONTNAME', (2, 0), (2, -1), self.bold_font_name),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return table

    def _collect_items(self):
        """Aggregate priced items from encounter (dental, eye, hair transplant)"""
        items = [['Açıklama', 'Adet', 'Birim Fiyat', 'Tutar']]
        subtotal_by_currency = {}

        # Hair transplant (if price configured)
        if getattr(self.encounter, 'hair_annotations', None) and self.distributor.price_per_graft:
            total_grafts = 0
            # Manuel sorgu kullan
            from app.models import HairAnnotation
            hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
            
            for anno in hair_annotations:
                if ':' in anno.label:
                    # Parse "Zone: 500 grafts" format
                    try:
                        graft_text = anno.label.split(':')[1].strip().split()[0]
                        total_grafts += int(graft_text)
                    except (IndexError, ValueError):
                        pass
            
            if total_grafts > 0:
                currency = self.distributor.currency or 'EUR'
                currency_symbol = get_currency_symbol(currency)
                price_per_graft = float(self.distributor.price_per_graft)
                total = total_grafts * price_per_graft
                items.append([
                    f"Saç Ekimi - {total_grafts} greft",
                    '1',
                    f"{price_per_graft:.2f} {currency_symbol}",
                    f"{total:.2f} {currency_symbol}"
                ])
                subtotal_by_currency[currency] = subtotal_by_currency.get(currency, 0) + total

        # Dental procedures - Manuel sorgu kullan
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        
        if dental_procedures:
            for proc in dental_procedures:
                price = float(proc.price or 0)
                if price:
                    currency = getattr(proc, 'currency', None) or 'EUR'
                    currency_symbol = get_currency_symbol(currency)
                    items.append([
                        f"Diş {proc.tooth_no} - {proc.treatment_type}",
                        '1',
                        f"{price:.2f} {currency_symbol}",
                        f"{price:.2f} {currency_symbol}"
                    ])
                    subtotal_by_currency[currency] = subtotal_by_currency.get(currency, 0) + price

        # Eye treatments
        if getattr(self.encounter, 'eye_treatments', None):
            # Manuel sorgu kullan
            from app.models import EyeTreatmentSelection
            eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
            
            for tr in eye_treatments:
                price = float(tr.price or 0)
                if price:
                    currency = getattr(tr, 'currency', None) or 'EUR'
                    currency_symbol = get_currency_symbol(currency)
                    items.append([
                        f"{tr.title} ({tr.side})",
                        '1',
                        f"{price:.2f} {currency_symbol}",
                        f"{price:.2f} {currency_symbol}"
                    ])
                    subtotal_by_currency[currency] = subtotal_by_currency.get(currency, 0) + price

        # If no priced items, include a placeholder
        if len(items) == 1:
            items.append(['Muayene ve değerlendirme', '1', '0.00', '0.00'])

        return items, subtotal_by_currency

    def _items_table(self, items, subtotal_by_currency):
        table = Table(items, colWidths=[9*cm, 2*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.distributor.color_hex or '#7a001d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font_name),
            ('ALIGN', (-3, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        # Summary rows
        summary_rows = []
        for currency, amount in sorted(subtotal_by_currency.items()):
            currency_symbol = get_currency_symbol(currency)
            summary_rows.append(['Toplam', f"{amount:.2f} {currency_symbol}"])
        
        if not summary_rows:
            summary_rows = [['Toplam', '0.00 €']]
        
        summary = Table(summary_rows, colWidths=[14*cm, 3*cm])
        summary.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font_name),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), self.bold_font_name),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        wrapper = []
        wrapper.append(table)
        wrapper.append(Spacer(1, 8))
        wrapper.append(summary)
        return wrapper

    def _notes(self):
        text = (
            "<b>Açıklamalar:</b><br/>")
        text += ("• Bu teklif düzenleme tarihinden itibaren 30 gün geçerlidir.<br/>"
                 "• Fiyatlara KDV dahil değildir (varsa).<br/>"
                 "• Randevu ve operasyon planlaması için ön ödeme talep edilebilir.<br/>")
        return Paragraph(text, self.styles['Normal'])
