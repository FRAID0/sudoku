# Utilise une image officielle de Python comme base
FROM python:3.9-slim

# Définir un répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires depuis le répertoire local
COPY . /app

# Installer les dépendances spécifiées dans le fichier requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9020
# Définir la commande pour exécuter votre application
CMD ["python", "-u", "mqtt.py"]
