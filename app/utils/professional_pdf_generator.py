from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os

# Font registration
_FONTS_REGISTERED = False

def _ensure_fonts_registered():
    """Register Unicode-capable fonts (Arial or DejaVu) so Turkish characters (ş, ğ, İ) render correctly."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        # Assume Arial registered; fall back to Helvetica if not.
        if pdfmetrics.getFont('Arial'):
            return 'Arial', 'Arial-Bold'
        elif pdfmetrics.getFont('DejaVu'):
            return 'DejaVu', 'DejaVu-Bold'
        return 'Helvetica', 'Helvetica-Bold'
    try:
        if os.name == 'nt':
            arial = r"C:\Windows\Fonts\arial.ttf"
            arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
            if os.path.exists(arial) and os.path.exists(arial_bold):
                pdfmetrics.registerFont(TTFont('Arial', arial))
                pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold))
                _FONTS_REGISTERED = True
                return 'Arial', 'Arial-Bold'
        # Optional custom font (place files under app/static/fonts)
        dejavu = os.path.join('app', 'static', 'fonts', 'DejaVuSans.ttf')
        dejavu_bold = os.path.join('app', 'static', 'fonts', 'DejaVuSans-Bold.ttf')
        if os.path.exists(dejavu) and os.path.exists(dejavu_bold):
            pdfmetrics.registerFont(TTFont('DejaVu', dejavu))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', dejavu_bold))
            _FONTS_REGISTERED = True
            return 'DejaVu', 'DejaVu-Bold'
    except Exception:
        pass
    _FONTS_REGISTERED = True
    return 'Helvetica', 'Helvetica-Bold'


class ProfessionalPDFCanvas(canvas.Canvas):
    """Custom canvas for header and footer"""
    
    def __init__(self, *args, **kwargs):
        self.distributor = kwargs.pop('distributor', None)
        self.encounter = kwargs.pop('encounter', None)
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
        
    def save(self):
        page_count = len(self.pages)
        for page_num, page in enumerate(self.pages, 1):
            self.__dict__.update(page)
            self.draw_header()
            self.draw_footer(page_num, page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_header(self):
        """Draw professional header with logo and clinic info"""
        width, height = A4
        
        # Red/Burgundy header bar
        header_color = colors.HexColor(self.distributor.color_hex or '#7a001d')
        self.setFillColor(header_color)
        self.rect(0, height - 50*mm, width, 50*mm, fill=True, stroke=False)
        
        # Logo (left side)
        if self.distributor.logo_path:
            try:
                logo_path = os.path.join('app', 'static', 'uploads', self.distributor.logo_path)
                if os.path.exists(logo_path):
                    # White square background for logo
                    self.setFillColor(colors.white)
                    self.rect(15*mm, height - 45*mm, 40*mm, 40*mm, fill=True, stroke=False)
                    
                    # Logo image
                    self.drawImage(logo_path, 17*mm, height - 43*mm, 
                                  width=36*mm, height=36*mm, 
                                  preserveAspectRatio=True, mask='auto')
            except:
                pass
        else:
            # Default logo square with initials
            self.setFillColor(colors.white)
            self.rect(15*mm, height - 45*mm, 40*mm, 40*mm, fill=True, stroke=False)
            self.setFillColor(header_color)
            self.setFont('Arial-Bold', 24)
            initials = ''.join([word[0] for word in self.distributor.name.split()[:2]])
            self.drawCentredString(35*mm, height - 28*mm, initials)
        
        # Clinic name and info (right side)
        self.setFillColor(colors.white)
        self.setFont('Arial-Bold', 20)
        self.drawRightString(width - 15*mm, height - 20*mm, self.distributor.name)
        
        self.setFont('Arial', 10)
        y_pos = height - 28*mm
        
        if self.distributor.website:
            self.drawRightString(width - 15*mm, y_pos, self.distributor.website)
            y_pos -= 5*mm
            
        if self.distributor.phone:
            phone_text = f"☎ {self.distributor.phone}"
            self.drawRightString(width - 15*mm, y_pos, phone_text)
            y_pos -= 5*mm
            
        if self.distributor.email:
            self.drawRightString(width - 15*mm, y_pos, self.distributor.email)
    
    def draw_footer(self, page_num, page_count):
        """Draw professional footer"""
        width, height = A4
        
        # Footer bar
        footer_color = colors.HexColor(self.distributor.color_hex or '#7a001d')
        self.setFillColor(footer_color)
        self.rect(0, 0, width, 20*mm, fill=True, stroke=False)
        
        self.setFillColor(colors.white)
        self.setFont('Arial', 8)
        
        # Left: Copyright and clinic info
        footer_left = f"© {datetime.now().year} {self.distributor.name}"
        if self.distributor.website:
            footer_left += f" • {self.distributor.website}"
        if self.distributor.phone:
            footer_left += f" • {self.distributor.phone}"
            
        self.drawString(15*mm, 10*mm, footer_left)
        
        # Right: Page number
        self.drawRightString(width - 15*mm, 10*mm, f"Sayfa {page_num} / {page_count}")
        
        # Center: Additional info
        if self.distributor.address:
            self.setFont('Arial', 7)
            self.drawCentredString(width/2, 6*mm, self.distributor.address)


class ProfessionalEncounterPDF:
    """Professional PDF generator for medical encounters"""
    
    def __init__(self, encounter, distributor):
        self.encounter = encounter
        self.distributor = distributor
        self.patient = encounter.patient
        self.buffer = BytesIO()
        self.width, self.height = A4
        
        # Register fonts
        self.base_font, self.bold_font = _ensure_fonts_registered()
        
        # Setup styles
        self.setup_styles()
        
    def setup_styles(self):
        """Create custom paragraph styles"""
        self.styles = getSampleStyleSheet()
        
        # Main title style
        self.title_style = ParagraphStyle(
            'MainTitle',
            fontName=self.bold_font,
            fontSize=22,
            textColor=colors.HexColor(self.distributor.color_hex or '#7a001d'),
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10
        )
        
        # Section heading
        self.section_style = ParagraphStyle(
            'SectionHeading',
            fontName=self.bold_font,
            fontSize=16,
            textColor=colors.HexColor(self.distributor.color_hex or '#7a001d'),
            spaceBefore=15,
            spaceAfter=10,
            borderWidth=0,
            borderPadding=5,
            borderColor=colors.HexColor(self.distributor.color_hex or '#7a001d'),
            borderRadius=None,
            backColor=colors.HexColor('#f8f8f8')
        )
        
        # Subsection
        self.subsection_style = ParagraphStyle(
            'SubSection',
            fontName=self.bold_font,
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceBefore=10,
            spaceAfter=5
        )
        
        # Normal text
        self.normal_style = ParagraphStyle(
            'NormalText',
            fontName=self.base_font,
            fontSize=10,
            textColor=colors.HexColor('#444444'),
            leading=14
        )
        
        # Info box style
        self.info_style = ParagraphStyle(
            'InfoBox',
            fontName=self.base_font,
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            backColor=colors.HexColor('#f0f0f0'),
            borderPadding=8,
            leading=12
        )
    
    def generate(self):
        """Generate the complete PDF"""
        # Create PDF with custom canvas
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=55*mm,  # Space for header
            bottomMargin=25*mm,  # Space for footer
            title=f"Muayene Raporu - {self.patient.first_name} {self.patient.last_name}",
            author=self.distributor.name
        )
        
        # Build content
        story = []
        
        # Page 1: Patient Information
        story.extend(self.create_patient_page())
        
        # Page 2+: Treatment Details
        story.append(PageBreak())
        story.extend(self.create_treatment_pages())
        
        # Build PDF with custom canvas
        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: ProfessionalPDFCanvas(
                *args, 
                distributor=self.distributor,
                encounter=self.encounter,
                **kwargs
            )
        )
        
        self.buffer.seek(0)
        return self.buffer
    
    def create_patient_page(self):
        """Create first page with patient information"""
        elements = []
        
        # Personalized greeting if present
        greeting = self.encounter.greeting_message or self.distributor.greeting_message
        if greeting:
            elements.append(Paragraph(greeting, self.normal_style))
            elements.append(Spacer(1, 5*mm))
        
        # Main title
        elements.append(Paragraph("Muayene / Teklif Raporu", self.title_style))
        elements.append(Spacer(1, 10*mm))
        
        # Patient info box
        patient_data = [
            ['Hasta:', f"{self.patient.first_name} {self.patient.last_name}"],
            ['Tarih:', self.encounter.date.strftime('%d.%m.%Y') if self.encounter.date else '-'],
            ['Teklif No:', str(self.encounter.id)],
        ]
        
        if self.patient.dob:
            age = (datetime.now().date() - self.patient.dob).days // 365
            patient_data.append(['Doğum Tarihi:', f"{self.patient.dob.strftime('%d.%m.%Y')} ({age} yaş)"])
        
        if self.patient.gender:
            gender_text = 'Erkek' if self.patient.gender == 'M' else 'Kadın'
            patient_data.append(['Cinsiyet:', gender_text])
        
        if self.patient.nationality:
            patient_data.append(['Uyruk:', self.patient.nationality])
        
        if self.patient.phone:
            patient_data.append(['Telefon:', self.patient.phone])
        
        if self.patient.email:
            patient_data.append(['E-posta:', self.patient.email])
        
        patient_table = Table(patient_data, colWidths=[45*mm, 120*mm])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.base_font),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f8f8')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 15*mm))
        
        # General notes
        if self.encounter.note:
            elements.append(Paragraph("Genel Notlar", self.subsection_style))
            elements.append(Paragraph(self.encounter.note, self.normal_style))
        
        return elements
    
    def create_treatment_pages(self):
        """Create treatment detail pages"""
        elements = []
        
        # Hair transplant - Manuel sorgu kullan
        from app.models import HairAnnotation, HairPatternSelection
        hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
        hair_patterns = HairPatternSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if hair_annotations or hair_patterns:
            elements.extend(self._create_hair_section())
            elements.append(Spacer(1, 10*mm))
        
        # Dental - Manuel sorgu kullan
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        
        if dental_procedures:
            elements.extend(self._create_dental_section())
            elements.append(Spacer(1, 10*mm))
        
        # Eye - Manuel sorgu kullan
        from app.models import EyeRefraction, EyeTreatmentSelection
        eye_refraction = EyeRefraction.query.filter_by(encounter_id=self.encounter.id).first()
        eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if eye_refraction or eye_treatments:
            elements.extend(self._create_eye_section())
            elements.append(Spacer(1, 10*mm))
        
        # Aesthetic - Manuel sorgu kullan
        from app.models import AestheticProcedure
        aesthetic_procedure = AestheticProcedure.query.filter_by(encounter_id=self.encounter.id).first()
        
        if aesthetic_procedure:
            elements.extend(self._create_aesthetic_section())
            elements.append(Spacer(1, 10*mm))
        
        # Bariatric - Manuel sorgu kullan
        from app.models import BariatricSurgery
        bariatric_surgery = BariatricSurgery.query.filter_by(encounter_id=self.encounter.id).first()
        
        if bariatric_surgery:
            elements.extend(self._create_bariatric_section())
            elements.append(Spacer(1, 10*mm))
        
        # IVF - Manuel sorgu kullan
        from app.models import IVFTreatment
        ivf_treatment = IVFTreatment.query.filter_by(encounter_id=self.encounter.id).first()
        
        if ivf_treatment:
            elements.extend(self._create_ivf_section())
            elements.append(Spacer(1, 10*mm))
        
        # Check-up - Manuel sorgu kullan
        from app.models import CheckUpPackage
        checkup_package = CheckUpPackage.query.filter_by(encounter_id=self.encounter.id).first()
        
        if checkup_package:
            elements.extend(self._create_checkup_section())
            elements.append(Spacer(1, 10*mm))
        
        # Final price summary
        elements.append(PageBreak())
        elements.extend(self._create_price_summary())
        
        return elements
    
    def _generate_treatment_summary(self):
        """Generate brief treatment summary"""
        treatments = []
        
        # Hair - Manuel sorgu
        from app.models import HairAnnotation
        hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
        if hair_annotations:
            total_grafts = sum(ann.graft_count or 0 for ann in hair_annotations if hasattr(ann, 'graft_count'))
            if total_grafts > 0:
                treatments.append(f"• Saç Ekimi: {total_grafts} greft")
        
        # Dental - Manuel sorgu
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        if dental_procedures:
            treatments.append(f"• Diş Tedavisi: {len(dental_procedures)} işlem")
        
        # Eye manual check için yeniden sorgu
        from app.models import EyeRefraction, EyeTreatmentSelection
        eye_refraction = EyeRefraction.query.filter_by(encounter_id=self.encounter.id).first()
        eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if eye_refraction or eye_treatments:
            treatments.append("• Göz Ameliyatı")
        
        if self.encounter.aesthetic_procedure:
            treatments.append(f"• Estetik Cerrahi: {self.encounter.aesthetic_procedure.procedure_type}")
        
        if self.encounter.bariatric_surgery:
            treatments.append(f"• Bariatrik Cerrahi: {self.encounter.bariatric_surgery.surgery_type}")
        
        if self.encounter.ivf_treatment:
            treatments.append(f"• Tüp Bebek: {self.encounter.ivf_treatment.treatment_type}")
        
        if self.encounter.checkup_package:
            treatments.append(f"• Check-Up: {self.encounter.checkup_package.package_type}")
        
        return '<br/>'.join(treatments) if treatments else ''
    
    def _create_hair_section(self):
        """Create hair transplant section with details and diagram"""
        elements = []
        elements.append(Paragraph("💇 Saç Ekimi İşlemleri", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Try to add hair diagram
        try:
            hair_img_path = os.path.join('app', 'static', 'images', 'hair_transplant_diagram.png')
            if os.path.exists(hair_img_path):
                hair_img = Image(hair_img_path, width=80*mm, height=60*mm)
                hair_img.hAlign = 'CENTER'
                elements.append(hair_img)
                elements.append(Spacer(1, 5*mm))
        except:
            pass
        
        # Graft details table - Manuel sorgu kullan
        from app.models import HairAnnotation
        hair_annotations = HairAnnotation.query.filter_by(encounter_id=self.encounter.id).all()
        
        if hair_annotations:
            graft_data = [['Bölge', 'Greft Sayısı']]
            total_grafts = 0
            
            for ann in hair_annotations:
                if hasattr(ann, 'area') and hasattr(ann, 'graft_count'):
                    graft_data.append([ann.area or 'Belirtilmemiş', str(ann.graft_count or 0)])
                    total_grafts += ann.graft_count or 0
            
            graft_data.append(['TOPLAM GREFT', str(total_grafts)])
            
            graft_table = Table(graft_data, colWidths=[100*mm, 70*mm])
            graft_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTNAME', (0, 0), (-1, -1), self.base_font),
                ('FONTNAME', (0, -1), (-1, -1), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f5e9')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#c8e6c9')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(graft_table)
            elements.append(Spacer(1, 5*mm))
            
            # Calculate price (example: 1 EUR per graft)
            estimated_price = total_grafts * 1.0  # You can adjust this calculation
            
            # Price box
            price_data = [[f'💰 Tahmini Ücret: {estimated_price:.2f} EUR']]
            price_data.append([f'({total_grafts} greft × 1.00 EUR)'])
            
            price_table = Table(price_data, colWidths=[170*mm])
            price_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 0), self.bold_font),
                ('FONTNAME', (0, 1), (0, 1), self.base_font),
                ('FONTSIZE', (0, 0), (0, 0), 18),
                ('FONTSIZE', (0, 1), (0, 1), 11),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#2e7d32')),
                ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#666666')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (0, 0), 12),
                ('BOTTOMPADDING', (0, 1), (0, 1), 8),
                ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#2e7d32')),
            ]))
            elements.append(price_table)
        
        return elements
    
    def _create_dental_section(self):
        """Create dental section"""
        elements = []
        elements.append(Paragraph("🦷 Diş İşlemleri", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Dental table - Manuel sorgu kullan
        from app.models import DentalProcedure
        dental_procedures = DentalProcedure.query.filter_by(encounter_id=self.encounter.id).all()
        
        dental_data = [['Diş No', 'İşlem', 'Tutar']]
        total = 0
        total_original = 0
        
        for proc in dental_procedures:
            final_price = proc.discounted_price if proc.discount_enabled and proc.discounted_price else proc.price
            total += final_price or 0
            total_original += proc.price or 0
            
            # Format price display
            if proc.discount_enabled and proc.discounted_price:
                price_text = f'<strike>{proc.price:.2f}</strike> → {proc.discounted_price:.2f} {proc.currency}'
            else:
                price_text = f'{proc.price:.2f} {proc.currency}'
            
            dental_data.append([
                str(proc.tooth_no),
                proc.treatment_type,
                price_text
            ])
        
        dental_table = Table(dental_data, colWidths=[30*mm, 100*mm, 40*mm])
        dental_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 0), (-1, -1), self.base_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(dental_table)
        elements.append(Spacer(1, 5*mm))
        
        # Total price box - prominent with discount info
        if total < total_original:
            price_text = f'💰 Toplam: <strike>{total_original:.2f}</strike> → {total:.2f} EUR<br/><font size="10">İndirim: {total_original - total:.2f} EUR</font>'
        else:
            price_text = f'💰 Toplam Diş Tedavisi Ücreti: {total:.2f} EUR'
        
        price_data = [[price_text]]
        price_table = Table(price_data, colWidths=[170*mm])
        price_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1565c0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#1565c0')),
        ]))
        elements.append(price_table)
        
        return elements
    
    def _create_eye_section(self):
        """Create eye treatment section with details"""
        elements = []
        elements.append(Paragraph("👁️ Göz Ameliyatı", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Eye diagram/icon placeholder
        try:
            # Try to add eye diagram if available
            eye_img_path = os.path.join('app', 'static', 'images', 'eye_diagram.png')
            if os.path.exists(eye_img_path):
                eye_img = Image(eye_img_path, width=60*mm, height=40*mm)
                eye_img.hAlign = 'CENTER'
                elements.append(eye_img)
                elements.append(Spacer(1, 3*mm))
        except:
            pass
        
        # Refraction data if available - Manuel sorgu kullan
        from app.models import EyeRefraction
        refraction = EyeRefraction.query.filter_by(encounter_id=self.encounter.id).first()
        
        if refraction:
            ref = refraction
            elements.append(Paragraph("<b>Refraksiyon Değerleri:</b>", self.subsection_style))
            
            refraction_data = [
                ['', 'Sağ Göz (OD)', 'Sol Göz (OS)'],
                ['Sphere (SPH)', ref.od_sph if ref.od_sph is not None else '-', ref.os_sph if ref.os_sph is not None else '-'],
                ['Cylinder (CYL)', ref.od_cyl if ref.od_cyl is not None else '-', ref.os_cyl if ref.os_cyl is not None else '-'],
                ['Axis', ref.od_ax if ref.od_ax is not None else '-', ref.os_ax if ref.os_ax is not None else '-'],
            ]
            
            ref_table = Table(refraction_data, colWidths=[50*mm, 60*mm, 60*mm])
            ref_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTNAME', (0, 0), (0, -1), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(ref_table)
            elements.append(Spacer(1, 5*mm))
        
        # Treatment details - Manuel sorgu kullan
        from app.models import EyeTreatmentSelection
        treatments = EyeTreatmentSelection.query.filter_by(encounter_id=self.encounter.id).all()
        
        if treatments:
            for treatment in treatments:
                elements.append(Paragraph(f"<b>Tedavi:</b> {treatment.title}", self.normal_style))
                
                if treatment.side:
                    side_text = {'OD': 'Sağ Göz', 'OS': 'Sol Göz', 'OU': 'Her İki Göz'}.get(treatment.side, treatment.side)
                    elements.append(Paragraph(f"<b>Hangi Göz:</b> {side_text}", self.normal_style))
                
                if treatment.note:
                    elements.append(Paragraph(f"<b>Notlar:</b> {treatment.note}", self.normal_style))
                
                elements.append(Spacer(1, 3*mm))
                
                # Price box - prominent with discount
                final_price = treatment.discounted_price if treatment.discount_enabled and treatment.discounted_price else treatment.price
                
                if treatment.discount_enabled and treatment.discounted_price:
                    price_text = f'💰 <strike>{treatment.price:.2f}</strike> → {treatment.discounted_price:.2f} {treatment.currency}'
                else:
                    price_text = f'💰 {treatment.price:.2f} {treatment.currency}'
                
                price_data = [[price_text]]
                price_table = Table(price_data, colWidths=[170*mm])
                price_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 16),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f4f8')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0066cc')),
                ]))
                elements.append(price_table)
        
        return elements
    
    def _create_aesthetic_section(self):
        """Create aesthetic surgery section with visuals"""
        elements = []
        elements.append(Paragraph("✨ Estetik Cerrahi", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Manuel sorgu kullan
        from app.models import AestheticProcedure
        proc = AestheticProcedure.query.filter_by(encounter_id=self.encounter.id).first()
        
        # Try to add relevant image based on procedure type
        try:
            procedure_images = {
                'rhinoplasty': 'rhinoplasty_diagram.png',
                'liposuction': 'liposuction_diagram.png',
                'breast_augmentation': 'breast_augmentation_diagram.png',
                'facelift': 'facelift_diagram.png',
                'blepharoplasty': 'blepharoplasty_diagram.png',
            }
            
            img_file = procedure_images.get(proc.procedure_type.lower().replace(' ', '_'), 'aesthetic_default.png')
            img_path = os.path.join('app', 'static', 'images', img_file)
            
            if os.path.exists(img_path):
                aesthetic_img = Image(img_path, width=80*mm, height=60*mm)
                aesthetic_img.hAlign = 'CENTER'
                elements.append(aesthetic_img)
                elements.append(Spacer(1, 5*mm))
        except:
            # If image not found, add placeholder icon
            pass
        
        # Procedure details
        info_data = [
            ['İşlem Detayları', ''],
            ['İşlem Türü', proc.procedure_type],
        ]
        
        if proc.notes:
            info_data.append(['Açıklama', proc.notes])
        
        info_table = Table(info_data, colWidths=[50*mm, 120*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (0, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff3e0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))
        
        # Price box - very prominent with discount
        final_price = proc.discounted_price if proc.discount_enabled and proc.discounted_price else proc.price
        
        if proc.discount_enabled and proc.discounted_price:
            price_text = f'💰 Toplam Ücret: <strike>{proc.price:.2f}</strike> → {proc.discounted_price:.2f} {proc.currency}<br/><font size="12">İndirim: {proc.price - proc.discounted_price:.2f} {proc.currency}</font>'
        else:
            price_text = f'💰 Toplam Ücret: {proc.price:.2f} {proc.currency}'
        
        price_data = [[price_text]]
        price_table = Table(price_data, colWidths=[170*mm])
        price_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3e0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#e65100')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#e65100')),
        ]))
        elements.append(price_table)
        
        return elements
    
    def _create_bariatric_section(self):
        """Create bariatric surgery section with visuals"""
        elements = []
        elements.append(Paragraph("⚖️ Bariatrik Cerrahi", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Manuel sorgu kullan
        from app.models import BariatricSurgery
        surg = BariatricSurgery.query.filter_by(encounter_id=self.encounter.id).first()
        
        # Try to add stomach/surgery diagram
        try:
            surgery_images = {
                'sleeve': 'sleeve_gastrectomy.png',
                'bypass': 'gastric_bypass.png',
                'band': 'gastric_band.png',
            }
            
            img_file = surgery_images.get(surg.surgery_type.lower().replace(' ', '_'), 'bariatric_default.png')
            img_path = os.path.join('app', 'static', 'images', img_file)
            
            if os.path.exists(img_path):
                bariatric_img = Image(img_path, width=70*mm, height=50*mm)
                bariatric_img.hAlign = 'CENTER'
                elements.append(bariatric_img)
                elements.append(Spacer(1, 5*mm))
        except:
            pass
        
        # Patient measurements and surgery details
        info_data = [
            ['Ameliyat Bilgileri', ''],
            ['Ameliyat Türü', surg.surgery_type],
            ['Mevcut Kilo', f'{surg.weight_kg} kg'],
            ['Boy', f'{surg.height_cm} cm'],
        ]
        
        if surg.bmi:
            # BMI kategorisi
            bmi_category = 'Normal'
            if surg.bmi >= 40:
                bmi_category = 'Morbid Obezite (Sınıf 3)'
            elif surg.bmi >= 35:
                bmi_category = 'Ciddi Obezite (Sınıf 2)'
            elif surg.bmi >= 30:
                bmi_category = 'Obezite (Sınıf 1)'
            elif surg.bmi >= 25:
                bmi_category = 'Fazla Kilolu'
            
            info_data.append(['BMI (Vücut Kitle İndeksi)', f'{surg.bmi:.1f} - {bmi_category}'])
        
        if surg.target_weight_kg:
            info_data.append(['Hedef Kilo', f'{surg.target_weight_kg} kg'])
        
        if surg.notes:
            info_data.append(['Ek Notlar', surg.notes])
        
        info_table = Table(info_data, colWidths=[60*mm, 110*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (0, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffebee')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))
        
        # Price box - very prominent with discount
        final_price = surg.discounted_price if surg.discount_enabled and surg.discounted_price else surg.price
        
        if surg.discount_enabled and surg.discounted_price:
            price_text = f'💰 Ameliyat Ücreti: <strike>{surg.price:.2f}</strike> → {surg.discounted_price:.2f} {surg.currency}<br/><font size="12">İndirim: {surg.price - surg.discounted_price:.2f} {surg.currency}</font>'
        else:
            price_text = f'💰 Ameliyat Ücreti: {surg.price:.2f} {surg.currency}'
        
        price_data = [[price_text]]
        price_table = Table(price_data, colWidths=[170*mm])
        price_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffebee')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#c62828')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#c62828')),
        ]))
        elements.append(price_table)
        
        return elements
    
    def _create_ivf_section(self):
        """Create IVF treatment section"""
        elements = []
        elements.append(Paragraph("👶 Tüp Bebek Tedavisi", self.section_style))
        elements.append(Spacer(1, 5*mm))
        
        # Manuel sorgu kullan
        from app.models import IVFTreatment
        ivf = IVFTreatment.query.filter_by(encounter_id=self.encounter.id).first()
        
        # Try to add IVF diagram
        try:
            ivf_img_path = os.path.join('app', 'static', 'images', 'ivf_process.png')
            if os.path.exists(ivf_img_path):
                ivf_img = Image(ivf_img_path, width=70*mm, height=50*mm)
                ivf_img.hAlign = 'CENTER'
                elements.append(ivf_img)
                elements.append(Spacer(1, 5*mm))
        except:
            pass
        
        # Treatment details
        info_data = [
            ['Tedavi Bilgileri', ''],
            ['Tedavi Türü', ivf.treatment_type],
            ['Döngü Numarası', f'{ivf.cycle_number}. Döngü'],
        ]
        
        if ivf.female_age:
            info_data.append(['Kadın Yaşı', f'{ivf.female_age} yaş'])
        
        if ivf.notes:
            info_data.append(['Ek Notlar', ivf.notes])
        
        info_table = Table(info_data, colWidths=[60*mm, 110*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (0, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fce4ec')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 5*mm))
        
        # Price box with discount
        final_price = ivf.discounted_price if ivf.discount_enabled and ivf.discounted_price else ivf.price
        
        if ivf.discount_enabled and ivf.discounted_price:
            price_text = f'💰 Tedavi Ücreti: <strike>{ivf.price:.2f}</strike> → {ivf.discounted_price:.2f} {ivf.currency}<br/><font size="12">İndirim: {ivf.price - ivf.discounted_price:.2f} {ivf.currency}</font>'
        else:
            price_text = f'💰 Tedavi Ücreti: {ivf.price:.2f} {ivf.currency}'
        
        price_data = [[price_text]]
        price_table = Table(price_data, colWidths=[170*mm])
        price_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fce4ec')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#c2185b')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#c2185b')),
        ]))
        elements.append(price_table)
        
        return elements
    
    def _create_checkup_section(self):
        """Create check-up package section (supports discount display)."""
        elements = []
        elements.append(Paragraph("❤️ Check-Up Paketi", self.section_style))
        elements.append(Spacer(1, 5*mm))

        # Manuel sorgu kullan
        from app.models import CheckUpPackage
        pkg = CheckUpPackage.query.filter_by(encounter_id=self.encounter.id).first()

        # Optional icon
        try:
            icon_path = os.path.join('app', 'static', 'images', 'checkup_icon.png')
            if os.path.exists(icon_path):
                icon = Image(icon_path, width=55*mm, height=35*mm)
                icon.hAlign = 'CENTER'
                elements.append(icon)
                elements.append(Spacer(1, 4*mm))
        except Exception:
            pass

        names = {
            'bronze': 'Bronze Paket',
            'silver': 'Silver (Gümüş) Paket',
            'gold': 'Gold (Altın) Paket',
            'platinum': 'Platinum (Platin) Paket',
            'diamond': 'Diamond (Elmas) Paket'
        }
        package_name = names.get(pkg.package_type.lower(), pkg.package_type)

        info = [
            ['Check-Up Detayları', ''],
            ['Paket Türü', package_name],
        ]
        if pkg.tests_included:
            tests = pkg.tests_included
            if len(tests) > 250:
                tests = tests[:250] + '...'
            info.append(['Dahil Testler', tests])

        table = Table(info, colWidths=[60*mm, 110*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
            ('FONTNAME', (0, 1), (0, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3e5f5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 5*mm))

        if pkg.discount_enabled and pkg.discounted_price:
            price_text = (
                f"💰 Paket Ücreti: <strike>{pkg.price:.2f}</strike> → "
                f"{pkg.discounted_price:.2f} {pkg.currency}<br/><font size='12'>İndirim: "
                f"{(pkg.price - pkg.discounted_price):.2f} {pkg.currency}</font>"
            )
        else:
            price_text = f"💰 Paket Ücreti: {pkg.price:.2f} {pkg.currency}"
        price_data = [[price_text]]
        price_table = Table(price_data, colWidths=[170*mm])
        price_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3e5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#7b1fa2')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 3, colors.HexColor('#7b1fa2')),
        ]))
        elements.append(price_table)
        return elements
    
    def _create_price_summary(self):
        """Create final price summary page (discount-aware) with per-module lines then general totals."""
        elements = []
        elements.append(Paragraph("Fiyat Özeti", self.title_style))
        elements.append(Spacer(1, 6*mm))

        currency_symbol = {'EUR': '€', 'USD': '$', 'TRY': '₺', 'GBP': '£'}

        # Table columns: [Modül, Açıklama, Tutar, İndirim, Geçerlilik, KDV/Vergi, Ödeme Planı, Döviz Kuru]
        module_rows = []

        def fmt_amount(amount, currency):
            cur = currency or (self.distributor.default_currency or self.distributor.currency or 'EUR')
            sym = currency_symbol.get(cur, cur)
            return f"{sym} {amount:,.2f}"

        def get_vat(item):
            return getattr(item, 'vat', None) or getattr(self.distributor, 'vat', None) or 0

        def get_validity(item):
            return getattr(item, 'valid_until', None) or getattr(self.encounter, 'valid_until', None)

        def get_payment_plan(item):
            return getattr(item, 'payment_plan', None) or getattr(self.encounter, 'payment_plan', None) or getattr(self.distributor, 'payment_plan', None)

        def get_exchange_rate(item):
            return getattr(item, 'exchange_rate', None) or getattr(self.encounter, 'exchange_rate', None) or getattr(self.distributor, 'exchange_rate', None)

        def get_description(item):
            return getattr(item, 'description', None) or getattr(item, 'notes', None) or getattr(item, 'note', None) or ''

        # Hair
        total_grafts = 0
        if getattr(self.encounter, 'hair_annotations', None):
            for ann in self.encounter.hair_annotations:
                if hasattr(ann, 'graft_count') and ann.graft_count:
                    total_grafts += ann.graft_count
        if total_grafts > 0:
            ppg = float(self.distributor.price_per_graft or 0)
            hair_currency = getattr(self.distributor, 'default_currency', None) or getattr(self.distributor, 'currency', 'EUR')
            hair_total = total_grafts * ppg
            desc = f"{total_grafts} greft x {fmt_amount(ppg, hair_currency)}"
            validity = getattr(self.encounter, 'valid_until', None)
            vat = getattr(self.distributor, 'vat', None) or 0
            payment_plan = getattr(self.encounter, 'payment_plan', None) or getattr(self.distributor, 'payment_plan', None)
            exchange_rate = getattr(self.distributor, 'exchange_rate', None)
            module_rows.append([
                "Saç Ekimi",
                desc,
                fmt_amount(hair_total, hair_currency),
                "-",  # No discount logic for hair
                validity.strftime('%d.%m.%Y') if validity else "-",
                f"{vat:.1f}%" if vat else "-",
                payment_plan or "-",
                f"{exchange_rate}" if exchange_rate else "-"
            ])

        # Helper for modules with discount
        def add_module_row(title, item):
            cur = getattr(item, 'currency', None) or (self.distributor.default_currency or self.distributor.currency or 'EUR')
            price = getattr(item, 'price', 0) or 0
            disc_en = bool(getattr(item, 'discount_enabled', False))
            disc_price = getattr(item, 'discounted_price', None)
            final = disc_price if disc_en and disc_price else price
            discount_amt = (price - disc_price) if disc_en and disc_price else 0
            desc = get_description(item)
            validity = get_validity(item)
            vat = get_vat(item)
            payment_plan = get_payment_plan(item)
            exchange_rate = get_exchange_rate(item)
            module_rows.append([
                title,
                desc or "-",
                fmt_amount(final, cur),
                fmt_amount(discount_amt, cur) if discount_amt else "-",
                validity.strftime('%d.%m.%Y') if validity else "-",
                f"{vat:.1f}%" if vat else "-",
                payment_plan or "-",
                f"{exchange_rate}" if exchange_rate else "-"
            ])

        # Dental
        if getattr(self.encounter, 'dental_procedures', None):
            for proc in self.encounter.dental_procedures:
                add_module_row("Diş Tedavisi", proc)

        # Eye
        if getattr(self.encounter, 'eye_treatments', None):
            for t in self.encounter.eye_treatments:
                add_module_row("Göz Ameliyatı", t)

        # Aesthetic
        if getattr(self.encounter, 'aesthetic_procedure', None):
            ap = self.encounter.aesthetic_procedure
            add_module_row("Estetik Cerrahi", ap)

        # Bariatric
        if getattr(self.encounter, 'bariatric_surgery', None):
            b = self.encounter.bariatric_surgery
            add_module_row("Bariatrik Cerrahi", b)

        # IVF
        if getattr(self.encounter, 'ivf_treatment', None):
            v = self.encounter.ivf_treatment
            add_module_row("Tüp Bebek", v)

        # Check-up
        if getattr(self.encounter, 'checkup_package', None):
            c = self.encounter.checkup_package
            add_module_row("Check-Up", c)

        if module_rows:
            # Render module summary table with new columns
            headers = [
                "Modül", "Açıklama", "Tutar", "İndirim", "Geçerlilik", "KDV/Vergi", "Ödeme Planı", "Döviz Kuru"
            ]
            module_table = Table([headers] + module_rows, colWidths=[32*mm, 38*mm, 25*mm, 22*mm, 25*mm, 22*mm, 28*mm, 18*mm])
            module_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), self.bold_font),
                ('FONTNAME', (0, 1), (-1, -1), self.base_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f8f8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(module_table)
            elements.append(Spacer(1, 8*mm))

        # General totals per currency (discounted)
        totals = {}
        for row in module_rows:
            # row: [Modül, Açıklama, Tutar, İndirim, Geçerlilik, KDV/Vergi, Ödeme Planı, Döviz Kuru]
            price_str = row[2]
            # Extract currency from price_str
            for cur, sym in currency_symbol.items():
                if price_str.startswith(sym):
                    price_val = float(price_str.replace(sym, '').replace(',', '').strip())
                    totals[cur] = totals.get(cur, 0) + price_val
        totals_rows = []
        for currency, amount in totals.items():
            if amount > 0:
                sym = currency_symbol.get(currency, currency)
                totals_rows.append([f"Genel Toplam ({currency})" if len(totals) > 1 else "Genel Toplam", f"{sym} {amount:,.2f}"])

        if totals_rows:
            total_table = Table(totals_rows, colWidths=[100*mm, 70*mm])
            total_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.bold_font),
                ('FONTSIZE', (0, 0), (-1, -1), 13),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#000000')),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.7, colors.grey),
            ]))
            elements.append(total_table)
        else:
            elements.append(Paragraph("Herhangi bir fiyat kaydı bulunamadı.", self.info_style))

        return elements
