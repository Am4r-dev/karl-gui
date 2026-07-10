from microbit import *
import radio
import music

# Alle Calliopes der Gruppe müssen denselben Kanal benutzen, sonst hören sie
# sich nicht. Wenn mehrere Gruppen im selben Raum funken, hier pro Gruppe
# einen anderen Wert (0-83) verwenden.
RADIO_CHANNEL = 1

# I2C-Adresse des Pico, muss zu I2C_ADDR in pico/main.py passen.
PICO_ADDR = 0x42

MAX_MOVES = 50

radio.on()
# length=64, damit auch lange Tänze in eine Funknachricht passen
radio.config(channel=RADIO_CHANNEL, length=64)

seq = 0
connected = False

# Startmelodie + Schlaf-Gesicht: Strom ist da, Script läuft, wartet auf Befehle
display.show(Image.HEART_SMALL)
music.play(music.POWER_UP, wait=False)


def idle_image():
    # Verbunden = glücklich, sonst schlafend (Mitläufer schlafen zwischen Tänzen)
    return Image.HAPPY if connected else Image.ASLEEP


def send_to_pico(moves, loop_flag):
    # Zwei Schreibvorgänge: erst Tanzdaten ab mem[1], dann die neue
    # Kommando-Nummer nach mem[0]. So sieht der Pico den neuen Tanz erst,
    # wenn alle Daten vollständig angekommen sind.
    global seq
    seq = seq % 255 + 1
    try:
        payload = bytes([1, loop_flag, len(moves)]) + bytes([int(c) for c in moves])
        i2c.write(PICO_ADDR, payload)
        i2c.write(PICO_ADDR, bytes([0, seq]))
        return True
    except OSError:
        return False


def handle_line(line, broadcast):
    global connected
    line = line.strip()

    # Handshake: die Website meldet sich direkt nach dem Verbinden
    if line == 'HELLO':
        connected = True
        display.show(Image.HAPPY)
        music.play(music.JUMP_UP, wait=False)
        print('READY')
        return

    # Die Website trennt sich: Abschieds-Sound spielen, dann Neustart,
    # damit der Calliope für die nächste Verbindung frisch dasteht.
    # (Die Picos tanzen unabhängig weiter — stoppen macht der Stopp-Button.)
    if line == 'BYE':
        connected = False
        display.show(Image.ASLEEP)
        music.play(music.JUMP_DOWN)
        sleep(300)
        reset()

    # Erwartetes Format: DANCE:<Moves>:<Loop>, z.B. DANCE:1352:1
    # Leere Move-Liste (DANCE::0) bedeutet: Tanz stoppen.
    parts = line.split(':')
    if len(parts) != 3 or parts[0] != 'DANCE':
        return
    moves = ''.join(c for c in parts[1] if c in '12345')[:MAX_MOVES]
    loop_flag = 1 if parts[2] == '1' else 0

    ok = send_to_pico(moves, loop_flag)
    if not ok:
        # Pico antwortet nicht -> Verkabelung/Stromversorgung prüfen
        display.show('X')
        music.pitch(160, 400, wait=False)
    elif moves:
        display.show(Image.MUSIC_QUAVER)
        music.play(music.BA_DING, wait=False)
    else:
        display.show(idle_image())
        music.play(music.JUMP_DOWN, wait=False)

    if broadcast:
        radio.send('DANCE:' + moves + ':' + str(loop_flag))


buffer = ''

while True:
    # Kommandos von der Website (USB seriell). uart ist standardmäßig mit USB
    # verbunden; uart.read() blockiert nicht, solange vorher any() geprüft wird.
    if uart.any():
        data = uart.read()
        if data:
            # Beim Batteriestart (ohne USB) hängt die serielle Leitung in der
            # Luft und liefert beim Einschalten manchmal Müll-Bytes. Die würden
            # str(data, 'utf-8') crashen lassen — deshalb nur lesbares ASCII
            # und Zeilenumbrüche übernehmen, alles andere wegwerfen.
            for b in data:
                if b == 10 or 32 <= b <= 126:
                    buffer += chr(b)
            # Notbremse: Müll ohne Zeilenumbruch darf den Puffer nicht
            # unendlich wachsen lassen (längstes echtes Kommando ~60 Zeichen)
            if len(buffer) > 100:
                buffer = buffer[-100:]
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if line.strip():
                    handle_line(line, broadcast=True)

    # Tänze von anderen Calliopes -> nicht erneut weiterfunken,
    # sonst schaukelt sich das Funknetz auf. Fremde oder kaputte Funkpakete
    # (z.B. andere Gruppen, MakeCode-Geräte) können ValueError auslösen.
    try:
        msg = radio.receive()
    except ValueError:
        msg = None
    if msg:
        handle_line(msg, broadcast=False)
