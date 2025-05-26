import os
from pathlib import Path
from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory
import pytesseract
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

# ==== CONFIGURATION TESSERACT DANS LE CONTAINER ====
# Forcer le binaire et le dossier de données
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/usr/share/tessdata"
# ================================================

# Configuration projet Kedro
PROJECT_PATH = Path(__file__).parent  # Racine du projet Kedro
PIPELINE_NAME = None  # None pour pipeline par défaut

# Templates HTML
INDEX_HTML = '''
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <title>OCR Pipeline</title>
  </head>
  <body>
    <h1>Lancer le pipeline OCR</h1>
    <form method="post">
      <button type="submit">Exécuter</button>
    </form>
  </body>
</html>
'''

RESULT_HTML = '''
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <title>Résultat Annoté</title>
  </head>
  <body>
    <h1>Vidéo Annotée</h1>
    <video width="720" controls>
      <source src="{{ url_for('serve_output') }}" type="video/mp4">
      Votre navigateur ne supporte pas la lecture vidéo.
    </video>
    <br/><br/>
    <a href="{{ url_for('index') }}">Revenir</a>
  </body>
</html>
'''

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Boot Kedro sans installation globale
        metadata = bootstrap_project(PROJECT_PATH)
        session = KedroSession.create(project_path=metadata.project_path)
        session.run(pipeline_name=PIPELINE_NAME)
        return redirect(url_for('result'))
    return render_template_string(INDEX_HTML)

@app.route('/result')
def result():
    return render_template_string(RESULT_HTML)

@app.route('/output')
def serve_output():
    # Chemin relatif vers la vidéo annotée
    output_path = PROJECT_PATH / "data/07_model_output/annotated_video.mp4"
    return send_from_directory(
        directory=str(PROJECT_PATH),
        path=str(output_path.relative_to(PROJECT_PATH))    
    )

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    # debug=True pour le développement
    app.run(debug=True, host='0.0.0.0', port=port)
