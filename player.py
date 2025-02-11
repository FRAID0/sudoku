import paho.mqtt.client as mqtt
import json
#import gpio_manager


# MQTT Setup
#BROKER = "iot.it.hs-worms.de"
BROKER = "test.mosquitto.org"
PORT = 1883

# Topics MQTT
MQTT_TOPICS = {
    "FULL_GRID": "sudoku/game_sync",
    "START_GAME": "game/start",
    "SYNCH_GAME": "game/grid",
    "UPDATE_GAME": "game/update",
    "RESTART_GAME": "game/restart",
    "RESTARTED_GAME": "game/restarted",
    "END_GAME": "game/end",

# TOPICS KI_
    "KI_FULL_GRID": "sudoku/game_sync/1",
    "KI_START_GAME": "game/start/1",
    "KI_SYNCH_GAME": "game/grid/1",
    "KI_UPDATE_GAME": "game/update/1",
    "KI_RESTART_GAME": "game/restart/1",
    "KI_RESTARTED_GAME": "game/restarted/1"
}


# Initialisieren des MQTT-Clients
client = mqtt.Client()


game_state = {
    "game_active": True,
    "selected_difficulty": None,
    "grid": None,
    "current_player": 0,
    "time_limit": 30000,  
    "timer_running": False,
    "base_points": 1,
    "player_scores": [0, 0],
    "timer":0,
    "is_game_over": False,
    "winner":0,
    "ki": False,

}

restart_in_progress = False
player_id = 1
cell_width =142
cell_height = 80
margin = 0

def update_game_state(new_state):
    global game_state
    game_state.update(new_state)



# Sendet den gewählten Schwierigkeitsgrad und den Status des KI-Modus an den Server
def send_difficulty(difficulty):
    message = json.dumps({
        "difficulty": difficulty,
        "player_id": player_id,
        "ki": game_state["ki"] 
        })
    client.publish(MQTT_TOPICS["START_GAME"], message)
    print(f"Schwierigkeitsgrad '{difficulty}' mit KI-Modus '{game_state['ki']}' gesendet an {MQTT_TOPICS['START_GAME']}")
    print (f"le player_id est {player_id}")

    game_state["game_activate"] = True



def send_restart_message():

    global restart_in_progress

    if not restart_in_progress:
        restart_in_progress = True
        restart_message = json.dumps({"restart": True})
        client.publish( MQTT_TOPICS["RESTART_GAME"], restart_message)  
        print("An den Server gesendete Neustartnachricht.")
        restart_in_progress = False


def update_grid_ui(grid, canvas, cell_width, cell_height, margin):

    canvas.delete("all")  

    grid_size = len(grid)  

   
    for i in range(grid_size + 1):
        line_width = 3 if i % 3 == 0 else 1 
        # Horizontale Linien
        canvas.create_line(
            margin,
            margin + i * cell_height,
            margin + grid_size * cell_width,
            margin + i * cell_height,
            width=line_width
        )
        # Vertikale Linien
        canvas.create_line(
            margin + i * cell_width,
            margin,
            margin + i * cell_width,
            margin + grid_size * cell_height,
            width=line_width
        )

    # Zeichnen Sie jede Zelle und ihren Inhalt
    for row in range(grid_size):
        for col in range(grid_size):
            value = grid[row][col]
            x1 = margin + col * cell_width
            y1 = margin + row * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height

            # Zeichnen Sie für jede Zelle ein Rechteck
            canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")

            # Fügen Sie der Zelle Text hinzu, wenn ein Wert vorhanden ist
            if value != 0:
                canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=str(value),
                    font=("Arial", int(min(cell_width, cell_height) * 0.4))  
                )


def on_message(client, userdata, message):
    """
    Verwaltet empfangene MQTT-Nachrichten und aktualisiert den Spielstatus und die Benutzeroberfläche.
    """
    global game_state  
    print(f"Das aktuelle game_state ist: {game_state}")

    try:
        # Dekodierung der MQTT-Nachricht
        payload = json.loads(message.payload.decode())
        #print("Die vom client erhaltene Nachricht lautet:", payload)
        #print("Das aktuelle Raster ist :", game_state["grid"])

        # Mise à jour de l'interface utilisateur si une grille est reçue
        if "grid" in payload:
            grid = payload["grid"]
            game_state["grid"]=grid
            print("Grid vom Broker erhalten:", grid)
            canvas = userdata["canvas"]
            update_grid_ui(grid, canvas,cell_width, cell_height, margin) 

        # Überprüfen Sie, ob es sich um ein Grid-Update oder eine Serverantwort handelt
        if "status" in payload and "row" in payload and "col" in payload and "number" in payload:
            # Serverantwort nach Validierung einer Ziffer
            game_state["grid"] = payload.get("grid", None)
            handle_server_response(payload, userdata)
        else:
            # Globale Aktualisierung des Spielstatus
            game_state["game_active"] = payload.get("game_active", False)  # Spielstatus (aktiv/inaktiv)
            game_state["selected_difficulty"] = payload.get("difficulty", None)  # Ausgewählter Schwierigkeitsgrad
            game_state["current_player"] = payload.get("current_player", game_state["current_player"])  # Jaktueller Spieler (0 oder 1)
            game_state["timer"] = payload.get("time_left", game_state["timer"])  # Verbleibende Zeit in Sekunden
            game_state["timer_running"] = payload.get("timer_running", game_state["timer_running"])  # wenn der Timer läuft

            # Spielstatusverwaltung
            if game_state["game_active"]:
                print(f"Der Spielstand ist : {game_state['game_active']}")
                print(f"Das Spiel begann mit Schwierigkeiten : {game_state['selected_difficulty']}")
            else:
                print("Le jeu est inactif.")

            # Aktuelles Spieler-Update
            if "current_player" in payload:
                print(f"Aktueller Spieler: {game_state['current_player'] + 1}")

            # Mise à jour du timer
            if "time_left" in payload:
                remaining_time = game_state["timer"]  
                print(f"Verbleibende Zeit : {remaining_time} secondes")

            # Mise à jour des scores
            if "player_scores" in payload:
                game_state["player_scores"] = payload["player_scores"]
                print(f"Scores mis à jour : {game_state['player_scores']}")

            # Wenn der Timer läuft, starten Sie die Zählung oder setzen Sie sie fort
            if game_state["timer_running"]:
                print("Der Timer läuft.")
            else:
                print("Der Timer wird gestoppt.")

            if "player_id" in payload:
                game_state["player_id"]=0
                game_state["player_id"]= player_id
                print(f"le player_id est {player_id} et le game de sa est {game_state['player_id']}")
                
            # Überprüfen Sie, ob das Spiel beendet ist
            if payload.get("is_game_over"):
                game_state["winner"] = payload.get("winner", None)
                game_state["is_game_over"] = payload.get("is_game_over", True)
                print(f"Game Over-Status : {game_state['is_game_over']}")
                game_state["player_scores"] = payload["player_scores"]
                print("Das Spiel ist vorbei!")
                if payload["winner"] == 0:
                    print("Es ist ein Unentschieden!")
                else:
                    print(f"Der Spieler {payload['winner']} hat gewonnen")
                print(f"Endergebnisse : {payload['player_scores']}")
    except Exception as e:
        print("Fehler beim Aktualisieren des Spiels :", e)





def handle_server_response(payload, userdata):
    """
    Verwaltet die Antwort des Servers auf die Validierung einer Ziffer.
    """
    try:
        # Extrahieren von Daten aus der Antwort
        status = payload.get("status")
        row = payload.get("row")
        col = payload.get("col")
        number = payload.get("number")
        color = "green" if status == "success" else "red"

        print(f"Server-Antwort: {'Valide' if status == 'success' else 'Invalide'} pour ({row}, {col}) -> {number}")

        # Aktualisieren der Benutzeroberfläche
        canvas = userdata["canvas"]
        update_ui_cell(row, col, number, color, canvas,cell_width, cell_height, margin)

    except Exception as e:
        print("Fehler bei der Verarbeitung der Serverantwort :", e)



def update_ui_cell(row, col, number, color, canvas, cell_width, cell_height, margin):

    try:
       
        x1 = margin + col * cell_width
        y1 = margin + row * cell_height
        x2 = x1 + cell_width
        y2 = y1 + cell_height

        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

        if number != 0:
            canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=str(number),
                font=("Arial", int(min(cell_width, cell_height) * 0.4)) 
            )

    except Exception as e:
        print(f"Fehler beim Aktualisieren der UI-Zelle({row}, {col}): {e}")



        
        
# Senden von Daten an den Server über MQTT
def send_to_server(row, col, number):
    message = {
        "row": row,
        "col": col,
        "number": number
        
    }
    client.publish( MQTT_TOPICS["SYNCH_GAME"], json.dumps(message))   
    #print("Grille actuelle recu  mise à jour :", game_state.get('grid'))
    print(f"Gesendete JSON-Nachricht : {json.dumps(message)}")
    print(f"Senden der Verschlüsselung an den Server : {message}")
    
    


    
# Konfiguriert den MQTT-Client
def setup_mqtt(canvas):
    client.on_message = on_message
    client.user_data_set({"canvas": canvas})  
    client.connect(BROKER, PORT, 60)

    # Abonnement automatique à tous les topics
    for topic in MQTT_TOPICS.values():
        client.subscribe(topic)

    client.loop_start()  # Démarrer la boucle MQTT

