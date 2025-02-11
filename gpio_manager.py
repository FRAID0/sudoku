import RPi.GPIO as GPIO
from time import sleep


# Einrichten von Schaltflächen mit BCM GPIO-Nummern
button_pins = {
    22: 'restart',  # 
    23: 'end',      #
    17: 3,          # GPIO 17 ist mit Taste 3 verknüpft
    27: 2,          # GPIO 27 ist mit Taste 2 verknüpft
    14: 1,           # GPIO 14 ist mit Taste 1 verknüpft
    6: 5,           #GPIO 6 ist mit Taste 5 verknüpft
    13: 6,          # GPIO 13 ist mit Taste 6 verknüpft
    19: 4,          # GPIO 19 ist mit Taste 4 verknüpft
    26: 9,          #GPIO 26 ist mit Taste 9 verknüpft
    21: 8,          #GPIO 21 ist mit Taste 8 verknüpft
    20: 7,          # GPIO 20 ist mit Taste 7 verknüpft
}

button_pressed = None

# Initialisierung von GPIOs
def setup_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)  # Verwendung von BCM für die Nummerierung von GPIO-Pins
    for pin in button_pins:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Einsatz von Pull-Down-Widerstand

# Funktion, um zu überprüfen, welche Taste gedrückt wurde
def check_button_press():
    for pin, action in button_pins.items():
        if GPIO.input(pin) == GPIO.HIGH:  
            sleep(0.2)  
            if GPIO.input(pin) == GPIO.HIGH:  
                if isinstance(action, int): 
                    print(f"Die Schaltfläche mit dem Wert {action} wurde gedrückt.")
                    return action  
                else:  
                    print(f"Die Aktion '{action}'wurde gedrückt.")
                    return action  
    return None 
# Die Aktion Funktion, um den Eingang der Schaltfläche über GPIO abzurufen
def get_button_input():
    button_pressed = check_button_press()
    if button_pressed is not None:
        return button_pressed
    return None

def use_handle_restart_game():
    from front import handle_restart_game
    handle_restart_game()

if __name__ == "__main__":
    setup_gpio() 
    try:
        while True:
            button_pressed = check_button_press()  
            if button_pressed is not None:
                if button_pressed == 'restart':
                    print("Das Spiel wird neu gestartet.")
                    #use_handle_restart_game()
                elif button_pressed == 'end':
                    print("Das Spiel wird beendet.")
                else:
                    print(f"zahl {button_pressed} wurde gedrückt.")  
            
    except KeyboardInterrupt:
        print("Das Programm wird unterbrochen.")
    finally:
        GPIO.cleanup()  


