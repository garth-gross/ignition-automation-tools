from typing import Optional, List, Tuple, Union

from selenium.common import ElementNotInteractableException, NoSuchElementException, \
    TimeoutException, ElementClickInterceptedException, JavascriptException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent, ComponentPiece
from Components.Common.Button import CommonButton
from Components.Common.Dropdown import CommonDropdown
from Components.Common.TextInput import CommonTextInput
from Helpers.IAAssert import IAAssert
from Helpers.Point import Point


class FormComponent(BasicPerspectiveComponent):
    """
    A Perspective Form Component.
    """
    _FORM_CANCEL_ACTION_BUTTON_LOCATOR = (By.CSS_SELECTOR, ".ia_form__button--cancel")
    _FORM_SUBMIT_ACTION_BUTTON_LOCATOR = (By.CSS_SELECTOR, ".ia_form__button--submit")
    _FORM_NOTIFICATION_LOCATOR = (By.CSS_SELECTOR, ".ia_form__notifications")

    def __init__(
            self,
            driver: WebDriver,
            locator: Tuple[Union[By, str], str] = None,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None):
        BasicPerspectiveComponent.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list)
        self._cancel_action_button = CommonButton(
            locator=self._FORM_CANCEL_ACTION_BUTTON_LOCATOR,
            driver=self.driver,
            parent_locator_list=self.locator_list)
        self._submit_action_button = CommonButton(
            locator=self._FORM_SUBMIT_ACTION_BUTTON_LOCATOR,
            driver=self.driver,
            parent_locator_list=self.locator_list)
        self._form_notification = ComponentPiece(
            locator=self._FORM_NOTIFICATION_LOCATOR,
            driver=driver,
            description="The form inline notification that displays at the bottom of the form when awaitResponse is "
                        "set to true.",
            timeout=0)

    def click_cancel_action_button(
            self, timeout: Optional[Union[int, float]] = None, wait_after_click: float = 0) -> None:
        """
        Click the cancel action button.

        :param timeout: Poll the DOM up to this amount of time before potentially throwing a TimeoutException.
            Overrides the default of the component.
        :param wait_after_click: The amount of time to wait after the click event occurs before continuing.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        self._cancel_action_button.click(timeout=timeout, wait_after_click=wait_after_click)

    def click_submit_action_button(
            self, timeout: Optional[Union[int, float]] = None, wait_after_click: float = 0) -> None:
        """
        Click the submit action button.

        :param timeout: Poll the DOM up to this amount of time before potentially throwing a TimeoutException.
            Overrides the default of the component.
        :param wait_after_click: The amount of time to wait after the click event occurs before continuing.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        self._submit_action_button.click(timeout=timeout, wait_after_click=wait_after_click)

    def cancel_action_button_is_displayed(self) -> bool:
        """
        Checks if the cancel action button is displayed.
        This function returns a boolean indicating whether the cancel button is visible to the user on the form.
        :return: True if the cancel action button is displayed, False otherwise.
        """
        return self._cancel_action_button.is_displayed()

    def cancel_action_button_is_enabled(self) -> bool:
        """
        Checks if the form cancel action button is enabled.
        This function returns a boolean indicating whether the cancel button is enabled and clickable by the user.
        return: True if the cancel action button is enabled, False otherwise.
        """
        return self._cancel_action_button.is_enabled()

    def get_cancel_action_button_origin(self) -> Point:
        """
        Get the Cartesian Coordinate of the upper-left corner of the cancel button, measured from the top-left of the
        viewport.

        :returns: The Cartesian Coordinate of the upper-left corner of the cancel button, measured from the top-left
        of the viewport.
        """
        return self._cancel_action_button.get_origin()

    def get_submit_action_button_origin(self) -> Point:
        """
        Get the Cartesian Coordinate of the upper-left corner of the submit button, measured from the top-left of the
        viewport.

        :returns: The Cartesian Coordinate of the upper-left corner of the submit button, measured from the top-left
        of the viewport.
        """
        return self._submit_action_button.get_origin()

    def get_cancel_action_button_text(self) -> str:
        """
        Retrieves the text from the cancel action button.
        This method locates the cancel action button on the interface and returns the text displayed on it. Raises an
        exception if the element is not found.

        Returns:
            str: The text context of the cancel action button.

        Raises:
            NoSuchElementException: If the cancel action button is not found.
        """
        button_text = self._cancel_action_button.find().text
        if not button_text:  # If text is empty or none
            raise NoSuchElementException("Cancel action button not found on the page.")
        return button_text

    def get_origin_of_cancel_action_button(self) -> Point:
        """
        Get the Cartesian Coordinate of the upper-left corner of the cancel action button, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the upper-left corner of the cancel action button, measured from the
        top-left of the viewport.
        """
        return self._cancel_action_button.get_origin()

    def get_origin_of_submit_action_button(self) -> Point:
        """
        Get the Cartesian Coordinate of the upper-left corner of the submit action button, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the upper-left corner of the submit action button, measured from the
        top-left of the viewport.
        """
        return self._submit_action_button.get_origin()

    def get_submit_action_button_text(self) -> str:
        """
        Retrieves the text from the submit action button.
        This method locates the submit action button on the interface and returns the text displayed on it. Raises an
        exception if the element is not found.

        Returns:
            str: The text context of the submit action button.

        Raises:
            NoSuchElementException: If the submit action button is not found.
        """
        button_text = self._submit_action_button.find().text
        if not button_text:  # If text is empty or none
            raise NoSuchElementException("Submit action button not found on the page.")
        return button_text

    def get_termination_of_cancel_action_button(self) -> Point:
        """
        Get the Cartesian Coordinate of the bottom-right corner of the cancel action button, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the bottom-right corner of the cancel action button, measured from the
        top-left of the viewport.
        """
        return self._cancel_action_button.get_termination()

    def get_termination_of_submit_action_button(self) -> Point:
        """
        Get the Cartesian Coordinate of the bottom-right corner of the submit action button, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the bottom-right corner of the submit action button, measured from the
        top-left of the viewport.
        """
        return self._submit_action_button.get_termination()

    def form_notification_is_displayed(self) -> bool:
        """
        Determine whether the form inline notification is currently visible.

        :returns: True if the notification is visible, False otherwise.
        """
        try:
            return self._form_notification.is_displayed()
        except TimeoutException:
            return False

    def submit_action_button_is_displayed(self) -> bool:
        """
        Checks if the form submit action button is displayed.
        This function returns a boolean indicating whether the submit button is visible to the user on the form.
        :return: True if the submit action button is displayed, False otherwise.
        """
        return self._submit_action_button.is_displayed()

    def submit_action_button_is_enabled(self) -> bool:
        """
        Checks if the form submit action button is enabled.
        This function returns a boolean indicating whether the submit button is enabled and clickable by the user.
        return: True if the submit action button is enabled, False otherwise.
        """
        return self._submit_action_button.is_enabled()


class _FormWidget(ComponentPiece):
    """
    A generic class intended to be inherited from by any sort of Perspective Form widget. When using widgets,
    it is highly recommended to add a `domId` property to the `widget` object.
    """
    _FORM_VALIDATION_ERROR_LOCATOR = (By.CSS_SELECTOR, ".ia_form__error")

    def __init__(
            self,
            driver: WebDriver,
            locator: Tuple[Union[By, str], str],
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 10,
            description: Optional[str] = None):
        ComponentPiece.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description)
        self._validation_message = ComponentPiece(
            driver=driver,
            locator=self._FORM_VALIDATION_ERROR_LOCATOR,
            parent_locator_list=self.locator_list,
            description="The validation message for a widget.")

    def get_widget_validation_message(self) -> str:
        """
        Retrieves the widget validation message displayed on the form.

        :raises TimeoutException: If the validation message is not displayed.

        :return: The text content of the validation message element.
        """
        return self._validation_message.get_text()

    def validation_warning_is_displayed(self) -> bool:
        """
        Determine whether the widget validation warning is currently visible.

        :returns: True if the validation warning is visible, False otherwise.
        """
        return self._validation_message.is_displayed()


class _FormInputWidget(_FormWidget):
    """
    A generic class intended to be inherited from by any sort of Perspective Form input widget. When using widgets,
    it is highly recommended to add a `domId` property to the `widget` object.
    """
    _FORM_INPUT_FIELD_LOCATOR = (By.CSS_SELECTOR, ".ia_form__controlBody>:first-child")

    def __init__(
            self,
            driver: WebDriver,
            locator: Tuple[Union[By, str], str],
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 10,
            description: Optional[str] = None):
        _FormWidget.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description)
        self._input_field = CommonTextInput(
            driver=driver,
            locator=self._FORM_INPUT_FIELD_LOCATOR,
            parent_locator_list=self.locator_list,
            timeout=timeout)

    def can_receive_focus(self) -> bool:
        """
        Determine if the input field can receive focus.

        :returns: True if the input field can receive focus, False otherwise.
        """
        try:
            element = self._input_field.find()
            self.driver.execute_script("arguments[0].focus();", element)
            return self.driver.execute_script(
                "return document.activeElement === arguments[0];", element)
        except JavascriptException:
            return False

    def is_enabled(self) -> bool:
        """
        Determine if the input field is enabled.

        :returns: True if the input field is enabled, False otherwise.
        """
        return self._input_field.find().get_attribute(name="disabled") is None

    def is_read_only(self) -> bool:
        """
        Determine if the input field is read-only.

        :returns: True if the input field is read-only, False otherwise.
        """
        return self._input_field.find().get_attribute(name="readonly") is not None

    def _set_text(
            self,
            text: str,
            release_focus: bool = True,
            wait_after: float = 0) -> None:
        """
        Set the text of the input field for the widget.

        :param text: The text you would like to apply.
        :param release_focus: dictates whether a `blur()` event is invoked for the component after typing the supplied
            text. Default is True.
        :param wait_after: How long to wait after supplying the provided text and applying the potential `blur()` event.

        :raises AssertionError: If the text was not set to the supplied value.
        :raises ElementNotInteractableException: If the input field is read-only.
        """
        if self._input_field.find().get_attribute(name="readonly"):
            raise ElementNotInteractableException(f"The input field is read-only.")

        text = str(text)
        # strip special characters (ESC, ENTER) while leaving spaces and punctuation
        expected_text = text.encode("ascii", "ignore").decode()
        if text is None or text == '':
            text = ' ' + Keys.BACKSPACE

        try:
            self._input_field.click()
        except ElementClickInterceptedException:
            # Handle overlay interference
            ActionChains(driver=self.driver) \
                .move_to_element_with_offset(to_element=self._input_field.find(), xoffset=5, yoffset=5) \
                .click() \
                .perform()

        current_text = self._input_field.find().get_attribute('value')  # Get current text without waiting
        keys_to_send = ''.join([Keys.ARROW_RIGHT for _ in current_text] +
                               [Keys.BACKSPACE for _ in current_text] +
                               [text])

        self._input_field.find().send_keys(keys_to_send)
        if release_focus:
            self._input_field.release_focus()
        # Verify the text is set correctly
        IAAssert.is_equal_to(
            actual_value=self._input_field.find().get_attribute('value'),
            expected_value=expected_text,
            failure_msg=f"Failed to set the text for this widget.")
        self.wait_some_time(time_to_wait=wait_after)


class NumberWidget(_FormInputWidget):
    """
    A Perspective Form `number` widget. When using widgets, it is highly recommended to add a `domId` property to
    the `widget` object.
    """
    def __init__(self,
                 driver: WebDriver,
                 locator: Tuple[Union[By, str], str],
                 parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
                 timeout: float = 10):
        _FormInputWidget.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list,
            timeout=timeout)

    def get_text(self) -> str:
        return self._input_field.get_text()

    def set_text(self, text: Union[float, str], release_focus: bool = True, wait_after: float = 0) -> None:
        _FormInputWidget._set_text(self, text=str(text), release_focus=release_focus, wait_after=wait_after)


class TextWidget(_FormInputWidget):
    """
    A Perspective Form `text` widget. When using widgets, it is highly recommended to add a `domId` property to
    the `widget` object.
    """
    def __init__(self,
                 driver: WebDriver,
                 locator: Tuple[Union[By, str], str],
                 parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
                 timeout: float = 10):
        _FormInputWidget.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list,
            timeout=timeout)

    def get_text(self) -> str:
        return self._input_field.get_text()

    def get_placeholder_text(self) -> str:
        return self._input_field.get_placeholder_text()

    def set_text(self, text: str, release_focus: bool = True, wait_after: float = 0) -> None:
        _FormInputWidget._set_text(self, text=text, release_focus=release_focus, wait_after=wait_after)


class TextAreaWidget(_FormInputWidget):
    """
    A Perspective Form `text-area` widget. When using widgets, it is highly recommended to add a `domId` property to
    the `widget` object.
    """
    def __init__(self,
                 driver: WebDriver,
                 locator: Tuple[Union[By, str], str],
                 parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
                 timeout: float = 10):
        _FormInputWidget.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list,
            timeout=timeout)

    def get_text(self) -> str:
        return self._input_field.get_text()

    def set_text(self, text: str, release_focus: bool = True, wait_after: float = 0) -> None:
        _FormInputWidget._set_text(self,  text=text, release_focus=release_focus, wait_after=wait_after)


class DropdownWidget(_FormWidget):
    """
    A Perspective Form `dropdown` widget. When using widgets, it is highly recommended to add a `domId` property to
    the `widget` object.
    """
    # does not use _FormInputWidget because the "input" field for Dropdowns is not an <input> element.
    def __init__(self,
                 driver: WebDriver,
                 locator: Tuple[Union[By, str], str],
                 parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
                 timeout: float = 10):
        _FormWidget.__init__(
            self,
            driver=driver,
            locator=locator,
            parent_locator_list=parent_locator_list)
        self._dropdown = CommonDropdown(
            driver=driver,
            locator=(By.CSS_SELECTOR, ".ia_form__controlBody>:first-child"),  # we still want the first child
            parent_locator_list=self.locator_list,
            timeout=timeout)

    def get_selected_options(self) -> list[str]:
        return self._dropdown.get_selected_options_as_list()

    def get_text(self) -> str:
        return self._dropdown.get_text()

    def select_option_by_text_if_not_selected(self, option_text: str) -> None:
        self._dropdown.select_option_by_text_if_not_selected(option_text=option_text)
