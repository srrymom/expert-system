def rule_to_text(rule):
    """Преобразование правила в текстовый формат."""
    conditions = " и ".join([f"{key} == {value}" for key, value in rule["if"].items()])
    actions = " и ".join([f"{key} = {value}" for key, value in rule["then"].items()])

    return f"ЕСЛИ ({conditions}) ТО {actions}"


