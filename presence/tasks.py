# presence/tasks.py

from celery import shared_task
from .models import NFCReader
from pythonping import ping
from django.utils import timezone

@shared_task
def ping_nfc_readers():
    readers = NFCReader.objects.all()
    for reader in readers:
        ip = reader.ip_address
        if not ip:
            continue  # Pas d'adresse IP définie
        try:
            response = ping(ip, count=1, timeout=2)
            if response.success():
                reader.is_online = True
                reader.status = NFCReader.ReaderStatus.ACTIVE
            else:
                reader.is_online = False
                reader.status = NFCReader.ReaderStatus.ERROR
            reader.last_online = timezone.now()
            reader.save()
        except Exception as e:
            reader.is_online = False
            reader.status = NFCReader.ReaderStatus.ERROR
            reader.save()
