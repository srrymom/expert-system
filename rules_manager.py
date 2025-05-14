import copy
import json
import os
from typing import Dict, List, Union


class RulesFactsManager:
    def __init__(self, file_name: str = None, action_key="действие"):
        """
        Класс для управления правилами и фактами.

        :param file_name: Имя файла для сохранения и загрузки данных.
        """
        if file_name is None:
            file_name = os.path.join(os.path.dirname(__file__), 'base.json')

        self.file_name = file_name
        self.action_key = action_key
        self.data = self._load_data()
        self._facts = self.data["facts"]
        self._rules = self.data["rules"]

    # --- Загрузка и сохранение данных ---

    def _load_data(self) -> Dict[str, Union[Dict, None]]:
        """Загрузка данных из JSON файла."""
        try:
            with open(self.file_name, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'rules': {}, 'facts': {}}

    def _save_data(self) -> None:
        """Сохранение текущего состояния данных в JSON файл."""
        with open(self.file_name, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)

    def save(self) -> None:
        """Сохранить изменения и добавить отсутствующие факты."""
        self._sync_facts_with_rules()
        self._save_data()

    def reload_data(self) -> None:
        """Перезагрузка данных из файла."""
        self.data = self._load_data()
        self._facts = self.data["facts"]
        self._rules = self.data["rules"]

    # --- Управление фактами ---

    def get_facts(self) -> Dict[str, str]:
        """Получить все факты."""
        return self.data.get('facts', {})

    def update_fact_question(self, fact_id: str, description: str) -> None:
        if fact_id in self._facts:
            self._facts[fact_id] = description

    def add_fact(self, fact_id: str, description: str) -> None:
        """Добавить факт."""
        self.data['facts'][fact_id] = description

    def delete_fact(self, fact_id: str) -> bool:
        """Удалить факт. Нельзя удалить факт, если он используется в правилах или имеет ключ self.action_key."""
        if fact_id == self.action_key:
            raise ValueError(f"Невозможно удалить факт с ключом '{self.action_key}'.")

        # Проверяем, используется ли факт в правилах
        for rule_id, rule in self.data["rules"].items():
            if fact_id in rule.get("if", {}) or fact_id in rule.get("then", {}):
                raise ValueError(f"Факт '{fact_id}' используется в правиле '{rule_id}' и не может быть удалён.")

        # Удаляем факт, если он не используется
        return self.data['facts'].pop(fact_id, None) is not None

    # --- Управление правилами ---

    def get_rules(self) -> Dict[str, Dict[str, Union[Dict[str, int], Dict[str, str]]]]:
        """Получить все правила."""
        return self.data.get('rules', {})

    def get_rule(self, rule_id: str) -> Dict:
        """Получить правило по идентификатору."""
        if rule_id in self.data['rules']:
            return self.data['rules'][rule_id]
        raise KeyError(f"Rule with ID {rule_id} does not exist.")

    def add_rule(self, rule_id: str, rule: Dict[str, Union[Dict[str, int], Dict[str, str]]]) -> None:
        """Добавить правило."""
        self.data['rules'][rule_id] = rule

    def add_blank_rule(self) -> None:
        """Добавить пустое правило с уникальным идентификатором."""
        rule_id = str(max(map(int, self.data['rules'].keys()), default=0) + 1)
        self.data['rules'][rule_id] = {"if": {}, "then": {self.action_key: None}}

    def delete_rule(self, rule_id: str) -> bool:
        """Удалить правило по его идентификатору."""
        return self.data['rules'].pop(rule_id, None) is not None

    def edit_rule(self, rule_id: str, new_rule: Dict) -> None:
        """Изменить правило."""
        if rule_id in self.data['rules']:
            self.data['rules'][rule_id] = new_rule
        else:
            raise KeyError(f"Rule with ID {rule_id} does not exist.")

    def move_rule_up(self, ind):
        keys = list(self.get_rules().keys())
        current_idx = keys.index(ind)
        if current_idx > 0:
            swap_ind = keys[current_idx - 1]
            self._swap_rules(ind, swap_ind)

    def move_rule_down(self, ind):
        keys = list(self.get_rules().keys())
        current_idx = keys.index(ind)
        if current_idx < len(keys) - 1:
            swap_ind = keys[current_idx + 1]
            self._swap_rules(ind, swap_ind)

    def _swap_rules(self, ind1, ind2):
        rule1 = self.get_rule(ind1).copy()
        rule2 = self.get_rule(ind2).copy()
        self.edit_rule(ind1, rule2)
        self.edit_rule(ind2, rule1)


    def set_then(self, rule_id: str, fact: str, val: int) -> None:
        """Установить действие (then) для правила."""
        if fact not in self.get_facts():
            self.add_fact(fact, None)
        self.data['rules'][rule_id]['then'] = {fact: val}

    # --- Управление условиями ---

    def add_condition(self, rule_id: str, fact: str, val: int) -> None:
        """Добавить условие в правило."""
        if fact not in self.get_facts():
            self.add_fact(fact, None)
        self.data['rules'][rule_id]['if'][fact] = val

    def delete_condition(self, rule_id: str, condition: str) -> None:
        """Удалить условие из правила."""
        self.data['rules'][rule_id]['if'].pop(condition, None)

    def delete_all_conditions(self, rule_id: str) -> None:
        """Удалить все условия из правила."""
        self.data['rules'][rule_id]['if'].clear()

    # --- Утилиты ---

    def copy(self) -> "RulesFactsManager":
        """Создать глубокую копию объекта."""
        new_instance = RulesFactsManager(file_name=self.file_name, action_key=self.action_key)
        new_instance.data = copy.deepcopy(self.data)
        return new_instance

    def _sync_facts_with_rules(self) -> None:
        """Добавить отсутствующие факты из правил."""
        for rule in self.get_rules().values():
            # Проверить условия (if)
            for fact in rule.get("if", {}).keys():
                if fact not in self._facts:
                    self._facts[fact] = None

            # Проверить действия (then)
            for fact in rule.get("then", {}).keys():
                if fact not in self._facts:
                    self._facts[fact] = None

    def check(self) -> None:
        """Проверить, что все ключи и значения корректны."""
        for rule_id, rule in self.get_rules().items():
            for fact in rule.get("if", {}).keys():
                if not isinstance(fact, str):
                    raise ValueError(f"Invalid fact key in rule {rule_id}: {fact}")
            for fact in rule.get("then", {}).keys():
                if not isinstance(fact, str):
                    raise ValueError(f"Invalid fact key in rule {rule_id}: {fact}")
