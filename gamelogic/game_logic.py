
import random
import json
import threading
import time


FULL_GRID_TOPIC = "sudoku/game_sync"  
SYNCH_GAME_TOPIC = "game/grid"
START_GAME_TOPIC = "game/start"
UPDATE_GAME_TOPIC = "game/update"
RESTART_GAME_TOPIC = "game/restart"
RESTARTED_GAME_TOPIC = "game/restarted"
END_GAME_TOPIC = "game/end"
LED_GAME_TOPIC = "game/led"

GRID_SIZE = 9
current_player = 0  
player_scores = {}

POINTS = {
    'easy': 1,
    'medium': 1.5,
    'hard': 2
}


BONUS_THRESHOLDS = {
    'easy': [(10, 1), (20, 0.5)],
    'medium': [(7, 1), (15, 0.5)],
    'hard': [(5, 1), (8, 0.5)]
}
game_state = {
    "game_active": False,
    "selected_difficulty": None,
    "grid": [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
    "current_player": current_player,
    "time_limit": 30000,  # 30 Sekunden
    "timer_running": False,
    "player_scores": [0, 0],
    "base_points": 1,
    "timer":0,
    "start_time":None,
    "is_game_over": False,
    "ki":False,
    "player_id":0    
    
}


def is_game_over(client,game_state):

    if all(cell != 0 for row in game_state["grid"] for cell in row):
        game_state["is_game_over"] = True
        client.publish(LED_GAME_TOPIC, json.dumps({"state": "off"}))

        # Ermittlung des Gewinners anhand von Punktzahlen
        scores = game_state["player_scores"]
        if scores[0] > scores[1]:
            return 1  # Spieler 1 hat gewonnen
        elif scores[1] > scores[0]:
            return 2  #  Spieler 2 hat gewonnen
        else:
            return 0 

    return None


def restart_game(client, payload):

    global game_state
    previous_ki = game_state.get("ki", False)
    previous_player_id = game_state.get("player_id", 1) 
    game_state = {
        "game_active": False,
        "selected_difficulty": None,
        "grid": [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
        "current_player": 0,
        "time_limit": 30000,  
        "timer_running": False,
        "player_scores": [0, 0],
        "base_points": 1,
        "timer": 0,
        "is_game_over": False ,
        "start_time": None,
        "ki":previous_ki,
        "player_id":previous_player_id
    }

    # Veröffentlichen des Status des zurückgesetzten Spiels im Topic Neustart
    reset_message = json.dumps(game_state)
    if "ki" in game_state and game_state["ki"]:
            client.publish(f"{RESTARTED_GAME_TOPIC}/{previous_player_id}", reset_message)
            KI_target_topic = f"game/led/{previous_player_id}" 
            client.publish(KI_target_topic, json.dumps({"state": "off"})) 
    else:
        print("le ki est faux")          
        client.publish(RESTARTED_GAME_TOPIC, reset_message)
        client.publish(LED_GAME_TOPIC, json.dumps({"state": "off"}))
    
    print("Game has been restarted. Sending new game state to clients.")



# Funktion zur Berechnung von Punkten
def calculate_points(difficulty, time_taken, correct_move=True, current_score=0):
    """
    Berechnet die Punkte basierend auf der Schwierigkeit, der benötigten Zeit, 
    der Gültigkeit der Antwort, und die Punktehistorie des Spielers.
    """
    base_points = POINTS[difficulty]
    penalty_points = 1  
    bonus = 0

    print(f"=== Punkte Berechnung ===")
    print(f"Difficulty : {difficulty}, Zeit genommen : {time_taken}, Korrekt Bewegung : {correct_move}")

    # Überprüfen Sie die Bonusschwellen
    for threshold, bonus_points in BONUS_THRESHOLDS[difficulty]:
        if time_taken < threshold:
            bonus = bonus_points
            print(f"Bonus  : {bonus} (schwelle : {threshold})")
            break
    
    if not correct_move:
        # Bei falscher Bewegung die Maschen um 1 Masche reduzieren
        final_points = max(current_score - penalty_points, 0)  
        print(f"Mouvement incorrect, points calculés : {final_points}")
        return final_points

    final_points = max(base_points + bonus, 0)  # Wenn der Zug richtig ist, füge die Basispunkte und Boni hinzu
    print(f"korrekte Bewegung, Punktberechnung : {final_points}")
    return final_points


def update_score(client, game_state, player_index, correct_move=True):
    """
    Aktualisiert der Punktzahl von aktuelem Spieler nach richtige Bewegung.
    """
    
    print("=== Aktualisierung der Punktzahl ===")
    print(f"Aktuel Spieler  : {player_index}")
    print(f"korrekte Bewegung : {correct_move}")
   
    # Wiederherstellung der Schwierigkeit und der benötigten Zeit
    difficulty = game_state["selected_difficulty"]
    print(f"ausgewähhlte Schwierigkeitsgrad : {difficulty}")

    start_time = game_state["start_time"]  
    time_taken = (time.time() - start_time)  
    print(f" Verstrichene Zeit: {time_taken:.2f} Sekunden")

    # Rufen Sie den aktuellen Punktestand des Spielers ab
    old_score = game_state["player_scores"][player_index]
    print(f"last score : {old_score}")

    # Punkt Berechnung
    points_earned = calculate_points(difficulty, time_taken, correct_move, current_score=old_score)
    print(f"Berechnete Punkte : {points_earned}")

    if correct_move:
        # Wenn der Zug richtig ist, addieren Sie die Punkte zur aktuellen Punktzahl
        new_score = old_score + points_earned
    else:
        # Wenn die Bewegung falsch ist, verwenden Sie die berechneten Punkte (die niedriger sein können)
        new_score = old_score - 1

    print(f"last score : {old_score}, New score : {new_score}")

    # Aktualisieren des Punktestands im Spielzustand
    game_state["player_scores"][player_index] = new_score

    # Veröffentlichen Sie aktualisierte Bewertungen für alle Kunden
    score_update = {
        "player_scores": game_state["player_scores"],
        "current_player": game_state["current_player"]  
    }
    print(f"published message : {json.dumps(score_update)}")

    client.publish(UPDATE_GAME_TOPIC, json.dumps(score_update))  
    print("=== Spielend ===")


def generate_filled_sudoku():
    """
    Generiert ein gefülltes Sudoku-Raster.
    """
    grid = [[0 for _ in range(9)] for _ in range(9)]

    def fill_grid():
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    random_nums = random.sample(range(1, 10), 9)
                    for num in random_nums:
                        if is_valid_move(grid, row, col, num):
                            grid[row][col] = num
                            if fill_grid():
                                return True
                            grid[row][col] = 0
                    return False
        return True

    fill_grid()
    return grid

def generate_sudoku_with_holes(filled_grid, holes):
    """
    Generiert ein Sudoku-Gitter mit einer bestimmten Anzahl von Löchern.
    """
    grid = [row[:] for row in filled_grid]
    count = holes
    while count > 0:
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if grid[row][col] != 0:
            grid[row][col] = 0
            count -= 1
    return grid

def is_valid_move(grid, row, col, num):
    """
    Überprüft, ob eine Zahl in einer bestimmten Zelle platziert werden kann.
    """
    if num in grid[row]:
        return False
    if num in [grid[i][col] for i in range(9)]:
        return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if grid[i][j] == num:
                return False
    return True



def ki_make_move(client):
    global game_state

    if not game_state["game_active"] or not game_state["ki"]:
        return  

    difficulty = game_state["selected_difficulty"]
    grid = game_state["grid"]
    solution = game_state["filled_grid"]


    if "ki_sequence_index" not in game_state:
        game_state["ki_sequence_index"] = 0  

    #Verfügbare Positionen ermitteln (leere Boxen)
    empty_positions = [(i, j) for i in range(9) for j in range(9) if grid[i][j] == 0]
    if not empty_positions:
        return  

    # Definieren Sie KI-Verhalten basierend auf der Schwierigkeit
    if difficulty == "easy":
        win_count, lose_count = 6, 3
        delay_min, delay_max = 5, 30  # Verzögerung zwischen 5 und 30 Sekunden für "easy"
    elif difficulty == "medium":
        win_count, lose_count = 5, 2
        delay_min, delay_max = 5, 20  # Verzögerung zwischen 5 und 20 Sekunden für "medium"
    else:  # difficult
        win_count, lose_count = 4, 1
        delay_min, delay_max = 3, 10  #Verzögerung zwischen 3 und 10 Sekunden für "hard"

    # Abfolge von Zügen (Beispiel: [Sieg, Sieg, Sieg, Niederlage, Sieg, Niederlage, etc.])
    sequence = ([True] * win_count) + ([False] * lose_count)
    random.shuffle(sequence)  # Mischen Sie die Reihenfolge, um nicht zu vorhersehbar zu sein

    #Bestimme, ob die KI diesen Zug gewinnen oder verlieren soll
    if game_state["ki_sequence_index"] >= len(sequence):
        game_state["ki_sequence_index"] = 0  # Réinitialiser le cycle
    should_win = sequence[game_state["ki_sequence_index"]]
    game_state["ki_sequence_index"] += 1

    i, j = random.choice(empty_positions)

    if should_win:
        value = solution[i][j]  # KI spielt die richtige Antwort
    else:
        value = random.randint(1, 9)  # Die KI spielt eine Zufallszahl ab
        while value == solution[i][j]:  # Stellen Sie sicher, dass sie falsch liegt
            value = random.randint(1, 9)

    #Simulieren Sie eine zufällige Verzögerung basierend auf dem Schwierigkeitsgrad
    delay = random.randint(delay_min, delay_max)  # Variable Verzögerung je nach Schwierigkeitsgrad
    print(f"L'IA joue dans {delay} secondes...")
    time.sleep(delay)

    # Simulieren Sie den Schlag, der gesendet wird (rufen Sie Ihre Funktion 'handle_grid_game' auf)
    handle_grid_update(client, {"row": i, "col": j, "number": value})

    message = {
        "row": i,
        "col": j,
        "number": value
    }
# client.publish("SYNCH_GAME_TOPIC", json.dumps(message))
    #client.publish(f"{SYNCH_GAME_TOPIC}/{game_state.get('player_id')}", json.dumps(message))

    print(f"Message publié sur {SYNCH_GAME_TOPIC}: {message}")




def handle_grid_update(client, payload):
    """
    Verwaltet die Aktualisierung des Netzes nach Erhalt der Kundendaten, Verwenden game_state Rasters als aktuelles Raster.
    """
    try:
        
        global game_state

        # prüf das aktuelle Spielzustand
        print(f" game_state aktuel : {game_state}")

        # Extraire les données du payload
        row = payload.get('row')
        col = payload.get('col')
        number = payload.get('number')
        target_topic = f"game/led/{game_state['current_player']}" 
        

        if row is None or col is None or number is None:
            print("Erreur : Fehlende Daten in der Payload")
            return

        # Greifen Sie von game_state aus auf das aktuelle Raster zu
        grid = game_state.get('grid')

        if grid is None:
            print("Error : Raster in game_state nicht verfügbar")
            return

        filled_grid = game_state.get('filled_grid')
        if filled_grid is None:
            print("Error : Gefülltes Gitter in game_state nicht verfügbar")
            return

        correct_number = filled_grid[row][col] 


        # Prüfen Sie, ob die Bewegung gültig ist

        # if is_valid_move(grid, row, col, number): 
        #  alte Methode, die den is_valid_move verwendet,
        #  um zu überprüfen, ob die Ziffer eingefügt werden kann... aber weniger robust, wenn man tatsächlich spielt
        if number == correct_number:    
            grid[row][col] = number
            print(f"Ziffer {number} in das Feld ({row}, {col})")
            game_state['grid'] = grid

            # Aktualisieren Sie die Punktzahl und starten Sie den Timer neu
            update_score(client, game_state, game_state["current_player"], correct_move=True)
            start_timer(client, force_restart=True)
            

            # Mit einer Erfolgsmeldung antworten
            response = {
                'status': 'success',
                'row': row,
                'col': col,
                'number': number,
                'color': 'green',
                'grid': game_state['grid']
            }
            
        else:
            print(f"Chiffre {number} invalide à la position ({row}, {col})")
            
            # next player
            update_score(client, game_state, game_state["current_player"], correct_move=False)
            switch_player(client)
            

            # Mit einer Fehlermeldung antworten
            response = {
                'status': 'error',
                'row': row,
                'col': col,
                'number': number,
                'color': 'red',
                'grid': game_state['grid'],
            }

        # Veröffentlichen der Antwort auf die Rasteraktualisierung
        if game_state["ki"]:
            print(f"le player id est {game_state['player_id']}")
            client.publish(f"{FULL_GRID_TOPIC}/{game_state.get('player_id')}", json.dumps(response))
            KI_target_topic = f"game/led/{game_state['player_id']}" 
            client.publish(KI_target_topic, json.dumps({"state": "green" if response["color"] == "green" else "red"}))
        else:
            client.publish(FULL_GRID_TOPIC, json.dumps(response))
            client.publish(target_topic, json.dumps({"state": "green" if response["color"] == "green" else "red"}))


        # Überprüfen Sie, ob das Spiel vorbei ist
        winner = is_game_over(client,game_state)
        if winner is not None:
            end_game_message = {
                "is_game_over": True,
                "winner": winner,
                "player_scores": game_state.get("player_scores", [0, 0])
            }
            client.publish(END_GAME_TOPIC, json.dumps(end_game_message))
            print(f"Jeu terminé. Message publié sur {END_GAME_TOPIC}: {end_game_message}")

    except Exception as e:
        print(f"Fehler bei der Behandlung der Rasteraktualisierung: {e}")


def handle_start_game(client, payload):
    try:
        global game_state  
        if game_state["game_active"]:
            print("Ein Spiel ist bereits im Gange!")
            return

        # Schwierigkeit beim Abrufen von "Payload"
        difficulty = payload.get("difficulty", "easy")
        ki = payload.get("ki", False)
        current_player_id = payload.get("player_id")
        player_id = 1 if int(current_player_id) else 0

        print(f"le id est {current_player_id}")

        if difficulty not in ["easy", "medium", "hard"]:
            print("Ungültiger Schwierigkeitsgrad.")
            return

        # Spielstatus aktualisieren
        game_state["game_active"] = True
        game_state["selected_difficulty"] = difficulty
        game_state["ki"] = ki 
        game_state["current_player"] = current_player_id
        game_state["ki_player"] = 1 if current_player_id == 0 else 0
        game_state["player_id"] = current_player_id



        # Legen Sie die Schwierigkeitsparameter fest: Löcher, Zeit, Punkte
        holes = {"easy": 20, "medium": 30, "hard": 40}.get(difficulty, 20)
        time_limit = {"easy": 30 * 1000, "medium": 20 * 1000, "hard": 10 * 1000}.get(difficulty, 30 * 1000)
        base_points = {"easy": 1, "medium": 1.5, "hard": 2}.get(difficulty, 1)

        # Generieren des Rasters
        filled_grid = generate_filled_sudoku()
        game_state["filled_grid"]=filled_grid 
        print("Solution of the Sudoku:")
        for row in game_state.get("filled_grid"):
            print(row) 
        sudoku_grid = generate_sudoku_with_holes(filled_grid, holes)
        game_state['grid'] = sudoku_grid

        # Spielinformationen im Bundesstaat speichern
        game_state["time_limit"] = time_limit
        game_state["base_points"] = base_points
        
        if ki:
            print("Le mode KI est activé. Le joueur affronte l'IA.")
        else:
            print("Mode Joueur vs Joueur activé.")  

        target_topic = f"game/led/{game_state['current_player']}" 


        # Veröffentlicht das Spielraster mit den zugehörigen Informationen
        response = {
            "grid": sudoku_grid,
            "difficulty": difficulty,
            "game_active": True,
            "time_limit": time_limit,
            "base_points": base_points,
            "current_player": game_state["current_player"] + 1,
            "ki": game_state["ki"]
        }

        if game_state["ki"]:
            client.publish(f"{START_GAME_TOPIC}/{game_state.get('player_id')}", json.dumps(response))
            client.publish(target_topic, json.dumps({"state": "on"}))
            client.publish(target_topic, json.dumps({"state": "blue"}))
        else:
            client.publish(START_GAME_TOPIC, json.dumps(response))
            client.publish(LED_GAME_TOPIC, json.dumps({"state": "on"}))
            client.publish(target_topic, json.dumps({"state": "blue"}))

        print(f"Grille publiée sur {START_GAME_TOPIC}")
        print("Affichage de la grille de départ", game_state['grid'])   


        # Starten des serverseitigen Timers
        start_timer(client)  
        game_state["start_time"] = time.time()

    except Exception as e:
        print(f"Erreur dans handle_start_game: {e}")



def start_timer(client, force_restart=False):
    global game_state

    
    if game_state.get("timer_running"):
        if not force_restart:
            return  
        else:
            game_state["timer_running"] = False  
            if "timer_thread" in game_state and game_state["timer_thread"].is_alive():
                game_state["timer_thread"].join() 

    # Timer-Variablen zurücksetzen
    game_state["timer_running"] = True
    game_state["timer"] = game_state["time_limit"]  

    # Starten eines neuen Countdown-Timers
    timer_thread = threading.Thread(target=countdown, args=(client,))
    timer_thread.daemon = True  
    timer_thread.start()
    game_state["timer_thread"] = timer_thread  

# Sperren, um zu verhindern, dass mehrere Threads einen Countdown ausführen
countdown_lock = threading.Lock()

def countdown(client):
    global game_state

    # Acquérir le verrou pour éviter plusieurs instances
    with countdown_lock:
        # Setzt die start_time zu Beginn jedes Countdowns zurück
        game_state["start_time"] = time.time()

        # Startet den Countdown
        while game_state["timer"] > 0 and game_state["timer_running"]:
            game_state["timer"] -= 1000  
            update_timer_on_client(client)  
            time.sleep(1) 

        if game_state["timer"] <= 0 and game_state["timer_running"]:
            game_state["timer_running"] = False
            print(f"Temps écoulé pour le joueur {game_state['current_player'] + 1}. Passage au joueur suivant.")
            switch_player(client)  

# Timer-Update für den Client

def update_timer_on_client(client):
    remaining_time = game_state["timer"] // 1000  
    client.publish(UPDATE_GAME_TOPIC, json.dumps({
        "time_left": remaining_time,
        "timer_running": game_state["timer_running"],
        "game_active": game_state["game_active"],
        "difficulty": game_state["selected_difficulty"],
        "current_player":game_state["current_player"],
        "player_id": game_state["player_id"]
    }))

def switch_player(client):
    global game_state

    # Spieler andern
    current_player = (game_state["current_player"] + 1) % 2 
    game_state["current_player"] = current_player
    print(f"Changement : Joueur {current_player + 1}")

    client.publish(UPDATE_GAME_TOPIC, json.dumps({
        "current_player": current_player,
    }))

    # Topic festlegen
    target_topic = f"game/led/{game_state['current_player']}"  
    target_topic2 = f"game/led/{(current_player + 1) % 2}" 

    print(f"Le target pour le joueur actif est {target_topic} et le jouer est {game_state['current_player']} ")
    print(f"Le target pour l'autre joueur est {target_topic2}")


    client.publish(target_topic2, json.dumps({"state": "off"}))  
    client.publish(target_topic, json.dumps({"state": "blue"}))  
    
    if game_state.get("ki_player") == current_player:
        print("C'est au tour de l'IA de jouer...")

        ki_thread = threading.Thread(target=ki_make_move, args=(client,))
        ki_thread.daemon = True
        ki_thread.start()


    start_timer(client, force_restart=True)



