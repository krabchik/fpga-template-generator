import pathlib
import shutil
import uuid

from flask import Flask, jsonify, render_template, request, send_file, session
from flask_cors import CORS

from board import Board
from util import clear_dir

app = Flask(__name__, static_folder='static')
CORS(app, supports_credentials=True)
app.secret_key = 'your_secret_key'  # Установите надежный секретный ключ
BASE_RENDER_DIR = pathlib.Path('rendered/output')
ARCHIVE_EXTENSION = 'zip'


BOARD_DATA = list(Board.list_boards())  # Загружаем все данные при запуске


@app.before_request
def set_session_id():
    if 'id' not in session:
        print('id not in session')
        session['id'] = str(uuid.uuid4())[:8]  # создание уникального id для каждого пользователя


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get-boards-names')
def get_boards_names():
    board_names = [board.name for board in BOARD_DATA]
    return jsonify(board_names)


@app.route('/get-board')
def get_board():
    board_name = request.args.get('board')

    try:
        board = Board.get_board_by_name(board_name)
    except ValueError:
        return jsonify({"error": "Плата не найдена"}), 404
    return jsonify(board.config)


@app.route('/render-board', methods=['POST'])
def render_board():
    session_dir = BASE_RENDER_DIR / session['id']
    render_dir = session_dir / 'rendered'
    clear_dir(session_dir)

    data: dict[str] = request.json
    print(data)
    try:
        board_name = data['board']
    except KeyError:
        return jsonify({"error": f'Не указано имя платы'}), 404

    project_name = data.get('project-name', None)
    try:
        board = Board.get_board_by_name(board_name, project_name=project_name)
    except ValueError as e:
        print('No board found for render request')
        return jsonify({"error": f"Плата {board_name} не найдена"}), 404

    print(project_name, session['id'])
    last_component = None
    extras = dict()
    try:
        for key in data:
            if key.startswith('component-') and data[key]:
                component_name = key[10:]
                last_component = component_name
                board.use_component_by_name(component_name)
            elif key.startswith('extras-'):
                extras[key[7:]] = data[key]
    except KeyError as e:
        print(last_component)
        print(f'Component {last_component} of board {board_name} doesn\'t exist')
        return jsonify({"error": f"Компонент {last_component} не найден"}), 404

    try:
        board.render_to(render_dir)
    except Exception as e:
        print('Error while render')
        print(e)
        return jsonify({"error": f"Ошибка при генерации архива"}), 404

    archive_path = session_dir / board.project_name
    shutil.make_archive(archive_path, ARCHIVE_EXTENSION, render_dir)

    return jsonify({'file_path': str(archive_path.as_posix())})


@app.route('/download-file')
def download_file():
    output_dir = BASE_RENDER_DIR / session['id']
    
    if not output_dir.exists():
        return jsonify({'error': 'No generated file'}), 404

    archive_files = [file for file in output_dir.iterdir() if file.is_file() and file.name.endswith(ARCHIVE_EXTENSION)]
    
    if not archive_files:
        return jsonify({'error': 'No generated file'}), 404
    
    if len(archive_files) > 1:
        return jsonify({'error': 'Found multiple archives'}), 400

    archive_file = archive_files[0]
    return send_file(archive_file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
