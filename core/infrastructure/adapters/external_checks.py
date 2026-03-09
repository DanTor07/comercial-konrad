import random
import os
from django.conf import settings
from ...domain.ports.external_services import CreditCheckPort, CreditScore, PoliceCheckPort

class DatacreditoAdapter(CreditCheckPort):
    def check_score(self, identificacion: str) -> CreditScore:
        # Simulate REST API call
        return random.choice(list(CreditScore))

class CifinAdapter(CreditCheckPort):
    def check_score(self, identificacion: str) -> CreditScore:
        # Simulate reading from a flat file in the FileSystem
        file_path = os.path.join(settings.BASE_DIR, 'simulations', 'cifin_data.txt')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                # Dummy search: if ID is in file, return ALTA, else BAJA
                if identificacion in f.read():
                    return CreditScore.ALTA
        return CreditScore.BAJA

class PoliceAdapter(PoliceCheckPort):
    def has_criminal_record(self, identificacion: str) -> bool:
        # Simulate web scraping
        return random.random() < 0.1 
