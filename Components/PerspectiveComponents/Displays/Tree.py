from typing import List, Optional, Tuple, Union

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent, ComponentPiece
from Components.PerspectiveComponents.Common.Tree import CommonTree


class Tree(CommonTree, BasicPerspectiveComponent):
    """A Perspective Tree Component."""

    def __init__(
            self,
            locator: Tuple[Union[By, str], str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 3,
            description: Optional[str] = None,
            poll_freq: float = 0.5,
            raise_exception_for_overlay: bool = False):
        CommonTree.__init__(
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
        self._items_by_path = {}

    def right_click(self, wait_after_click: float = 0) -> None:
        """
        Right-click the Tree. As individual items do not allow for their own events, this click will always target the
        0th top-level item (if one exists).
        """
        try:
            ComponentPiece(
                locator=(By.CSS_SELECTOR, f'div[data-item-path="0"]'),
                driver=self.driver,
                parent_locator_list=self.locator_list,
                timeout=1,
                poll_freq=self.poll_freq).right_click(wait_after_click=wait_after_click)
        except TimeoutException:
            super().right_click()
