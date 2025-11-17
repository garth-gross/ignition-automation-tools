from typing import List, Optional, Tuple, Union

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import ComponentPiece
from Components.Common.Icon import CommonIcon
from Components.PerspectiveComponents.Common.ComponentModal import ComponentModal
from Components.PerspectiveComponents.Inputs.Button import Button


class OneShotButton(Button):
    """A Perspective One-Shot Button Component"""
    _CANCEL_BUTTON_LOCATOR = (By.CSS_SELECTOR, 'button[data-button-type="cancel"]')
    _CONFIRM_BUTTON_LOCATOR = (By.CSS_SELECTOR, 'button[data-button-type="confirm"]')
    _MODAL_MESSAGE_LOCATOR = (By.CSS_SELECTOR, "div.ia_oneShotButtonComponent__confirmModal__message")
    _ICON_LOCATOR = (By.TAG_NAME, "svg")

    def __init__(
            self,
            locator: Tuple[Union[By, str], str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 3,
            description: Optional[str] = None,
            poll_freq: float = 0.5,
            raise_exception_for_overlay: bool = False):
        super().__init__(
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description,
            poll_freq=poll_freq,
            raise_exception_for_overlay=raise_exception_for_overlay)
        self._modal = ComponentModal(driver=driver, poll_freq=poll_freq)
        self._cancel_button = Button(
            locator=self._CANCEL_BUTTON_LOCATOR,
            driver=driver,
            parent_locator_list=self._modal.locator_list,
            poll_freq=poll_freq)
        self._confirm_button = Button(
            locator=self._CONFIRM_BUTTON_LOCATOR,
            driver=driver,
            parent_locator_list=self._modal.locator_list,
            poll_freq=poll_freq)
        self._modal_message = ComponentPiece(
            locator=self._MODAL_MESSAGE_LOCATOR,
            driver=driver,
            parent_locator_list=self._modal.locator_list,
            poll_freq=poll_freq)
        self._local_icon = CommonIcon(
            locator=self._ICON_LOCATOR,
            driver=driver,
            parent_locator_list=self.locator_list,
            poll_freq=poll_freq)

    def click_cancel_in_modal(self) -> None:
        """
        Click the Cancel button, available when confirmation is enabled.

        :raises TimeoutException: If the Cancel button is not present.
        """
        self._cancel_button.click()

    def click_confirm_in_modal(self) -> None:
        """
        Click the Confirm button, available when confirmation is enabled.

        :raises TimeoutException: If the Confirm button is not present.
        """
        self._confirm_button.click()

    def confirmation_modal_is_displayed(self) -> bool:
        """
        Determine if the confirmation modal is currently displayed.

        :returns: True, if the confirmation modal is present - False otherwise.
        """
        try:
            return self._modal.find(timeout=0.5) is not None and self._confirm_button.find(0.5) is not None
        except TimeoutException:
            return False
