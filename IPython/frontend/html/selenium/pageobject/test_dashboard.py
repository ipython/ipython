from driver import driver, wait, keys
d = driver()

from dashboard import Dashboard
from . import find

def test_basic():
    db = Dashboard()
    assert 'IPython Dashboard' in d.title

def test_create_notebook():
    db = Dashboard()

    # Click new notebook button
    find('dashboard.new_notebook').click()
    d.switch_to_window(d.window_handles[-1])

    # Click on the notebook name to rename it
    find('dashboard.notebook_name').click()

    # Wait for the popup dialog
    wait(lambda d: d.find_element_by_class_name('ui-dialog-titlebar-close'))

    # Type in the new name
    name_input = d.find_element_by_tag_name('input')
    name_input.clear()
    name_input.send_keys('Test Notebook')

    # Click OK
    old_name = find('notebook.name').text
    buttons = d.find_elements_by_class_name('ui-button')

    OK_button = [b for b in buttons if b.text == 'OK']
    OK_button[0].click()

    # Wait until save is done
    wait(lambda d: old_name != find('notebook.name').text)

#    find('notebook').send_keys(keys.CONTROL + 'm', 's')
