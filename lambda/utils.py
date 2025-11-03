import pytz
from datetime import datetime


def get_datetime_vienna():
    return datetime.now(pytz.timezone('Europe/Vienna'))

# get utc 12 pm as vienna time
def get_utc_noon_vienna():
    utc_noon = datetime.now(pytz.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    vienna_tz = pytz.timezone('Europe/Vienna')
    return utc_noon.astimezone(vienna_tz)


def format_time(dt_obj):
    """ Formatiert ein Datetime-Objekt in eine sprechbare Uhrzeit (z.B. '10 Uhr' oder '10 Uhr 30'). """
    hour = dt_obj.hour
    minute = dt_obj.minute
    if minute == 0:
        return f"{hour} Uhr"
    else:
        # Führende Null bei Minuten entfernen, falls vorhanden (z.B. '05' -> '5')
        return f"{hour} Uhr {minute}"

def format_price(price_float):
    """ 
    Formatiert einen Preis-Float (z.B. 10.5) in einen sprechbaren String (z.B. '10 Komma 5' oder '10'). 
    Entfernt Nullen am Ende von Nachkommastellen.
    """
    # Wandle float in String um (z.B. 10.5 -> "10.5", 10.0 -> "10.0", 10.55 -> "10.55")
    price_str = str(round(price_float, 2))
    
    # 1. Entferne Nullen am Ende der Nachkommastellen (z.B. "10.0" -> "10.")
    # 2. Entferne den Punkt, falls er jetzt am Ende steht (z.B. "10." -> "10")
    # Die Operationen werden nacheinander ausgeführt (chaining).
    price_str = price_str.rstrip('0').rstrip('.')
    
    # Ersetzt den Punkt durch "Komma" für die deutsche Sprachausgabe
    return price_str.replace('.', ' Komma ')
