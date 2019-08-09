import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from functional_tests.fixtures import *  # noqa
from .utils import go_to_account, login, logout


def create_category():
    pass


def create_discipline():
    pass


# def create_assignment(browser, category, discipline):
#     # Teacher can create an assignment
#     browser.get(live_server_url + reverse("teacher", kwargs={"pk": 1}))
#     browser.find_element_by_id("assignment-section").click()
#     browser.find_element_by_link_text("Manage assignments").click()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#             (By.XPATH, "//h2[contains(text(), 'Create a new assignment')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     inputbox = browser.find_element_by_id("id_identifier")
#     inputbox.send_keys("new-unique-assignment-identifier")
#
#     inputbox = browser.find_element_by_id("id_title")
#     inputbox.send_keys("New assignment title")
#
#     inputbox.submit()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (
#                     By.XPATH,
#                     "//*[contains(text(), "
#                     "'new-unique-assignment-identifier')]",
#                 )
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     assert (
#         Assignment.objects.filter(
#             identifier="new-unique-assignment-identifier"
#         ).count()
#         == 1
#     )
#
#     # Teacher can edit an assignment
#
#     # Teacher can create a blink assignment
#
#     # Teacher can delete a blink assignment
#
#     # Teacher can edit a blink assignment
#
#     # Access account from link in top right corner
#
#     # Teacher cannot access other teacher accounts
#     browser.get(live_server_url + reverse("teacher", kwargs={"pk": 2}))
#     assert "Forbidden" in browser.page_source
#
#     # Teacher declines TOS
#
#     # Checkout what answer choice form looks like if student answers
#
#     # Teacher cannot delete any questions
#
#     # Need a test to assert reset question never appears in LTI
#
#     # Teacher clones: check new and old question states including
#     # answer_choices
#
#
# def edit_question(browser):
#     # Teacher can edit their questions
#     try:
#         WebDriverWait(browser, timeout).until(
#             element_to_be_clickable((By.ID, "question-section"))
#         ).click()
#     except TimeoutException:
#         assert False
#     question = Question.objects.get(title="Test title")
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             element_to_be_clickable(
#                 (By.ID, "edit-question-{}".format(question.id))
#             )
#         ).click()
#     except TimeoutException:
#         assert False
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (By.XPATH, "//h2[contains(text(), 'Step 1')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     assert "Step 1" in browser.find_element_by_tag_name("h2").text
#
#     tinymce_embed = browser.find_element_by_tag_name("iframe")
#     browser.switch_to.frame(tinymce_embed)
#     ifrinputbox = browser.find_element_by_id("tinymce")
#     ifrinputbox.send_keys("Edited: ")
#     browser.switch_to.default_content()
#
#     inputbox = browser.find_element_by_id("id_title")
#     inputbox.submit()
#
#     try:
#         WebDriverWait(browser, timeout).until(
#             presence_of_element_located(
#                 (By.XPATH, "//h2[contains(text(), 'Step 2')]")
#             )
#         )
#     except TimeoutException:
#         assert False
#
#     question.refresh_from_db()
#
#     assert "Edited: Test text" in question.text
#
#     # Teacher cannot edit another teacher's questions
#     browser.get(
#         live_server_url + reverse("question-update", kwargs={"pk": 43})
#     )
#     assert "Forbidden" in browser.page_source


def create_PI_question(browser, assert_, category, discipline):
    # Teacher can create a question
    browser.find_element_by_id("question-section").click()
    browser.find_element_by_link_text("Create new").click()

    browser.wait_for(
        assert_("Question" in browser.find_element_by_tag_name("h1").text)
    )

    assert "Step 1" in browser.find_element_by_tag_name("h2").text

    inputbox = browser.find_element_by_id("id_title")
    inputbox.send_keys("Test title")

    tinymce_embed = browser.find_element_by_tag_name("iframe")
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys("Test text")
    browser.switch_to.default_content()

    Select(browser.find_element_by_id("id_discipline")).select_by_value("1")

    input_category = browser.find_element_by_id("autofill_categories")
    input_category.send_keys(category.title)
    time.sleep(1)
    input_category.send_keys(Keys.ENTER)

    browser.find_element_by_id("question-create-form").submit()

    browser.wait_for(
        assert_("Step 2" in browser.find_element_by_tag_name("h2").text)
    )

    tinymce_embed = browser.find_element_by_id(
        "id_answerchoice_set-0-text_ifr"
    )
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys("Answer 1")
    browser.switch_to.default_content()

    tinymce_embed = browser.find_element_by_id(
        "id_answerchoice_set-1-text_ifr"
    )
    browser.switch_to.frame(tinymce_embed)
    ifrinputbox = browser.find_element_by_id("tinymce")
    ifrinputbox.send_keys("Answer 2")
    browser.switch_to.default_content()

    browser.find_element_by_id("id_answerchoice_set-0-correct").click()

    inputbox = browser.find_element_by_id("answer-choice-form")

    inputbox.submit()

    browser.wait_for(
        assert_("Step 3" in browser.find_element_by_tag_name("h2").text)
    )

    browser.find_element_by_id("add_question_to_assignment").submit()

    browser.wait_for(
        assert_("My Account" in browser.find_element_by_tag_name("h2").text)
    )

    assert "Test title" in browser.page_source


def test_create_question(browser, assert_, category, discipline, teacher):
    login(browser, teacher)
    go_to_account(browser)
    create_PI_question(browser, assert_, category, discipline)
    # edit_PI_question
    logout(browser, assert_)
