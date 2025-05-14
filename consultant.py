import json
import logging
from typing import Dict, Union

from nicegui import ui
from pages import create_header, add_styles, BUTTON_STYLE

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("consultant.log", mode='w', encoding='utf-8')
    ]
)


class Consultant:
    def __init__(self, file_name: str = None, action_key="действие"):
        """
        Класс для управления правилами и фактами.

        :param file_name: Имя файла для сохранения и загрузки данных.
        :param action_key: Ключ для действий в правилах.
        """
        if file_name is None:
            file_name = os.path.join(os.path.dirname(__file__), 'base.json')
        self.file_name = file_name
        self.action_key = action_key
        self.facts = {}
        self._data = self._load_data()
        self.rules = self._prepare_rules()
        self.questions = self._data.get('facts', {})
        self.current_rule_id = 0
        self.suggested_actions = []
        self.process_actions = []
        self.result = None

    def _prepare_rules(self) -> list:
        """Подготавливает правила, сортируя их в обратном порядке."""
        logging.debug("Подготовка правил: сортировка в обратном порядке")
        return [x[1] for x in sorted(self._data.get("rules", {}).items(), key=lambda x: int(x[0]))]

    def process_rules(self):
        """Обрабатывает правила: проверяет условия и добавляет факты, если правило выполнено."""
        logging.info("Начинаем обработку правил")
        for ind, rule in enumerate(self.rules[self.current_rule_id:]):
            self.current_rule_id = ind
            if_conditions = rule.get("if", {})
            then_conditions = rule.get("then", {})

            logging.debug(f"Текущее правило: {rule}")

            # Проверяем конфликты
            conflicts = [
                fact for fact, value in if_conditions.items()
                if self.facts.get(fact, -1) != -1 and self.facts[fact] != value
            ]
            if conflicts:
                logging.debug(f"Пропускаем правило из-за конфликта: {conflicts}")
                continue

            # Проверяем выполнение условий
            for condition, value in if_conditions.items():
                if condition not in self.facts:
                    logging.info(f"Не хватает факта для выполнения правила: {condition}")
                    return condition

            if ((if_conditions, then_conditions)) not in self.process_actions:
                # Применяем действия, если все условия выполнены
                self._apply_then(if_conditions, then_conditions)

        logging.info("Обработка правил завершена")

    def _apply_then(self, if_conditions: Dict[str, Union[int, str]], then_conditions: Dict[str, Union[int, str]]):
        """Применяет действия из блока "then"."""
        logging.info(f"Добавляем факты: {then_conditions}")
        self.facts.update(then_conditions)

        if self.action_key in then_conditions:
            logging.info(f"Добавлено действие: {then_conditions[self.action_key]}")
            self.suggested_actions.append(then_conditions[self.action_key])

        self.process_actions.append((if_conditions, then_conditions))
        logging.debug(f"Текущее состояние фактов: {self.facts}")

    def _load_data(self) -> Dict[str, Union[Dict, None]]:
        """Загрузка данных из JSON файла."""
        try:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                logging.info(f"Данные успешно загружены из {self.file_name}")
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Файл {self.file_name} не найден. Используем пустые данные.")
            return {'rules': {}, 'facts': {}}
        except json.JSONDecodeError:
            logging.error(f"Ошибка декодирования JSON в файле {self.file_name}. Используем пустые данные.")
            return {'rules': {}, 'facts': {}}

    def answer_question(self, fact: str, answer: Union[int, None]):
        """Добавляет ответ на вопрос в факты."""
        logging.info(f"Получен ответ на вопрос: {fact} = {answer}")
        self.facts[fact] = answer
        logging.debug(f"Обновленное состояние фактов: {self.facts}")


class ConsultantUI:

    def __init__(self):
        self.consultant = Consultant()
        self.current_question = ""

    def answer_question(self, answer: Union[int, None]):
        """Устанавливает значение факта на основе ответа пользователя."""
        self.consultant.answer_question(self.current_fact, answer)
        self.processing()
        self.actions_ui.refresh()

    @ui.refreshable
    def question_ui(self):
        """Обновляет пользовательский интерфейс в зависимости от текущего состояния."""
        with ui.element('div').classes('w-full h-100 d-flex content-center'):
            if self.current_question:
                create_header(self.current_question)
                with ui.row().classes("w-full d-flex justify-center p-5"):
                    ui.button('Да', on_click=lambda: self.answer_question(1))
                    ui.button('Нет', on_click=lambda: self.answer_question(0))
                    ui.button('Не знаю', on_click=lambda: self.answer_question(None))
                ui.separator()
            else:
                create_header("Консультация завершена.")

    @ui.refreshable
    def actions_ui(self):
        """Интерфейс для отображения действий и обработанных правил."""
        with ui.element("div").classes("row w-full d-flex justify-center p-0"):
            self._display_actions()
            self._display_process_actions()
        add_styles()

    def _display_actions(self):
        """Отображает список предложенных действий."""
        with ui.element("div").classes('overflow-auto col-6 ps-1 bg-gray0 border').style(
                'max-height: 80vh; min-height: 10vh'):
            for i, action in enumerate(self.consultant.suggested_actions):
                with ui.row().classes(f"{'bg-gray1' if i % 2 else 'bg-gray2'}"):
                    ui.label(action)

    def _display_process_actions(self):
        """Отображает список обработанных правил."""
        with ui.element("div").classes('overflow-auto col-6 pe-1 bg-gray0 border').style(
                'max-height: 80vh; min-height: 10vh'):
            for i, (if_conditions, then_conditions) in enumerate(self.consultant.process_actions):
                with ui.row().classes(f"{'bg-gray1' if i % 2 else 'bg-gray2'}"):
                    self._create_rule_expansion(if_conditions, then_conditions)

    def _create_rule_expansion(self, if_conditions: Dict[str, str], then_conditions: Dict[str, str]):
        """Создаёт разворачиваемый элемент для правила."""
        lab = []
        for key, value in then_conditions.items():
            lab.append(f"- {key} == {value}; ")
        with ui.expansion("".join(lab)):
            ui.label("ЕСЛИ")
            for key, value in if_conditions.items():
                ui.label(f"- {key} == {value}")
            ui.label("ТО")
            for key, value in then_conditions.items():
                ui.label(f"- {key} == {value}")

    def processing(self):
        question = self.consultant.process_rules()
        if question:
            self.ask_question(question)
        else:
            self.current_question = ""
            self.question_ui.refresh()

    def ask_question(self, fact):
        self.current_question = self.consultant.questions.get(fact, "")
        self.current_fact = fact
        self.question_ui.refresh()

    def cons_page(self):
        ui.button(icon="arrow_back", color="standart", on_click=lambda: ui.navigate.to("/")).props(BUTTON_STYLE).style(
            'position: absolute;')

        """Основная страница консультации."""
        self.question_ui()
        self.processing()
        self.actions_ui()
        ui.add_css(".nicegui-content{ padding: 0;}")
