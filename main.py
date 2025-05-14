from nicegui import ui

from consultant import ConsultantUI
from pages import main_page, rules_page, facts_page
from rule_page import RulePage


@ui.page('/')   
def main_page_view():
    main_page()


@ui.page('/cons')
def cons_page_view():
    cons = ConsultantUI()
    cons.cons_page()


@ui.page('/facts')
def facts_view():
    facts_page()


@ui.page('/rules')
def rules_page_view():
    rules_page()


@ui.page('/rule/{rule_index}')
def edit_page_view(rule_index):
    rule_page = RulePage(rule_index)

    rule_page.edit_page()


ui.run(native=True)
