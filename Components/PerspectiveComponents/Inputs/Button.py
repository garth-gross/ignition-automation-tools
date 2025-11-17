from typing import Tuple, List, Optional, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent
from Components.Common.Button import CommonButton


class Button(CommonButton, BasicPerspectiveComponent):
    """A Perspective Button Component."""

    def __init__(
            self,
            locator: Tuple[Union[By, str], str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 3,
            description: Optional[str] = None,
            poll_freq: float = 0.5,
            raise_exception_for_overlay: bool = False):
        CommonButton.__init__(
            self,
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description,
            poll_freq=poll_freq)
        BasicPerspectiveComponent.__init__(
            self,
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description,
            poll_freq=poll_freq,
            raise_exception_for_overlay=raise_exception_for_overlay)
