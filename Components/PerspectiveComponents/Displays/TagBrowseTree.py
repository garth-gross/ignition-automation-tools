from typing import List, Optional, Tuple, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import BasicPerspectiveComponent
from Components.PerspectiveComponents.Common.TagBrowseTree import CommonTagBrowseTree
from Components.PerspectiveComponents.Common.Tree import Item
from Helpers.Ignition.Tag import Tag, Folder


class TagBrowseTree(CommonTagBrowseTree, BasicPerspectiveComponent):
    """A Perspective Tag Browse Tree Component."""

    def __init__(
            self,
            locator: Tuple[Union[By, str], str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 3,
            description: Optional[str] = None,
            poll_freq: float = 0.5,
            raise_exception_for_overlay: bool = False):
        CommonTagBrowseTree.__init__(
            self,
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            description=description,
            poll_freq=poll_freq)
        BasicPerspectiveComponent.__init__(
            self,
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            poll_freq=poll_freq,
            raise_exception_for_overlay=raise_exception_for_overlay)

    def multi_select(
            self, items: List[Item], inclusive_multi_selection: bool = True, timeout: float = 5) -> None:
        """
        Unused. Tag Browse Trees should enforce that Tags are being selected. This is especially important due to the
        special handling within their extended use in Power Charts.
        """
        raise NotImplementedError(f"Use {self.multi_select_tags.__name__} instead.")

    def multi_select_tags(
            self, tags: List[Union[Tag, Folder]], inclusive_multi_selection: bool, timeout: int = 5) -> None:
        """
        Select multiple Tags (or Folders) within the Tag Browse Tree.

        :param tags: A list of Tags or Folders to be selected.
        :param inclusive_multi_selection: A True value specifies that all Tags between the supplied Tags should also be
            selected, and so SHIFT will be held. A False value specifies that ONLY the supplied Tags should be selected,
            and so CONTROL will be held.
        :param timeout: The amount of time to potentially wait (in seconds) for each Tag to become visible.

        :raises TimeoutException: If any of the supplied Tags did not exist.
        """
        super().multi_select(
            items=[self._item_from_tag(tag=tag) for tag in tags],
            inclusive_multi_selection=inclusive_multi_selection,
            timeout=timeout)

    def select_item(self, item: Item, timeout: int = 5, wait_after_click: int = 1) -> None:
        """
        Unused. Tag Browse Trees should enforce that Tags are being selected. This is especially important due to the
        special handling within their extended use in Power Charts.
        """
        raise NotImplementedError(f"Use {self.select_tag.__name__} instead")

    def select_tag(self, tag: Union[Tag, Folder], timeout: int = 5) -> None:
        """
        Select a Tag or Folder from the Tag Browse Tree.

        :param tag: The Tag or Folder to select.
        :param timeout: The amount of time (in seconds) to potentially wait for the supplied Tag to appear.

        :raises TimeoutException: If no such Tag exists.
        """
        super().select_item(item=self._item_from_tag(tag=tag), timeout=timeout)

    @staticmethod
    def _item_from_tag(tag: Union[Tag, Folder]) -> Item:
        # we don't want the provider.
        pieces = tag.get_full_path().split(tag.get_provider())[1].split("/")
        item = Item(label_text=pieces.pop(0))
        while len(pieces) > 0:
            piece = pieces.pop()
            if len(piece) > 0:
                item = Item(label_text=piece, parent=item)
        return item
