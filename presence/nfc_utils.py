# core/nfc_utils.py

from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import CardConnectionException, NoCardException

def get_uid(connection):
    get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    try:
        response, sw1, sw2 = connection.transmit(get_uid_command)
        if sw1 == 0x90 and sw2 == 0x00:
            uid = toHexString(response)
            return uid.replace(' ', '').upper()
        else:
            print(f"Erreur lors de la récupération de l'UID : {sw1:02X} {sw2:02X}")
            return None
    except NoCardException:
        print("Erreur : Aucune carte n'est présente sur le lecteur.")
        return None
    except CardConnectionException as e:
        print(f"Exception lors de la récupération de l'UID : {e}")
        return None

def authenticate_sector(connection, sector_number, key):
    sector_trailer_block = sector_number * 4 + 3

    load_key_command = [0xFF, 0x82, 0x00, 0x00, 0x06] + key
    try:
        response, sw1, sw2 = connection.transmit(load_key_command)
        if sw1 != 0x90:
            print(f"Erreur lors du chargement de la clé : {sw1:02X} {sw2:02X}")
            return False

        authenticate_command = [
            0xFF, 0x86, 0x00, 0x00, 0x05,
            0x01, 0x00, sector_trailer_block, 0x60, 0x00
        ]
        response, sw1, sw2 = connection.transmit(authenticate_command)
        if sw1 != 0x90:
            print(f"Échec de l'authentification pour le secteur {sector_number} : {sw1:02X} {sw2:02X}")
            return False

        return True
    except NoCardException:
        print("Erreur : Aucune carte n'est présente sur le lecteur.")
        return False
    except CardConnectionException as e:
        print(f"Exception lors de l'authentification : {e}")
        return False

def write_block(connection, block_number, data):
    if len(data) > 16:
        print(f"Les données dépassent la limite d'un bloc (16 octets).")
        return False

    data_bytes = list(data.encode('utf-8')) if isinstance(data, str) else list(data)
    data_bytes += [0x00] * (16 - len(data_bytes))  # Remplir avec des zéros si nécessaire

    write_command = [0xFF, 0xD6, 0x00, block_number, 0x10] + data_bytes
    try:
        response, sw1, sw2 = connection.transmit(write_command)
        if sw1 == 0x90 and sw2 == 0x00:
            return True
        else:
            print(f"Erreur lors de l'écriture dans le bloc {block_number} : {sw1:02X} {sw2:02X}")
            return False
    except NoCardException:
        print("Erreur : Aucune carte n'est présente sur le lecteur.")
        return False
    except CardConnectionException as e:
        print(f"Exception lors de l'écriture dans le bloc {block_number} : {e}")
        return False

def write_card_uid_to_sector5(connection, card_uid, key):
    sector_number = 5
    block_number = sector_number * 4  # Premier bloc du secteur 5

    if not authenticate_sector(connection, sector_number, key):
        print(f"Impossible d'authentifier le secteur {sector_number}.")
        return False

    # Convertir card_uid en octets
    uid_bytes = bytes.fromhex(card_uid)
    uid_bytes += b'\x00' * (16 - len(uid_bytes))  # Remplir avec des zéros pour atteindre 16 octets

    success = write_block(connection, block_number, uid_bytes)
    if success:
        print(f"UID de la carte écrit avec succès dans le bloc {block_number} du secteur {sector_number}.")
    else:
        print(f"Échec de l'écriture de l'UID de la carte dans le bloc {block_number}.")
    return success

def read_card_uid_from_sector5(connection, key):
    sector_number = 5
    block_number = sector_number * 4  # Premier bloc du secteur 5

    if not authenticate_sector(connection, sector_number, key):
        print(f"Impossible d'authentifier le secteur {sector_number}.")
        return None

    read_command = [0xFF, 0xB0, 0x00, block_number, 0x10]
    try:
        response, sw1, sw2 = connection.transmit(read_command)
        if sw1 == 0x90 and sw2 == 0x00:
            uid_bytes = bytes(response).rstrip(b'\x00')  # Enlever les zéros de remplissage
            uid = uid_bytes.hex().upper()
            return uid
        else:
            print(f"Erreur lors de la lecture du bloc {block_number} : {sw1:02X} {sw2:02X}")
            return None
    except NoCardException:
        print("Erreur : Aucune carte n'est présente sur le lecteur.")
        return None
    except CardConnectionException as e:
        print(f"Exception lors de la lecture du bloc {block_number} : {e}")
        return None

def write_card_uid(card_uid):
    try:
        available_readers = readers()
        if not available_readers:
            return False, "Aucun lecteur de carte n'a été trouvé. Veuillez brancher un lecteur."

        reader = available_readers[0]
        connection = reader.createConnection()
        connection.connect()

        key = [0xFF] * 6  # Clé par défaut pour l'authentification

        success = write_card_uid_to_sector5(connection, card_uid, key)

        return success, "UID de la carte écrit avec succès." if success else "Échec de l'écriture de l'UID de la carte."

    except NoCardException:
        return False, "Aucune carte n'est détectée sur le lecteur."
    except CardConnectionException as e:
        return False, f"Erreur de connexion au lecteur : {e}"
    except Exception as e:
        return False, f"Erreur inconnue : {e}"

def read_card_uid():
    try:
        available_readers = readers()
        if not available_readers:
            return None, "Aucun lecteur de carte n'a été trouvé. Veuillez brancher un lecteur."

        reader = available_readers[0]
        connection = reader.createConnection()
        connection.connect()

        key = [0xFF] * 6  # Clé par défaut pour l'authentification

        card_uid = read_card_uid_from_sector5(connection, key)
        if card_uid:
            return card_uid, "UID de la carte lu avec succès."
        else:
            return None, "Échec de la lecture de l'UID de la carte."

    except NoCardException:
        return None, "Aucune carte n'est détectée sur le lecteur."
    except CardConnectionException as e:
        return None, f"Erreur de connexion au lecteur : {e}"
    except Exception as e:
        return None, f"Erreur inconnue : {e}"
