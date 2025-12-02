import sys
import time
from typing import List, Optional, Tuple, Self, Union

from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from Components.BasicComponent import ComponentPiece
from Components.Common.Icon import CommonIcon

_ITEM_CLASS = "tree-item"
_TREE_ITEM_LOCATOR = (By.CSS_SELECTOR, f".{_ITEM_CLASS}")


class Item:
    _locator = None
    _ancestry = None
    _path = None
    """
    Items are understood to be the individual line items within a Perspective Tree component. They are most helpful
    when their parent (and the parent of their parent, and so on) is also supplied. On the back-end, we build a
    locator for the Item based off of its derived ancestry.
    If failing to use or locate an Item, make sure you are supplying the EXACT ancestry, and that each ancestor is
    expanded.
    """

    def __init__(self, label_text: str, parent: Optional[Self] = None, zero_indexed_path: Optional[str] = None):
        self.label = label_text
        self.parent = parent
        self.index_path = zero_indexed_path
        self._build_ancestry()  # ancestry must be derived first because both the locator and path are dependent
        self._build_locator()
        self._build_path()

    def get_ancestry(self) -> List[Self]:
        """
        Obtain a list of Items, where each Item in the list describes the ancestry chain of the Item.

        Example: Consider an Item with label text of "Child", and a parent with label text of "Parent". The "Parent"
            item also has a parent with label text of "Grandparent". The returned text of the Items in the returned
            list would be ["Grandparent", "Parent", "Child"].

        :return: A list of Items, with the last item in the list being the direct parent of this Item
        """
        return self._ancestry

    def get_locator(self) -> Tuple[Union[By, str], str]:
        """
        Obtain the locator which describes this exact Item in the Tree based on its derived ancestry.

        :return: A tuple where the 0th item is a By locator type and the 1th item is a CSS string.
        """
        return self._locator

    def get_path(self) -> str:
        """
        Obtain the label text path which describes the route used to locate this Item. Not to be confused with
        index_path, which is derived within Perspective and which represents the location of Items based on a numeric
        index. Primarily used for troubleshooting.

        :return: A slash-delimited string where each slash separates the label text of an item and its parent.
        """
        return self._path

    def _build_ancestry(self) -> None:
        ancestry = []
        _parent = self.parent
        while _parent is not None and len(_parent.label) > 0:
            ancestry.insert(0, _parent)
            _parent = _parent.parent
        self._ancestry = ancestry

    def _build_locator(self) -> None:
        path_pieces = [item.label for item in self.get_ancestry()]
        path_pieces.append(self.label)
        # all pieces of path get a parent-node
        ancestry_css_pieces = [
            f'[class*="-node"][data-label="{item_label}"]' for item_label in path_pieces]
        # and now the last entry should be the tree item
        terminal_css_piece = f'{_TREE_ITEM_LOCATOR[1]}[data-label="{path_pieces[-1]}"]'
        self._locator = By.CSS_SELECTOR, " ".join(ancestry_css_pieces + [terminal_css_piece])

    def _build_path(self) -> None:
        self._path = "/".join([item.label for item in self.get_ancestry()] + [self.label])

    def __str__(self):
        return self._path


class CommonTree(ComponentPiece):
    """
    A Tree of items, as is found as part of the Tree Component, the Tag Browse Tree, and the Power Chart.

    Prior to 8.1.39, Selenium was unable to discern Tree items which shared names. We allowed for interacting with 
    items by their label name, but if two displayed items in the tree had a label of "X", Selenium would always 
    interact with the highest item. 
    
    In 8.1.39, a new locator was added which allowed for a much better location strategy within the component. 
    Functions which previously accepted labels for interaction now require an Item object. Items behave as something 
    approaching a linked list, where an Item knows about its parent, and that parent knows about its own parent. This
    allows for us to build a highly specific locator at runtime.
    """
    _EXPANDED_ICON_CLASS = "ia_treeComponent__expandIcon--expanded"
    _FOLDER_EXPAND_ICON_LOCATOR = (
        By.CSS_SELECTOR, 'svg.expand-icon.ia_treeComponent__expandIcon')
    _LABEL_LOCATOR = (
        By.CSS_SELECTOR, 'div.label-wrapper-text')
    _TOP_LEVEL_ITEMS_LOCATOR = (By.CSS_SELECTOR, 'div.tree>div>div>div.tree-row')

    def __init__(
            self,
            driver: WebDriver,
            locator: Tuple[Union[By, str], str],
            parent_locator_list: Optional[List] = None,
            timeout: float = 3,
            description: Optional[str] = None,
            poll_freq: float = 0.5):
        super().__init__(
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description,
            poll_freq=poll_freq)
        self._folder_icons = ComponentPiece(
            locator=self._FOLDER_EXPAND_ICON_LOCATOR,
            driver=self.driver,
            parent_locator_list=self.locator_list,
            poll_freq=poll_freq)
        self._expanded_folders = ComponentPiece(
            locator=(By.CSS_SELECTOR, f'div[class*="expanded"] div.text-scroll'),
            driver=self.driver,
            parent_locator_list=self.locator_list,
            poll_freq=poll_freq)
        self._top_level_items = ComponentPiece(
            locator=self._TOP_LEVEL_ITEMS_LOCATOR,
            driver=driver,
            parent_locator_list=self.locator_list,
            poll_freq=poll_freq)
        self._tree_items = ComponentPiece(
            locator=_TREE_ITEM_LOCATOR,
            driver=self.driver,
            parent_locator_list=self.locator_list,
            poll_freq=poll_freq)
        self._items = {}
        self._item_icons = {}
        self._expand_collapse_icons = {}
        self._labels = {}

    def click_expansion_icon(self, item: Item, wait_after_click: int = 0) -> None:
        """
        Click the expand icon for an Item regardless of expansion state. If you are attempting to set the expansion
        state, you should use :func:`set_expansion_state_for_item`

        :param item: The Item for which we will click the expansion icon.
        :param wait_after_click: The amount of time (in seconds) to wait after the click event before allowing code to
            continue.

        :raises TimeoutException: If no icon exists or if no Item with the supplied label exists.
        """
        self._get_expansion_icon(item=item).click(wait_after_click=wait_after_click)

    def click_item(self, item: Item, wait_after_click: float = 0) -> None:
        """
        Click the label of an Item.

        :param item: The Item you would like to click.
        :param wait_after_click: The amount of time (in seconds) to wait after the click event before allowing code to
            continue.

        :raises TimeoutException: If no Item with the same text is available to be clicked. This could either mean
            no Item with that text exists, or the target Item could be inside an Item which has not yet been expanded.
        """
        path = str(item)
        label = self._labels.get(path)
        if not label:
            label = ComponentPiece(
                locator=self._LABEL_LOCATOR,
                driver=self.driver,
                parent_locator_list=self._get_item(item=item).locator_list,
                poll_freq=self.poll_freq)
            self._labels[path] = label
        label.click(wait_after_click=wait_after_click)

    def expand_to_item(self, item: Item,
                       max_attempts: int = 3,
                       delay_between_attempts: float = 1.0) -> None:
        """
        Expand the Tree along the path of the Item until the Item is displayed. If the target item is not displayed
        after the configured number of attempts, raise a TimeoutException.
        This function does not actually click the supplied Item.

        :param item: The Item to which the Tree should be expanded.
        :param max_attempts: The maximum number of full attempts.
        :param delay_between_attempts: The delay in seconds between retry attempts.

        :raises TimeoutException: If any part of the ancestry of the Item was not found, or if the Item itself was
            not displayed after expanding the ancestry of the Item, or if expansion fails after max_attempts.
        """
        for attempt in range(1, max_attempts + 1):
            try:
                for path_item in item.get_ancestry():
                    self.set_expansion_state(item=path_item, should_be_expanded=True)
                # If we reach here without exception, check if item is displayed
                if self.item_is_displayed(item=item):
                    break
            except (TimeoutException, StaleElementReferenceException) as e:
                if attempt >= max_attempts:
                    raise TimeoutException(
                        f"Could not expand ancestry to display item {item} after {max_attempts} attempts"
                    ) from e
                else:
                    time.sleep(delay_between_attempts)

    def expansion_icon_is_displayed(self, item: Item) -> bool:
        """
        Determine if an Item is currently displaying an expansion icon.

        :returns: True, if an expansion icon is displayed for the first Item with the supplied text. False, if an
            expansion icon is not displayed, or if no Item with the supplied text exists.
        """
        try:
            return ComponentPiece(
                locator=(By.CSS_SELECTOR, "g"),
                driver=self.driver,
                parent_locator_list=self._get_expansion_icon(item=item).locator_list,
                timeout=1,
                poll_freq=self.poll_freq).find().is_displayed()
        except TimeoutException:
            return False

    def get_fill_color_of_expansion_icon(self, item: Item) -> str:
        """
        Obtain the fill color of the expansion icon for an Item.

        :returns: The fill color of the expansion icon for the first Item with the supplied text as a string. Note that
            different browsers may return this string in different formats (RGB vs hex).

        :raises TimeoutException: If no expansion icon exists for the Item, or if no Item with matching text exists.
        """
        return self._get_expansion_icon(item=item).get_fill_color()

    def get_fill_color_of_icon(self, item: Item) -> str:
        """
        Obtain the fill color of the icon for an item.

        :returns: The fill color of the icon for the Item. Note that different browsers may return this string in
            different formats (RGB vs hex).

        :raises TimeoutException: If no icon exists for the item, or if no Item with the supplied text exists.
        """
        return self._get_icon(item=item).get_fill_color()

    def get_path_of_expansion_icon(self, item: Item) -> str:
        """
        Obtain the path of the expansion icon in use by an Item.

        :returns: A slash-delimited string representing the path of the svg in use.

        :raises TimeoutException: If no expansion icon exists for the Item, or if no Item with matching text exists.
        """
        return self._get_expansion_icon(item=item).get_icon_name()

    def get_path_of_node_icon(self, item: Item) -> str:
        """
        Obtain the path of the icon in use by an Item.

        :returns: A slash-delimited string representing the path of the svg in use.

        :raises TimeoutException: If no icon exists for the Item, or if no Item with matching text exists.
        """
        return self._get_icon(item=item).get_icon_name()

    def get_text_of_top_level_items(self) -> List[str]:
        """
        Obtain the text of all items located at the top-most level.

        :returns: A list of strings, where each entry in the list is the displayed text of an Item at the top-most
            level of the Tree.
        """
        try:
            return [_.text for _ in self._top_level_items.find_all()]
        except TimeoutException:
            return []

    def get_text_of_all_items_in_tree(self, timeout: float = 5) -> List[str]:
        """
        Obtain a list which contains the text of all displayed items in the Tree.

        :returns: A list of strings, where each entry in the list is the displayed text of an Item in the Tree.

        :param timeout: How long to potentially wait (in seconds) for any Tree Items to appear.
        """
        try:
            return [item.text for item in self._tree_items.find_all(timeout=timeout)]
        except TimeoutException:
            return []

    def multi_select(
            self, items: List[Item], inclusive_multi_selection: bool = True, timeout: float = 5) -> None:
        """
        Select multiple Items within the Tree. Note that any selections previous to this function could be lost.

        :param items: A list of Items to select.
        :param inclusive_multi_selection: Dictates whether we are holding Shift (True) or CMD/Ctrl (False) while making
            the selections.
        :param timeout: The amount of time to wait for each Item to become available before attempting selection.

        :raises TimeoutException: If no Item exists with text matching any individual entry from the supplied list.
        """
        actions = ActionChains(self.driver)
        if inclusive_multi_selection:
            mod_key = Keys.SHIFT
        else:
            mod_key = Keys.COMMAND if sys.platform.startswith('darwin') else Keys.CONTROL

        actions.key_down(mod_key)
        piece_list = [self._get_item(item=item, timeout=timeout) for item in items]
        for piece in piece_list:
            actions.click(on_element=piece.find()).pause(1)
        actions.key_up(mod_key)
        actions.perform()
        self.wait_some_time(1)

    def item_is_displayed(self, item: Item) -> bool:
        """
        Determine if an Item is displayed within the Tree.

        :param item: The Item whose existence you wish to verify.

        :returns: True, if the Item is displayed within the Tree - False otherwise.
        """
        try:
            return self._get_item(item=item).find(timeout=0).is_displayed()
        except TimeoutException:
            return False

    def item_is_expanded(self, item: Item) -> bool:
        """
        Determine if an Item is expanded.

        :param item: The Item we will check the expanded status of.

        :raises TimeoutException: If the Item we check does not have an expansion icon. This likely means that the
            specified Item is a terminal node and may not be expanded.
        """
        try:
            return self._EXPANDED_ICON_CLASS in self._get_expansion_icon(
                item=item).find(timeout=0).get_attribute(name="class")
        except TimeoutException:
            return False

    def node_icon_is_displayed(self, item: Item) -> bool:
        """
        Determine if an Item is currently displaying an icon which would convey whether the Item is a
        directory/folder or a terminal node.

        :param item: The Item we will check for a node icon.

        :returns: True, if an icon which would convey the type of the Item is displayed for the Item. False, if an
            icon is not displayed, or if no Item with matching text exists.
        """
        try:
            return ComponentPiece(
                locator=(By.CSS_SELECTOR, "g"),
                driver=self.driver,
                parent_locator_list=self._get_icon(item=item).locator_list,
                timeout=0,
                poll_freq=self.poll_freq).find().is_displayed()
        except TimeoutException:
            return False

    def select_item(self, item: Item, timeout: int = 5, wait_after_click: int = 1) -> None:
        """
        Select a single Item in the Tree.

        :param item: The Item to click.
        :param timeout: The amount of time (in seconds) to potentially wait for the Item to appear.
        :param wait_after_click: The amount of time (in seconds) to wait after clicking the Item before allowing code
            to continue.

        :raises TimeoutException: If no Item with matching text exists.
        """
        self.expand_to_item(item=item)
        self._get_item(item=item, timeout=timeout).click(wait_after_click=wait_after_click)

    def set_expansion_state(self, item: Item, should_be_expanded: bool) -> None:
        """
        Set an Item to be expanded or collapsed.

        :param item: The Item to expand or collapse.
        :param should_be_expanded: A True value specifies the Item should be expanded, while a False value specifies the
            Item should be collapsed.

        :raises TimeoutException: If no Item with matching text exists, or if the specified Item has no expansion
            icon.
        """
        self.expand_to_item(item=item)
        if self.item_is_expanded(item=item) != should_be_expanded:
            try:
                self._get_expansion_icon(item=item).click(wait_after_click=0.5)  # allow UI to catch up after
            except TimeoutException as toe:
                raise TimeoutException(
                    msg=f"Node with path of '{item}' does not contain an expand/collapse icon, so we may not "
                        f"expand it.") from toe

    def _get_expansion_icon(self, item: Item) -> CommonIcon:
        """Obtain the icon which conveys the expansion status of the Item."""
        path = str(item)
        icon = self._expand_collapse_icons.get(path)
        if not icon:
            icon = CommonIcon(
                locator=(By.CSS_SELECTOR, "svg.expand-icon"),
                driver=self.driver,
                parent_locator_list=self._get_item(item=item).locator_list,
                poll_freq=self.poll_freq)
            self._expand_collapse_icons[path] = icon
        return icon

    def _get_icon(self, item: Item) -> CommonIcon:
        """Obtain the icon which conveys whether the Item is a directory/folder or a terminal node."""
        path = str(item)
        icon = self._item_icons.get(path)
        if not icon:
            icon = CommonIcon(
                locator=(By.CSS_SELECTOR, "svg.node-icon"),
                driver=self.driver,
                parent_locator_list=self._get_item(item=item).locator_list,
                poll_freq=self.poll_freq)
            self._item_icons[path] = icon
        return icon

    def _get_index_of_item(self, item: Item) -> int:
        """Get the zero-indexed position among all items for the label with the supplied text."""
        return [_.text for _ in self._tree_items.find_all()].index(item.label)

    def _get_item(self, item: Item, timeout: float = 5) -> ComponentPiece:
        """Obtain the ComponentPiece which is described by the provided Item."""
        path = str(item)
        item_cp = self._items.get(path)
        if not item_cp:
            item_cp = ComponentPiece(
                locator=item.get_locator(),
                driver=self.driver,
                parent_locator_list=self.locator_list,
                timeout=timeout,
                poll_freq=self.poll_freq)
            self._items[path] = item_cp
        return item_cp

    @classmethod
    def _split_item_label_path(cls, slash_delimited_label_path: str) -> List[str]:
        """Obtain the pieces of a string after having split the string on a slas ('/')."""
        return slash_delimited_label_path.split('/')
