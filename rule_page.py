from nicegui import ui

from pages import add_back_button, create_header, LABEL_STYLE, BUTTON_STYLE, create_list, INPUT_WIDTH, add_styles, \
    rules_manager as RULES_MANAGER


class RulePage:
    def __init__(self, rule_index):
        self.rules_manager = RULES_MANAGER.copy()
        self.rule_index = rule_index
        self._load()

    def _load(self):
        self.rule = self.rules_manager.get_rule(self.rule_index)
        self.facts = self.rules_manager.get_facts()
        self.temp_conditions = list(self.rule["if"].items())

    def act_or_fact(self, selected_value, action_val_input, fact_val_selector):
        """Функция, вызываемая при изменении выбора факта или действия."""
        if selected_value == "действие":
            action_val_input.visible = True
            fact_val_selector.visible = False
        else:
            action_val_input.visible = False
            fact_val_selector.visible = True

    def add_condition(self):
        """Добавление нового пустого условия."""
        self.temp_conditions.append((None, None))
        self.rows_list.refresh()

    def delete_condition(self, ind):
        """Удаление условия."""
        self.temp_conditions.pop(ind)
        self.rows_list.refresh()

    def reload_data(self):
        """Перезагрузка данных."""
        self.rules_manager.reload_data()
        self._load()
        ui.navigate.reload()

    def delete_dialog(self):
        with ui.dialog() as dialog, ui.card():
            ui.label('Hello world!')
            ui.button('Close', on_click=dialog.close)

    def save_conditions(self):
        """Сохранение изменений."""
        self.rules_manager.delete_all_conditions(self.rule_index)
        for (fact, val) in self.temp_conditions:
            if None not in (fact, val):
                self.rules_manager.add_condition(self.rule_index, fact, val)
        self._save()
        self.reload_data()

    def _save(self):
        """Сохранение изменений."""

        self.rules_manager.save()
        RULES_MANAGER.reload_data()

    def change_condition_fact(self, cond_id, fact):
        self.temp_conditions[cond_id] = (
            fact, self.temp_conditions[cond_id][1]
        )

    def change_condition_val(self, cond_id, val):
        self.temp_conditions[cond_id] = (
            self.temp_conditions[cond_id][0], val
        )

    def on_fact_change(self, val, action_val_input, fact_val_selector):
        self.act_or_fact(val, action_val_input, fact_val_selector)
        self.change_then_fact(val)

    def change_then_fact(self, val):
        self.rules_manager.set_then(self.rule_index, val, None)

    def change_then_val(self, val):
        self.rules_manager.set_then(self.rule_index, list(self.rule["then"].keys())[0], val) #todo: а если несколько и вообще уродливо

    def navigate_to_facts(self):
        """Переход на страницу фактов."""
        ui.navigate.to("/facts", True)

    def delete_rule(self):
        self.rules_manager.delete_rule(self.rule_index)
        self._save()
        ui.navigate.to("/rules")

    @ui.refreshable
    def rows_list(self):
        rows = []

        for ind, (fact, val) in enumerate(self.temp_conditions):
            rows.append([
                ui.select(
                    list(self.facts.keys()),
                    value=fact,
                    with_input=True,
                    new_value_mode="add-unique",
                    on_change=lambda x, i=ind: self.change_condition_fact(i, x.value),
                ).classes("align-middle my-auto"),
                ui.select(
                    [1, 0],
                    value=val,
                    on_change=lambda x, i=ind: self.change_condition_val(i, x.value),
                ).classes("align-middle my-auto"),
                ui.space(),
                ui.button(
                    icon="delete",
                    color="standart",
                    on_click=lambda i=ind: self.delete_condition(i),
                ).props(BUTTON_STYLE),
            ])

        ui.label("ЕСЛИ").classes("w-full p-0 ps-2 m-0").style(LABEL_STYLE)
        create_list(rows)

    def edit_page(self):
        """Инициализация страницы редактирования."""
        add_back_button(ui.navigate.back)
        create_header("Редактирование правила")
        self.rows_list()

        # Выбираем первое условие в "then"
        then = list(self.rule["then"].items())[0]

        with ui.row().classes("w-full p-2 justify-center"):
            ui.button(
                text="Добавить условие", color="green-6", on_click=self.add_condition
            )

        ui.label("ТО").classes("w-full p-0 ps-2 m-0").style(LABEL_STYLE)

        # Разметка для выбора действия или факта
        with ui.row().classes("w-full p-2"):
            fact_or_action_select = ui.select(
                list(self.facts.keys()),
                value=then[0],
                with_input=True,
                new_value_mode="add-unique",
            ).classes("align-middle my-auto")

            if then[0] == self.rules_manager.action_key:
                action_val_input = ui.input(value=then[1]).classes(
                    f"{INPUT_WIDTH} align-middle my-auto"
                )
                fact_val_selector = ui.select([1, 0], value=None).classes(
                    "align-middle my-auto"
                )
            else:
                action_val_input = ui.input().classes(
                    f"{INPUT_WIDTH} align-middle my-auto"
                )
                fact_val_selector = ui.select([1, 0], value=then[1]).classes(
                    "align-middle my-auto"
                )
            self.act_or_fact(then[0], action_val_input, fact_val_selector)
            fact_or_action_select.on_value_change(
                lambda x: self.on_fact_change(x.value, action_val_input, fact_val_selector)
            )
            action_val_input.on_value_change(
                lambda x: self.change_then_val(x.value)
            )
            fact_val_selector.on_value_change(
                lambda x: self.change_then_val(x.value)
            )

            # Кнопки действий
        with ui.row().classes("w-full p-2 justify-center"):
            ui.button(
                text="Сохранить изменения",
                color="green-6",
                on_click=self.save_conditions,
            )
            ui.button(
                text="Отменить изменения", color="red-6", on_click=self.reload_data
            )
            ui.button(
                text="Удалить правило",
                color="grey-10",
                on_click=self.delete_rule,
            )
            ui.button(
                text="Изменить факты", color="standart", on_click=self.navigate_to_facts
            )

        add_styles()
