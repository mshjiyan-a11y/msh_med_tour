from app.models.distributor import Distributor
from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.hair import HairAnnotation, HairPatternSelection
from app.models.dental import DentalProcedure
from app.models.eye import EyeRefraction, EyeTreatmentSelection
from app.models.lead import Lead, LeadNote, APIKey
from app.models.hotel_reservation import HotelReservation
from app.models.settings import AppSettings
from app.models.patient_document import PatientDocument
from app.models.aesthetic import AestheticProcedure
from app.models.bariatric import BariatricSurgery
from app.models.ivf import IVFTreatment
from app.models.checkup import CheckUpPackage, CheckUpTest
from app.models.audit import AuditLog
from app.models.approval import QuoteApproval
from app.models.notification import Notification
from app.models.appointment import Appointment
from app.models.rbac import Role, Permission, RolePermission, UserRole
from app.models.document import Document
from app.models.journey import PatientJourney, JourneyStep, Flight, Transfer
from app.models.communication import (
    Message, CommunicationLog, PatientFeedback, 
    SupportTicket, TicketReply, ChatSession
)
from app.models.currency import CurrencyRate, PriceListItem
from app.models.meta_lead import MetaAPIConfig, FacebookLead, LeadInteraction