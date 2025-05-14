from nicegui import ui
from rule_utils import rule_to_text
from rules_manager import RulesFactsManager

# Константы
CSS_STYLES = """
    .q-scrollarea__content { padding: 0 !important;} 
    .bg-gray1 {background-color: #ededed} 
    .bg-gray2 {background-color: #dedede}
    .bg-gray0 {background-color: #fefefe}
        .row-hover:hover {
        filter: brightness(0.95); /* Делаем цвет блеклым */
        transition: filter 0.15s; /* Плавный переход */
    }
"""

LABEL_STYLE = 'font-size: 120%'
BUTTON_STYLE = "flat"  # Используем один стиль для всех кнопок
ROW_STYLE = "w-full p-2"
BUTTON_WIDTH = "col-1"
INPUT_WIDTH = "col-7"

rules_manager = RulesFactsManager()


# Универсальная функция для добавления кнопки "назад"
def add_back_button(on_click):
    ui.button(icon="arrow_back", color="standart", on_click=on_click).props(BUTTON_STYLE).style('position: absolute;')


# Функция для добавления пользовательских стилей
def add_styles():
    ui.add_css(CSS_STYLES)


# Функция для создания списка элементов
def create_list(rows, height=50):
    """Создает список элементов из строк."""
    with ui.element("div").classes('overflow-auto w-full p-0 bg-light').style(f'max-height: {height}vh;') as rows_list:
        with ui.column().classes('w-full p-0 gap-0 bg-gray1'):
            for i, row in enumerate(rows):
                grey = "bg-gray1" if i % 2 else "bg-gray2"
                with ui.row().classes(f"{grey} {ROW_STYLE} row-hover") as X:

                    for col in row:
                        col.move(X)
    return rows_list


# Функция создания заголовка
def create_header(text):
    ui.label(text).classes("w-full text-center p-0").style(LABEL_STYLE)


# Страница редактирования фактов
def facts_page():  # todo: лучше перетащить в отдельный файл и при вызове передовать состояние
    """Создает страницу для редактирования фактов."""

    def delete_fact(fact_name):
        """Удаляет факт и уведомляет об ошибке, если он используется в правилах."""
        try:
            rules_manager.delete_fact(fact_name)
            rules_manager.save()
            ui.notify(f"Факт '{fact_name}' успешно удалён.")
            ui.navigate.reload()
        except ValueError as e:
            # Показываем ошибку в нотификации
            ui.notify(str(e), color="red")

    def update_fact_question(fact_name, new_question):
        """Обновляет вопрос для указанного факта."""
        rules_manager.update_fact_question(fact_name, new_question)
        rules_manager.save()

    def add_fact(fact_name, question):
        """Добавляет новый факт с указанным именем и вопросом."""
        if not fact_name or not question:
            ui.notify("Поля имени факта и вопроса не могут быть пустыми.", color="red")
            return

        if fact_name in rules_manager.get_facts():
            ui.notify(f"Факт с именем '{fact_name}' уже существует.", color="red")
            return

        rules_manager.add_fact(fact_name, question)
        rules_manager.save()
        ui.notify(f"Факт '{fact_name}' добавлен.")
        ui.navigate.reload()

    facts = rules_manager.get_facts()
    rows = []

    # Добавляем кнопку для возвращения назад
    add_back_button(lambda: ui.navigate.to("/rules"))  # не туда

    # Создаем заголовок страницы
    create_header("Факты")

    # Генерируем строки для отображения фактов
    for fact_name, question in facts.items():
        if fact_name == rules_manager.action_key:
            continue
        rows.append([
            # Отображение имени факта (только текст)
            ui.label(fact_name).classes("align-middle col-3 my-auto"),

            # Поле ввода для редактирования вопроса
            ui.input(value=question, on_change=lambda e, name=fact_name: update_fact_question(name, e.value))
            .classes("col-7 align-middle my-auto"),

            # Кнопка для удаления факта
            ui.button(icon="delete", color="standart", on_click=lambda name=fact_name: delete_fact(name))
            .props(BUTTON_STYLE).classes("col-1 my-auto"),
        ])

    # Создаем список фактов
    create_list(rows, 80)

    # Добавляем поля ввода для имени факта и вопроса, а также кнопку
    with ui.row().classes("w-full p-0 gap-2"):
        fact_name_input = ui.input(label="Имя факта").classes("col-3")
        fact_question_input = ui.input(label="Вопрос для факта").classes("col-6")
        ui.button(
            text="Добавить факт", color="standart",
            on_click=lambda: add_fact(fact_name_input.value, fact_question_input.value)
        ).classes("col-2 my-auto mx-auto").props("no-caps outline")

    add_styles()


def add_rule():
    rules_manager.add_blank_rule()
    rules_manager.save()
    ui.navigate.reload()


def delete_rule(ind):
    rules_manager.delete_rule(ind)
    rules_manager.save()
    ui.navigate.reload()


def move_rule_up(ind):
    rules_manager.move_rule_up(ind)
    rules_manager.save()
    ui.navigate.reload()


def move_rule_down(ind):
    rules_manager.move_rule_down(ind)
    rules_manager.save()
    ui.navigate.reload()


# Страница отображения списка правил
def rules_page():
    """Страница отображения списка правил."""
    rules = rules_manager.get_rules()
    add_back_button(lambda: ui.navigate.to("/"))

    create_header("Список правил")

    rows = []
    for i in rules.keys():
        # Создаём контейнер для кнопок вверх и вниз
        with ui.row().classes("col-1 justify-center my-auto").style("gap: 0.25rem;") as move_buttons:
            ui.button(icon="arrow_upward", color="standard", on_click=lambda r=i: move_rule_up(r)).props(BUTTON_STYLE)
            ui.button(icon="arrow_downward", color="standard", on_click=lambda r=i: move_rule_down(r)).props(
                BUTTON_STYLE)

        # Создаём контейнер для кнопок редактирования и удаления
        with ui.row().classes("col-2 justify-center my-auto").style("gap: 0.25rem;") as action_buttons:
            ui.button(icon="edit", color="standard", on_click=lambda r=i: ui.navigate.to(f"rule/{r}")).props(
                BUTTON_STYLE)
            ui.button(icon="delete", color="standard", on_click=lambda r=i: delete_rule(r)).props(BUTTON_STYLE)

        # Добавляем элементы в строку
        rows.append([
            ui.label(rule_to_text(rules[i])).classes("align-middle my-auto col-7"),  # Текст с описанием правила
            ui.space(),
            move_buttons,  # Кнопки вверх/вниз
            action_buttons  # Кнопки редактировать/удалить
        ])

    create_list(rows)
    with ui.row().classes("w-full p-2 justify-center"):
        ui.button(
            text="Добавить правило", color="green-6", on_click=add_rule
        )

    add_styles()


# Главная страница
def main_page():
    with ui.column().classes("w-full p-12 my-auto justify-center items-center gap-4"):
        ui.button('Изменить правила', on_click=lambda: ui.navigate.to("/rules")).classes("w-1/3")
        ui.button('Консультация', on_click=lambda: ui.navigate.to("/cons")).classes("w-1/3")
