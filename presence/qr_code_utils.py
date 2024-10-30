import qrcode
from io import BytesIO
from PIL import Image
import base64
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_custom_qr_code(data, user):
    """
    Génère un QR code personnalisé avec un logo au centre.
    
    Args:
        data (str): Données à encoder dans le QR code.
        user (User): Utilisateur pour personnaliser le QR code (optionnel).

    Returns:
        PIL.Image: Image du QR code généré.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

    # Personnalisation : ajouter un logo au centre
    try:
        logo_display = Image.open('path/to/logo.png')  # Remplacez par le chemin réel de votre logo
        logo_size = 100
        logo_display.thumbnail((logo_size, logo_size))
        pos = ((qr_img.size[0] - logo_display.size[0]) // 2,
               (qr_img.size[1] - logo_display.size[1]) // 2)
        qr_img.paste(logo_display, pos, mask=logo_display if logo_display.mode == 'RGBA' else None)
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du logo : {e}")

    return qr_img

def qr_image_to_base64(qr_image):
    """
    Convertit une image PIL en chaîne base64.

    Args:
        qr_image (PIL.Image): Image du QR code.

    Returns:
        str: Image encodée en base64.
    """
    buffer = BytesIO()
    qr_image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

def send_qr_via_email(email, qr_image_base64):
    """
    Envoie le QR code par email.

    Args:
        email (str): Adresse email du destinataire.
        qr_image_base64 (str): Image du QR code encodée en base64.
    """
    subject = "Votre QR Code d'Attendance"
    message = "Voici votre QR Code pour l'attendance. Il est valide pendant 1 heure."
    email_message = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    email_message.content_subtype = "html"
    email_message.body += f'<br><img src="data:image/png;base64,{qr_image_base64}" alt="QR Code">'
    try:
        email_message.send()
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email : {e}")
