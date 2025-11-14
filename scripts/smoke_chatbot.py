import sys
from pathlib import Path
import importlib.util

# Load chatbot_service directly by path to avoid importing full app package
CHATBOT_PATH = Path(__file__).resolve().parents[1] / "app" / "utils" / "chatbot_service.py"
spec = importlib.util.spec_from_file_location("chatbot_service", CHATBOT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader, "Failed to load chatbot_service module spec"
spec.loader.exec_module(module)

detect_intent = module.detect_intent
generate_response = module.generate_response
should_auto_respond = module.should_auto_respond
get_chatbot_signature = module.get_chatbot_signature

samples = [
    "Randevu almak istiyorum",
    "Ücret nedir?",
    "Fiyat hakkında bilgi verir misiniz?",
    "Otel ayarlamak istiyorum",
    "Ne zaman açıksınız?",
    "Kaç gün sürer tedavi süresi?",
    "I need an appointment",
    "What is your price?",
    "Can you help with hotel booking?",
    "How long does the treatment take?",
    "موعد من فضلك",
    "أحتاج فندق",
    "Naber",
    "Hi",
]

for s in samples:
    intent = detect_intent(s)
    resp, rtype = generate_response(s)
    auto_patient = should_auto_respond(s, sender_is_staff=False)
    auto_staff = should_auto_respond(s, sender_is_staff=True)
    print(f"MSG: {s}\n  intent={intent}\n  auto_patient={auto_patient}\n  auto_staff={auto_staff}\n  type={rtype}\n  resp={resp}\n")

print("Signature:", get_chatbot_signature())
