from typing import List, Optional, Tuple, Union

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent, ComponentPiece


class BarcodeScanner(BasicPerspectiveComponent):
    """A Perspective Barcode Scanner Component."""
    _LABEL_LOCATOR = (By.CSS_SELECTOR, 'li')

    def __init__(
            self,
            locator: Tuple[Union[By, str], str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 2,
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
        self._label = ComponentPiece(locator=self._LABEL_LOCATOR, driver=driver, timeout=1, poll_freq=poll_freq)

    def is_displaying_value(self) -> bool:
        """
        Determine if the component is displaying any value.

        :returns: True, if any text content is displayed by the component - False otherwise.
        """
        try:
            return self._label.find().is_displayed() and (len(self._label.get_text()) > 0)
        except TimeoutException:
            return False

    def get_text(self, **kwargs) -> Optional[str]:
        """
        Retrieve text content that is displaying in the component.

        :returns: The text content that is displayed by the component. If no text is displayed by the component, it
            will return a 'None'.
        """
        try:
            return self._label.get_text()
        except TimeoutException:
            return None
