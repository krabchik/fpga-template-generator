import pathlib
import time

import jinja2
import yaml

BOARD_DIR = pathlib.Path('boards')


class Board:
    @classmethod
    def list_boards(cls, *args, **kwargs):
        for board_file in BOARD_DIR.iterdir():
            if board_file.is_dir():
                continue
            if board_file.name.endswith('.yaml') or \
                    board_file.name.endswith('.yml'):
                yield Board(board_file.name, *args, **kwargs)

    @classmethod
    def get_board_by_name(cls, name: str, *args, **kwargs):
        for board in cls.list_boards(*args, **kwargs):
            if board.name == name:
                return board
        raise ValueError(f'No such board')

    def __init__(self, board_config_name, project_name: str = None):
        config_path = BOARD_DIR / board_config_name
        if not config_path.exists():
            raise ValueError(f'Cant find config for {board_config_name} in {BOARD_DIR}')

        with open(config_path, encoding='utf-8') as f:
            config = f.read()
        try:
            self.config = yaml.safe_load(config)
        except yaml.YAMLError as exc:
            raise ValueError(f'YAML error in {config_path}: {exc}')

        templates_dir = self.config.get('templates_dir', self.name)
        self.templates_dir = BOARD_DIR / templates_dir
        if not self.templates_dir.exists() or not self.templates_dir.is_dir():
            raise ValueError(f'Cant find templates for {templates_dir}')

        self.project_name = project_name or self.name

        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_dir))

    @property
    def manufacturer(self):
        return self.config['manufacturer']

    @property
    def family(self):
        return self.config['family']

    @property
    def device(self):
        return self.config['device']

    @property
    def name(self):
        return self.config['name']

    @property
    def project_name(self):
        return self.config['project_name']

    @project_name.setter
    def project_name(self, project_name: str):
        project_name = project_name.replace(' ', '')
        project_name = project_name.replace('-', '_')
        self.config['project_name'] = project_name

    @property
    def image(self):
        return self.config['image']

    @property
    def components(self):
        return self.config['components']

    @property
    def extras(self):
        return self.config['extras']

    def use_component_by_label(self, component_label):
        for component_name, component in self.components.items():
            if component['label'] == component_label:
                component['use'] = True
                break
        else:
            raise KeyError(f'No component {component_label} found for board {self.name}')

    def use_component_by_name(self, component_name):
        component = self.components.get(component_name, None)
        if component is None:
            raise KeyError(f'No component {component_name} found for board {self.name}')
        component['use'] = True

    def set_extra(self, key: str, value) -> None:
        if key not in self.extras:
            raise KeyError(f'No such extra key for board {self.name}')
        expected_type = self.extras[key]['type']
        passed_type = str(type(value))
        if expected_type != passed_type:
            raise TypeError(f'Passed value {value} of type {passed_type} instead of {expected_type} for key {key}')

        self.extras[key]['value'] = value

    def fill_from_default_values(self):
        for extra in self.extras.values():
            if 'value' not in extra:
                extra['value'] = extra['default']

    def render_to(self, directory: pathlib.Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)

        self.fill_from_default_values()
        context = self.config.copy()

        context['components'] = {key: value for key, value in context['components'].items() if value.get('use', False)}

        time_date = time.strftime('%H:%M:%S %B %d, %Y')
        context['time_date'] = time_date

        for template_name in self.env.list_templates():
            template = self.env.get_template(template_name)
            rendered_file = template.render(context)

            rendered_file_path = directory / (self.project_name + '.' + '.'.join(template_name.split('.')[1:]))
            print('Writing to', rendered_file_path)

            rendered_file_path.touch()
            rendered_file_path.write_text(rendered_file)

    def __str__(self):
        return str(self.config)


if __name__ == '__main__':
    all_boards = [board for board in Board.list_boards()]
    for board in all_boards:
        print(board)
    board = all_boards[0]
    board.project_name = 'kto'
    board.render_to('rendered/' + board.name)
