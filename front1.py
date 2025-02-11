import tkinter as tk
from tkinter import simpledialog, messagebox
from player1 import *


# Sudoku Grid Size
# Globale Konstanten
GRID_SIZE = 9  
MARGIN = 0  
BUTTON_BAR_HEIGHT = 120  
CELL_SIZE=50

# Feste Größe der Zellen
CELL_WIDTH = 142  
CELL_HEIGHT = 80   


end_game_displayed = False  
player_scores = [0, 0]  
current_player = 0  
time_left = 0  

def handle_difficulty_click(difficulty):
    disable_difficulty_buttons()
    send_difficulty(difficulty)
    

def handle_restart_game():
    global end_game_displayed  
    enable_difficulty_buttons()
    send_restart_message()
    end_game_displayed = False  
    game_state["is_game_over"] = False
    ask_game_mode()


def send_restart_message_button():

    global restart_in_progress

    if not restart_in_progress:
        restart_in_progress = True
        restart_message = json.dumps({"restart": True})
        client.publish(MQTT_TOPICS["RESTART_GAME_TOPIC"], restart_message)  
        print("Neustartnachricht, die an den Server gesendet wird.")
        #time.sleep(0.5)
        restart_in_progress = False

def handle_end_game():
    """
    Verwaltet das Ende des Spiels und zeigt die Ergebnisse an.
    """
    global end_game_displayed  
    
    # Überprüft, ob das Spiel beendet ist und die Dialogbox noch nicht angezeigt wurde.
    if game_state.get("is_game_over", False) and not end_game_displayed:
        end_game_displayed = True  
        print(f"le player_id est {player_id} et le game de sa est {game_state['player_id']}")

        if game_state["ki"]:
            #if game_state["player_id"] == player_id:
            if player_id in game_state:
                spieler = "Spieler"
                ki_spieler = "KI FRAID"
            else:
                spieler = "KI FRAID"
                ki_spieler = "Spieler"
        else:
            spieler = "Spieler 1"
            ki_spieler = "Spieler 2"

        winner = game_state.get("winner", None)
        if winner == 1:
            message = f"{spieler} gewinnt!"
        elif winner == 2:
            message = f"{ki_spieler} gewinnt!"
        else:
            message = "Es ist ein Unentschieden!"
        messagebox.showinfo("Ende des Spiels", message)

        if "player_scores" in game_state:
            scores_message = f"Final Scores:\n{spieler}: {game_state['player_scores'][0]}\n{ki_spieler}: {game_state['player_scores'][1]}"
            messagebox.showinfo("Final Scores", scores_message)

        handle_restart_game()
    
       # Funktion, um den Klick auf ein Gitterfeld zu verwalten

#gpio_manager.setup_gpio()

def show_temporary_message(title, message, duration=3000):
    """
    Zeigt eine temporäre Nachricht an, die nach einer bestimmten Zeit automatisch geschlossen wird.
    :param title: Titel des Fensters.
    :param message: Die Nachricht, die angezeigt werden soll.
    :param duration: Zeit in Millisekunden bis zum Schließen (Standard: 3000 ms).
    """    
    temp_window = tk.Toplevel()
    temp_window.title(title)
    temp_window.geometry("300x100")
    temp_window.resizable(False, False)
    
    label = tk.Label(temp_window, text=message, wraplength=280, justify="center")
    label.pack(expand=True)
    
    temp_window.after(duration, temp_window.destroy)
    
    temp_window.attributes("-topmost", True)
    temp_window.protocol("WM_DELETE_WINDOW", lambda: None)  
    
    return temp_window
    
def grid_click(event, grid_size, cell_width, cell_height, margin, game_state, canvas):
    x, y = event.x, event.y

    # Überprüfen, ob der Klick innerhalb der Grenzen des Rasters liegt
    if margin < x < margin + grid_size * cell_width and margin < y < margin + grid_size * cell_height:
        # Berechnen Sie die angeklickte Zeile und Spalte
        row = (y - margin) // cell_height
        col = (x - margin) // cell_width

        print(f"Klick in der Zelle erkannt : Zeile {int(row)}, Spalte {int(col)}")

        # Überprüfen, ob das Spiel aktiv ist und ob eine Schwierigkeit ausgewählt wurde
        if not game_state.get("game_active", False) or game_state.get("selected_difficulty") is None:
            show_temporary_message("Error", "Bitte wählen Sie zunächst einen Schwierigkeitsgrad aus und starten Sie das Spiel.", duration=3000)
            return

        # Überprüfen Sie, ob das Raster vorhanden ist und ob das Feld bereits ausgefüllt ist
        if  game_state["grid"][row][col] != 0:
            show_temporary_message("Error", "Diese Zelle kann nicht geändert werden.", duration=2000)
            return

        # Setze das angeklickte Kästchen blau
        x1 = margin + col * cell_width
        y1 = margin + row * cell_height
        x2 = x1 + cell_width
        y2 = y1 + cell_height
        canvas.create_rectangle(x1, y1, x2, y2, fill="blue", outline="black")

        # Asynchrones Warten auf den GPIO-Eingang starten 
        wait_for_gpio_input(row, col)
    else:
        print("Klicke außerhalb des Rasters.")



def wait_for_gpio_input(row, col):
    """
    Wartet nicht blockierend auf Benutzereingaben über GPIO,
    und prüft dabei, ob der aktuelle Spieler an der Reihe ist.
    """
    # Prüfen, ob der aktuelle Spieler an der Reihe ist
    current_player = game_state.get("current_player")
    if current_player is None or current_player != player_id:
        show_temporary_message("Error", "Sie sind nicht an der Reihe.", duration=3000)
        return

# Warten Sie auf Benutzereingaben über GPIO
    number = simpledialog.askinteger("Entrer un nombre", "Entrez un nombre (1-9)")
    #number = gpio_manager.get_button_input()
    if number is None:
        # Wenn keine Eingabe erkannt wird, nach 100 ms erneut überprüfen.
        canvas.after(100, wait_for_gpio_input, row, col)
    else:
        print(f"Nummer erhalten: {number}")
        if not (1 <= number <= 9):
            messagebox.showwarning("Entrée invalide", "Le numéro entré est hors de portée (1-9).")
            return

        # Informationen an den Server senden
        try:
            send_to_server(row, col, number)
        except Exception as e:
            messagebox.showerror("Error", f"Es konnten keine Daten an den Server gesendet werden: {str(e)}")


# Funktion zum Anzeigen der detaillierten Regeln des Sudoku-Spiels
def show_rules():
    rules_text = """
Regeln für Sudoku:

1. Jede Zeile muss alle Zahlen von 1 bis 9 enthalten, ohne dass sich eine Zahl wiederholt.
2. Jede Spalte muss alle Zahlen von 1 bis 9 enthalten, ohne dass sich eine Zahl wiederholt.
3. Jedes 3x3-Feld muss ebenfalls alle Zahlen von 1 bis 9 enthalten, ohne dass sich eine Zahl wiederholt.

Ziel ist es, alle leeren Felder auszufüllen, indem diese Regeln eingehalten werden. Viel Erfolg!
"""
    messagebox.showinfo("Spielregeln", rules_text)
    show_how_to_start()  # Weiter zur Erklärung, wie man spielt


# Funktion zum Erklären, wie man das Spiel startet
def show_how_to_start():
    start_text = (
        "Spielanleitung:\n\n"
        "1. Klicken Sie auf die Schaltfläche 'Neustart', um ein laufendes Spiel zu beenden und ein neues Spiel zu starten.\n"
        "2. Wählen Sie einen Schwierigkeitsgrad aus: Leicht (30 Sekunden), Mittel (20 Sekunden), Schwer (10 Sekunden).\n\n"
        "Wichtig:\n"
        "- Sobald ein Spieler einen Schwierigkeitsgrad ausgewählt hat, gilt dieser Schwierigkeitsgrad für alle Spieler.\n"
        "Bonuspunkte:\n"
        "- Je schneller Sie spielen, desto mehr Bonuspunkte erhalten Sie.\n"
        "- Richtig innerhalb des ersten Drittels der Zeit: 1 Bonuspunkt.\n\n"
        "Strafen:\n"
        "- Falsche Zahl: -1 Punkt.\n"
        "- Zeit überschritten: Zug verloren, nächster Spieler an der Reihe."
    )
    messagebox.showinfo("Spielanleitung", start_text)
    show_how_to_win()


# Funktion zum Erklären, wie man das Spiel gewinnt
def show_how_to_win():
    win_text = """
Wie man gewinnt:

1. Vervollständigen Sie das gesamte Sudoku-Gitter, indem Sie die Regeln einhalten.
2. Füllen Sie alle Felder mit den richtigen Zahlen innerhalb der verfügbaren Zeit aus.
3. Maximieren Sie Ihre Punkte, indem Sie schnell und fehlerfrei spielen.

Der Spieler mit der höchsten Punktzahl am Ende des Spiels wird zum Gewinner erklärt. 
Viel Spaß und zeigen Sie Ihre Logikfähigkeiten!
"""
    messagebox.showinfo("Wie man gewinnt", win_text)
    ask_game_mode()


def ask_game_mode():
    """ Demande au joueur de choisir entre jouer contre une personne ou contre le KI """
    mode = messagebox.askquestion(
        "Spielmodus wählen", 
        "Möchten Sie gegen eine andere Person spielen? (Ja = Person, Nein = KI)",
        icon="question"
    )

    if mode == "yes":  
        game_state["ki"] = False 
    else:
        game_state["ki"] = True  

    print("Spielmodus gewählt:", "KI" if game_state["ki"] else "Multiplayer") 

window = tk.Tk()
window.title("Sudoku Game")
#window.attributes('-fullscreen', True)  
window.configure(bg="white")  

# Zeigen Sie die Dialogfenster nacheinander beim Start an
window.after(100, show_rules) 

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

desired_width = screen_width
desired_height = screen_height - BUTTON_BAR_HEIGHT 

canvas = tk.Canvas(window, bg="white")
canvas.pack(fill=tk.BOTH, expand=True)

grid_width = GRID_SIZE * CELL_WIDTH
grid_height = GRID_SIZE * CELL_HEIGHT

# Zeichnen Sie ein Sudoku-Raster
for i in range(GRID_SIZE + 1):
    line_width = 3 if i % 3 == 0 else 1  
    canvas.create_line(
        MARGIN, MARGIN + i * CELL_HEIGHT,
        MARGIN + GRID_SIZE * CELL_WIDTH, MARGIN + i * CELL_HEIGHT,
        width=line_width
    )
    canvas.create_line(
        MARGIN + i * CELL_WIDTH, MARGIN,
        MARGIN + i * CELL_WIDTH, MARGIN + GRID_SIZE * CELL_HEIGHT,
        width=line_width
    )

# Klickereignis im Raster konfigurieren
canvas.bind(
    "<Button-1>",
    lambda event: grid_click(event, GRID_SIZE, CELL_WIDTH, CELL_HEIGHT, MARGIN, game_state, canvas)
)


button_frame = tk.Frame(window)
button_frame.pack(pady=10, side=tk.BOTTOM, fill=tk.X)

# Schwierigkeitsschaltflächen
easy_button = tk.Button(button_frame, text="Easy", command=lambda: handle_difficulty_click("easy"))
easy_button.grid(row=0, column=0, padx=120) 
medium_button = tk.Button(button_frame, text="Medium", command=lambda: handle_difficulty_click("medium"))
medium_button.grid(row=0, column=1, padx=120)

hard_button = tk.Button(button_frame, text="Hard", command=lambda: handle_difficulty_click("hard") )
hard_button.grid(row=0, column=2, padx=120)

# Schaltfläche zum Neustart des Spiels
restart_button = tk.Button(button_frame, text="Restart",bg="red", fg="black" ,command=handle_restart_game)
restart_button.grid(row=0, column=3, padx=150)

# Fügt Beschriftungen für Punktestand, Zeit und aktuellen Spieler hinzu
info_frame = tk.Frame(window)
info_frame.pack(pady=5, side=tk.TOP, fill=tk.X)

current_player_label = tk.Label(info_frame, text=f"Current Player: Player {game_state['current_player']}")
current_player_label.grid(row=0, column=0, padx=150)  

score_label = tk.Label(info_frame, text="Scores: Player 1: 0, Player 2: 0")
score_label.grid(row=0, column=1, padx=120)

timer_label = tk.Label(info_frame, text=f"Time Left: {game_state['timer']} seconds")
timer_label.grid(row=0, column=2, padx=80)

window.update_idletasks()

canvas.config(width=grid_width, height=grid_height)

def disable_difficulty_buttons():
    easy_button.config(state="disabled")
    medium_button.config(state="disabled")
    hard_button.config(state="disabled")

def enable_difficulty_buttons():
    easy_button.config(state="normal")
    medium_button.config(state="normal")
    hard_button.config(state="normal")




def update_display():
    print(f"Updating display: timer={game_state['timer']}, current_player={game_state['current_player']}")
    score_label.config(text=f"Scores: Player 1: {game_state['player_scores'][0]}, Player 2: {game_state['player_scores'][1]}")
    timer_label.config(text=f"Time Left: {game_state['timer']} seconds")
    if game_state["ki"] and game_state["current_player"] != player_id :
        current_player_label.config(text=f"Current Player: KI FRAID")
    else:
        current_player_label.config(text=f"Current Player: Player {game_state['current_player'] +1}")


# Funktion zum Aktualisieren von game_state
def update_game_state():
    if game_state["game_active"]:
        game_state["timer"] -= 1
        if game_state["timer"] <= 0:
            game_state["timer"] = 30  # Réinitialise
            game_state["current_player"] = 1 - game_state["current_player"]  # Change de joueur
            game_state["player_scores"][game_state["current_player"]] 

    # Aktualisierung der Anzeige aufrufen
    update_display()

    # Rufen Sie handle_end_game() nur einmal auf, wenn das Spiel beendet ist
    if game_state.get("is_game_over", False) and not end_game_displayed:
        handle_end_game()

    # Starten Sie das Update nach 1 Sekunde neu
    window.after(1000, update_game_state)


# Spielaktualisierung starten
update_game_state()

# MQTT konfigurieren und Kommunikation starten
setup_mqtt(canvas)

# Startet die Hauptschnittstellenschleife
window.mainloop()
