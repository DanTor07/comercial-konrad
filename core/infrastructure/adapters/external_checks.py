import random
from ...domain.ports.external_services import CreditCheckPort, CreditScore, PoliceCheckPort

class DatacreditoAdapter(CreditCheckPort):
    def check_score(self, identificacion: str) -> CreditScore:
        # Simulate REST API call
        # For demonstration, we'll use random or based on ID pattern
        choice = random.choice(list(CreditScore))
        return choice

class CifinAdapter(CreditCheckPort):
    def check_score(self, identificacion: str) -> CreditScore:
        # Simulate reading from a flat file in the FileSystem
        # In a real scenario, we would load the file once and search in memory
        return random.choice(list(CreditScore))

class PoliceAdapter(PoliceCheckPort):
    def has_criminal_record(self, identificacion: str) -> bool:
        # Simulate web scraping or external API
        # Return True for "Requerido" and False for "No requerido"
        return random.random() < 0.1 # 10% chance of having a record
