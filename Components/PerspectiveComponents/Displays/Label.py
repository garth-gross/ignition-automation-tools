from typing import Optional, List, Tuple, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent


class Label(BasicPerspectiveComponent):
    """A Perspective Label Component."""

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
