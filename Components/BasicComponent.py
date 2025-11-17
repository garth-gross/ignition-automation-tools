import functools
import inspect
import re
from enum import Enum
from time import sleep
from typing import Optional, Union, List, Tuple, Any, Dict, TypeVar, Type, Self, Callable

from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, \
    TimeoutException, \
    ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from Helpers import CSSEnumerations
from Helpers.CSSEnumerations import CSSPropertyValue
from Helpers.IAExpectedConditions import IAExpectedConditions as IAec
from Helpers.IASelenium import IASelenium
from Helpers.PerspectivePages.Quality import PerspectiveQuality
from Helpers.Point import Point

K = List[Union[int, float, str]]
V = TypeVar('V')


class ComponentCollection(Dict[K, V]):

    def __init__(
            self,
            by: str,
            locator_string_ready_for_formatting: str,
            component_class: Type[V],
            driver: WebDriver,
            parent_locator_list: Optional[list] = None,
            timeout: float = 10.0,
            description: Optional[str] = None,
            poll_freq: float = 0.5):
        super().__init__()
        self._by = by
        self._locator_string_ready_for_formatting = locator_string_ready_for_formatting
        self._component_class = component_class
        self._driver = driver
        self._parent_locator_list = parent_locator_list
        self._timeout = timeout
        self._description = description
        self._poll_freq = poll_freq

    def get(self, list_of_pieces_to_format: K) -> V:
        """
        Obtain a component from the running collection.

        :param list_of_pieces_to_format: A list of values to be formatted into the locator string.
        :return: A component of the type specified in the constructor.
        """
        locator = (self._by, self._locator_string_ready_for_formatting.format(*list_of_pieces_to_format))
        component = super().get(locator)
        if not component:
            component = self._component_class(
                locator=locator,
                driver=self._driver,
                parent_locator_list=self._parent_locator_list,
                timeout=self._timeout,
                description=self._description,
                poll_freq=self._poll_freq)
            # The following line ignores a type difference between the declared class type K and the locator tuple.
            # We are storing and retrieving values internally under a different pattern.
            # noinspection PyTypeChecker
            self[locator] = component
        return component


class ComponentPiece:
    """
    Component Pieces may be understood as distinct Web Elements which are actually pieces of a greater component.
    """
    # For use on checkboxes that are pieces of another component
    _CHECKBOX_LOCATOR = (By.CSS_SELECTOR, 'label.ia_checkbox svg')
    _CHECKBOX_CHECKED = 'ia_checkbox__checkedIcon'
    _CHECKBOX_UNCHECKED = 'ia_checkbox__uncheckedIcon'

    def __init__(
            self,
            locator: Tuple[str, str],
            driver: WebDriver,
            parent_locator_list: Optional[list] = None,
            timeout: float = 10.0,
            description: Optional[str] = None,
            poll_freq: float = 0.5):
        """
        locator: Tuple
            A tuple which defines the CSS selector which would be used to locate the component.
        driver: WebDriver
            The WebDriver used to drive the session/page.
        parent_locator_list: List
            A list of the locators used to build the parent of this component. A value of None will be interpreted
            as opting into ignorance of the parentage of the component.
        timeout: float
            The amount of time to poll the DOM before throwing a potential TimeoutException in the event this component
            could not be located.
        poll_freq: float
            A value used to determine how frequently to poll the DOM. Used primarily for performance testing.
        """
        self._locator = locator
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver=self.driver, timeout=timeout, poll_frequency=poll_freq)
        self.description = description
        self._parent_locator_list = parent_locator_list.copy() if parent_locator_list else []
        self._update_locator_list()
        self.poll_freq = poll_freq

    @staticmethod
    def retry_on_stale_element(retry_attempts: int = 3):
        def decorator(call: Callable) -> Callable:
            @functools.wraps(call)
            def wrapper(self, *args, **kwargs):
                for attempt in range(retry_attempts):
                    try:
                        return call(self, *args, **kwargs)
                    except StaleElementReferenceException:
                        pass
                # final attempt
                return call(self, *args, **kwargs)
            # Preserve signature so pytest can see fixture parameters
            wrapper.__signature__ = inspect.signature(call)
            return wrapper
        return decorator

    @retry_on_stale_element()
    def boundary_collision(self, other_component: Self) -> bool:
        """
        Determine if the boundaries of this component overlap with another component. The compared components
        may touch, but not overlap.

        :param other_component: The other component to compare against.

        :returns: True, if the boundaries of this component overlap with another component, False otherwise - even if
            the components are touching.
        """
        rect_1 = self.find().rect
        rect_2 = other_component.find().rect
        return (rect_1['x'] < rect_2['x'] + rect_2['width']
                and rect_1['x'] + rect_1['width'] > rect_2['x']
                and rect_1['y'] < rect_2['y'] + rect_2['height']
                and rect_1['y'] + rect_1['height'] > rect_2['y'])

    def click(self, timeout: Optional[Union[int, float]] = None, wait_after_click: float = 0) -> None:
        """
        Click the component.

        :param timeout: Poll the DOM up to this amount of time before potentially throwing a TimeoutException.
            Overrides the default of the component.
        :param wait_after_click: The amount of time to wait after the click event occurs before continuing.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        wait = WebDriverWait(driver=self.driver, timeout=timeout) if timeout is not None else self.wait
        self.find(timeout=timeout)  # do not capture TimeoutException here

        # A TimeoutException here means the element never became clickable.
        wait.until(
            IAec.function_returns_true(custom_function=self._click, function_args={}),
            message="The element never became clickable.")
        self.wait_some_time(time_to_wait=wait_after_click)

    @retry_on_stale_element()
    def click_with_offset(self, x_offset: int, y_offset: int) -> None:
        """
        Click this element, but offset by some pixel count.

        :param x_offset: The count of pixels to move right before clicking.
        :param y_offset: The count of pixels to move down before clicking.

        :raises TimeoutException: If the component is not found in the DOM.
        :raises ElementClickInterceptedException: If the offset click is intercepted by some other element.
        """
        try:
            ActionChains(self.driver).move_to_element_with_offset(
                to_element=self.find(),
                xoffset=x_offset,
                yoffset=y_offset
            ).click().perform()
        except ElementClickInterceptedException as ecie:
            IASelenium(self.driver).take_screenshot_of_element(self.find())
            raise ecie

    @retry_on_stale_element()
    def double_click(self, wait_after_click: float = 0) -> None:
        """
        Double-click the component.

        :param wait_after_click: The amount of time to wait after the double-click event occurs before continuing.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        ActionChains(self.driver).move_to_element(to_element=self.find()).double_click(on_element=self.find()).perform()
        self.wait_some_time(time_to_wait=wait_after_click)

    def find(self, timeout: Optional[Union[int, float]] = None) -> WebElement:
        """
        Get a singular Web Element in the DOM which matches the supplied locator for this component. If more than one
        Web Element would match, return only the first match encountered in the DOM from top to bottom in the document
        - NOT the viewable area. Distinct from `xfind`, which uses XPATH.

        :param timeout: The amount of time (in seconds) to wait to locate the Web Element.

        :returns: The first Web Element found given the supplied locator for this component.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        if timeout is not None:  # 0 is acceptable
            local_wait = WebDriverWait(
                self.driver,
                timeout)
        else:
            local_wait = self.wait
        css_locator = self.get_full_css_locator()
        try:
            return local_wait.until(
                ec.presence_of_element_located(
                    css_locator))
        except TimeoutException as toe:
            description = f"\nDescription: {self.description}" if self.description else ''
            raise TimeoutException(
                msg=f"Unable to locate element with CSS locator: {css_locator}{description}") from toe

    def find_all(self, timeout: Optional[Union[int, float]] = None) -> List[WebElement]:
        """
        Get a list of all Web Elements in the DOM which match the supplied locator for this component.  Distinct from
        `xfind_all`, which uses XPATH.

        :param timeout: The amount of time (in seconds) to wait to locate the Web Element.

        :returns: A list of all Web Elements in the DOM which match the supplied locator for this component

        :raises TimeoutException: If no elements match the locator of this component.
        """
        if timeout is not None:  # 0 is acceptable
            local_wait = WebDriverWait(self.driver, timeout)
        else:
            local_wait = self.wait
        css_locator = self.get_full_css_locator()
        try:
            return local_wait.until(ec.presence_of_all_elements_located(css_locator))
        except TimeoutException as toe:
            description = f"\nDescription: {self.description}" if self.description else ''
            raise TimeoutException(
                msg=f"Unable to locate any elements with CSS locator: {css_locator}{description}") from toe

    @retry_on_stale_element()
    def get_computed_height(self, include_units: bool = False) -> str:
        """
        Get the computed height of the component. Must return as a string because of the possibility of included units.

        :param include_units: Include the units of height (typically "px") if True, otherwise return only the numeric
            value (as a str).

        :returns: The computed height of the component as a string.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        height = self.find().value_of_css_property("height")
        # special handling for flex containers
        if height == "auto":
            # no need to strip units here because it's always numeric
            return self.find().rect['height']
        if not include_units:
            height = height.split("px")[0]
        return height

    @retry_on_stale_element()
    def get_computed_width(self, include_units: bool = False) -> str:
        """
        Get the computed width of the component. Must return as a string because of the possibility of included units.

        :param include_units: Include the units of width (typically "px") if True, otherwise return only the numeric
            value (as a str).

        :returns: The computed width of the component as a string.

        :raises TimeoutException: If the component is not found in the DOM.
        """
        width = self.find().value_of_css_property("width")
        # special handling for flex containers
        if width == "auto":
            # no need to strip units here because it's always numeric
            return self.find().rect['width']
        if not include_units:
            width = width.split("px")[0]
        return width

    @retry_on_stale_element()
    def get_css_property(self, property_name: Union[CSSPropertyValue, str]) -> str:
        """
        Get a CSS property value of the Web Element defined by this component.

        :param property_name: The name of the CSS property you would like to retrieve the value of.

        :raises TimeoutException: If the element is not present on the page.

         :returns: The CSS property value of the Web Element defined by this component.
        """
        # cast arg as string to get underlying value of CSSPropertyValue type.
        return self.find().value_of_css_property(property_name=str(property_name))

    def get_full_css_locator(self) -> Tuple[Union[By, str], str]:
        """
        Get the fully constructed CSS selector of this component.

        :returns: The fully constructed CSS selector of this component.
        """
        return _LocatorBuilder.get_css_locator(locators=self.locator_list)

    def get_full_xpath_locator(self) -> Tuple[Union[By, str], str]:
        """
        Get the fully constructed XPATH selector of this component.

        :returns: The fully constructed XPATH selector of this component.
        """
        return _LocatorBuilder.get_xpath_locator(locators=self.locator_list)

    @retry_on_stale_element()
    def get_origin(self) -> Point:
        """
        Get the Cartesian Coordinate of the upper-left corner of the component, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the upper-left corner of the component, measured from the
            top-left of the viewport.
        """
        rect = self.find().rect
        return Point(x=rect['x'], y=rect['y'])

    @retry_on_stale_element()
    def get_termination(self) -> Point:
        """
        Get the Cartesian Coordinate of the bottom-right corner of the component, measured from the
        top-left of the viewport.

        :returns: The Cartesian Coordinate of the bottom-right corner of the component, measured from the
            top-left of the viewport.
        """
        rect = self.find().rect
        return Point(rect['x'] + rect['width'], rect['y'] + rect['height'])

    @retry_on_stale_element()
    def get_text(self) -> str:
        """
        Get the text of this component.
        :returns: The text of this component as a string.

        :raises TimeoutException: If the element is not present on the page.
        """
        return self.find().text

    @retry_on_stale_element()
    def hover(self) -> None:
        """
        Hover over this component.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        ActionChains(self.driver).move_to_element(self.find()).perform()

    @retry_on_stale_element()
    def is_displayed(self) -> bool:
        """
        Determine if a component is currently displayed.

        :returns: True, if the Component is currently displayed - False otherwise.
        """
        try:
            return self.find(timeout=0).is_displayed()
        except TimeoutException:
            return False

    def lose(self, timeout: Optional[float] = None) -> None:
        """
        Wait some period of time for the component to not be present in the DOM.
        """
        wait = WebDriverWait(self.driver, timeout) if timeout is not None else self.wait
        css_locator = self.get_full_css_locator()
        try:
            wait.until_not(ec.presence_of_element_located(css_locator))
        except TimeoutException as toe:
            description = f"\nDescription: {self.description}" if self.description else ''
            raise TimeoutException(
                msg=f"Element with CSS locator was never removed from the DOM: {css_locator}{description}") from toe

    @retry_on_stale_element()
    def release_focus(self) -> None:
        """
        Forces a blur() event on the Web Element.
        """
        self.driver.execute_script('arguments[0].blur()', self.find())

    @retry_on_stale_element()
    def right_click(self, wait_after_click: Optional[float] = 0) -> None:
        """
        Right-click this component.

        :param wait_after_click: The amount of time to wait after the click event occurs before continuing.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        IASelenium(driver=self.driver).right_click(web_element=self.find())
        self.wait_some_time(time_to_wait=wait_after_click)

    @retry_on_stale_element()
    def scroll_to_element(
            self,
            behavior: CSSEnumerations.CSS.Behavior = CSSEnumerations.CSS.Behavior.AUTO,
            block: CSSEnumerations.CSS.Block = CSSEnumerations.CSS.Block.START,
            inline: CSSEnumerations.CSS.Inline = CSSEnumerations.CSS.Inline.NEAREST) -> None:
        """
        For information about the default values, please visit
        https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView
        """
        self.driver.execute_script(
            'arguments[0].scrollIntoView({behavior: "' +
            str(behavior) + '", block: "' +
            str(block) + '", inline: "' +
            str(inline) + '"});',
            self.find())

    def set_locator(self, new_locator: Tuple[Union[By, str], str]) -> None:
        """
        Force a change in the locator/selector used to locate the component in the DOM.

        :param new_locator: The new locator to change to.
        """
        self._locator = new_locator
        self._update_locator_list()

    def wait_on_text_condition(
            self,
            text_to_compare: Optional[Any],
            condition: Union[IAec.TextCondition, IAec.NumericCondition],
            timeout: Optional[float] = None) -> str:
        """
        Obtain the text of this Component, after potentially waiting some period of time for the Component to display
        that text.

        :param text_to_compare: The text to be used in conjunction with the supplied condition. If the supplied value
            is None, then no wait will ever occur and the text of the component will be immediately returned.
        :param condition: The condition to be used to compare the Component text to the provided text.
        :param timeout: The amount of time (in seconds) you are willing to wait for the Component to display
            the specified text. If not supplied, this will default to the wait timeout supplied in the constructor
            of the Component.

        :returns: The text of the Component, after potentially having waited for an expected text match.
        """
        cond_wait = WebDriverWait(driver=self.driver, timeout=timeout) if timeout is not None else self.wait
        text_to_compare = str(text_to_compare) if text_to_compare is not None else text_to_compare
        text = ""
        present_then_removed = False

        def compare_against_condition():
            """
            Comparisons are only completed when the supplied comparison value is not None. One check is always executed
            to safeguard against StaleElementReferenceExceptions.

            :return: True, if the text of the Component satisfies the specified condition - False otherwise.

            :raises NotImplementError: If the specified condition is not supported.
            """
            nonlocal text
            nonlocal text_to_compare
            nonlocal present_then_removed
            try:
                text = self.get_text()
                present_then_removed = True
            except TimeoutException as get_text_toe:
                if not present_then_removed:
                    # toe from failing to locate the component/element at any point in time should be raised. We do
                    # not want to raise this TOE if the component was present at some point in time.
                    get_text_toe.should_raise = True
                raise
            if text_to_compare is None:
                # immediately return because the text will NEVER compare correctly against None
                return text
            if condition == IAec.TextCondition.EQUALS:
                return text_to_compare == text
            elif condition == IAec.TextCondition.DOES_NOT_EQUAL:
                return text_to_compare != text
            elif condition == IAec.TextCondition.CONTAINS:
                return text_to_compare in text
            elif condition == IAec.TextCondition.DOES_NOT_CONTAIN:
                return text_to_compare not in text
            elif condition == IAec.NumericCondition.EQUALS:
                return str(text_to_compare).replace(",", "") == str(text).replace(",", "")
            elif condition == IAec.NumericCondition.DOES_NOT_EQUAL:
                return str(text_to_compare).replace(",", "") != str(text).replace(",", "")
            else:
                raise NotImplementedError("Unhandled condition while comparing text.")

        try:
            cond_wait.until(IAec.function_returns_true(custom_function=compare_against_condition, function_args={}))
        except TimeoutException as toe:
            if getattr(toe, 'should_raise', False):
                raise  # due to failing to find the component/element
            pass  # otherwise pass because toe originated from not meeting condition
        return text

    def xfind(self, timeout: Optional[int] = None) -> WebElement:
        """
        Get a singular Web Element in the DOM which matches the supplied locator for this component. If more than one
        Web Element would match, return only the first match encountered in the DOM from top to bottom in the document
        - NOT the viewable area. Distinct from `find`, which uses CSS_SELECTOR.

        :param timeout: The amount of time (in seconds) to wait to locate the Web Element.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        if timeout is not None:
            local_wait = WebDriverWait(self.driver, timeout)
        else:
            local_wait = self.wait
        xpath_locator = self.get_full_xpath_locator()
        try:
            return local_wait.until(ec.presence_of_element_located(xpath_locator))
        except TimeoutException as toe:
            description = f"\nDescription: {self.description}" if self.description else ''
            raise TimeoutException(
                msg=f"Unable to locate any elements with XPath locator: {xpath_locator}{description}") from toe

    def xfind_all(self, timeout: Optional[int] = None) -> List[WebElement]:
        """
        Get a list of Web Elements in the DOM which matches the supplied locator for this component. Distinct from
        `find_all`, which uses CSS_SELECTOR.

        :param timeout: The amount of time (in seconds) to wait to locate the Web Element.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        if timeout is not None:
            local_wait = WebDriverWait(self.driver, timeout)
        else:
            local_wait = self.wait
        xpath_locator = self.get_full_xpath_locator()
        try:
            return local_wait.until(ec.presence_of_all_elements_located(xpath_locator))
        except TimeoutException as toe:
            description = f"\nDescription: {self.description}" if self.description else ''
            raise TimeoutException(
                msg=f"Unable to locate any elements with XPath locator: {xpath_locator}{description}") from toe

    @staticmethod
    def wait_some_time(time_to_wait=0.5) -> None:
        """
        A glorified hard-coded sleep, used to force the code to wait after some event before allowing code to
        continue.

        :param time_to_wait: The amount of time (in seconds) to wait.
        """
        sleep(time_to_wait)

    @retry_on_stale_element()
    def _click(self) -> bool:
        """
        Attempt to click an item, and continue attempting to do so until the item becomes "interactable".

        Some Perspective UI pieces (like Dropdown option items) appear in the DOM before they can be clicked, and so
        an attempt to interact with them before they are ready can result in a script failure.

        :return: True, if the click is successful - False if the element is not ready to be clicked.
        """
        try:
            self.find(timeout=0).click()
            return True
        except ElementNotInteractableException:
            return False

    def _has_text(self, text: str) -> bool:
        """
        Used to determine if a Web Element currently has the exact supplied text.

        :param text: Check to see if the Web Element has this exact text

        :raises TimeoutException: If no element matches the locator of this component.
        """
        return self.find().text == str(text)

    def _update_locator_list(self) -> None:
        """
        Used to force an update of the internal locator list used to define the component.
        """
        if self._parent_locator_list:
            # Used for subcomponents
            self.locator_list = self._parent_locator_list.copy()
            if self._locator:
                self.locator_list.append(self._locator)
        else:
            self.locator_list = [self._locator]


class BasicComponent(ComponentPiece):
    """
    A BasicComponent is analogous to a Web Element, albeit with custom wrapping and convenience methods.
    """
    pass


class BasicPerspectiveComponent(BasicComponent):
    """
    A BasicPerspectiveComponent may only exist inside a Perspective session, and is distinct from a BasicComponent
    in providing access and insight into Quality Overlays.
    """
    _QUALITY_OVERLAY_STATE_DIV_LOCATOR = (By.CSS_SELECTOR, "div.cfo-parent")
    _QUALITY_OVERLAY_FOOTER_LOCATOR = (By.CSS_SELECTOR, "div.cfo-footer")
    _QUALITY_OVERLAY_HEADER_LOCATOR = (By.CSS_SELECTOR, "div.cfo-header")
    _HEADER_POPOVER_ICON_LOCATOR = (By.CSS_SELECTOR, "div.icon-wrapper svg")
    _MICRO_OVERLAY_ICON_LOCATOR = (By.CSS_SELECTOR, "div.micro-icon")
    _POPOVER_LOCATOR = (By.CSS_SELECTOR, "div.component-popover")
    _POPOVER_SUBSECTION_LOCATOR = (By.CSS_SELECTOR, "div.popover-body-section div.body-content")
    _POPOVER_SUBCODE_INDEX = 0
    _POPOVER_PROPERTY_INDEX = 1
    _POPOVER_DESCRIPTION_INDEX = 2

    class QualityException(Exception):
        def __init__(self, full_locator: str, msg: Optional[str] = None):
            self.full_locator = full_locator
            self.msg = msg if msg else f'The component located with "{self.full_locator}" had a quality ' \
                                       f'overlay present.'
            super().__init__(self.msg)

    class RequestPrintTarget(Enum):
        """
        The expected target to be supplied as a parameter to the requestPrint method available to components.
        """
        COMPONENT = 'component'
        VIEW = 'view'
        PAGE = 'page'

    def __init__(
            self,
            locator: Tuple[str, str],
            driver: WebDriver,
            parent_locator_list: Optional[List[Tuple[Union[By, str], str]]] = None,
            timeout: float = 10,
            description: Optional[str] = None,
            poll_freq: float = 0.5,
            raise_exception_for_overlay: bool = False):
        """
        :param locator: A tuple which defines the CSS selector which would be used to locate the component.
        :param driver: The WebDriver used to drive the session/page.
        :param parent_locator_list: A list of the locators used to build the parent of this component. A value of None
            will be interpreted as opting into ignorance of the parentage of the component.
        :param timeout: The amount of time to poll the DOM before throwing a potential TimeoutException in the event
            this component could not be located.
        :param poll_freq: A value used to determine how frequently to poll the DOM. Used primarily for performance
            testing.
        :param raise_exception_for_overlay: If True, attempts to locate this component will raise an exception in
            the event the component has any quality overlay present. If False, overlays will be ignored unless
            explicitly checked for outside of normal usage.
        """
        super().__init__(
            locator=locator,
            driver=driver,
            parent_locator_list=parent_locator_list,
            timeout=timeout,
            description=description,
            poll_freq=poll_freq)
        self._quality_overlay_state_div = ComponentPiece(
            locator=self._QUALITY_OVERLAY_STATE_DIV_LOCATOR,
            driver=driver,
            parent_locator_list=self.locator_list,
            timeout=1,
            poll_freq=poll_freq)
        self._quality_overlay_footer = ComponentPiece(
            locator=self._QUALITY_OVERLAY_FOOTER_LOCATOR,
            driver=driver,
            parent_locator_list=self._quality_overlay_state_div.locator_list,
            timeout=0,
            poll_freq=poll_freq)
        self._quality_overlay_header = ComponentPiece(
            locator=self._QUALITY_OVERLAY_HEADER_LOCATOR,
            driver=driver,
            parent_locator_list=self._quality_overlay_state_div.locator_list,
            timeout=0,
            poll_freq=poll_freq)
        self._header_popover_badges = ComponentPiece(
            locator=self._HEADER_POPOVER_ICON_LOCATOR,
            driver=driver,
            parent_locator_list=self._quality_overlay_header.locator_list,
            timeout=0,
            poll_freq=poll_freq)
        self._micro_overlay_icons = ComponentPiece(
            locator=self._MICRO_OVERLAY_ICON_LOCATOR,
            driver=driver,
            parent_locator_list=self._quality_overlay_footer.locator_list,
            timeout=0,
            poll_freq=poll_freq)
        self._quality_popover = ComponentPiece(
            locator=self._POPOVER_LOCATOR,
            driver=driver,
            parent_locator_list=None,
            timeout=1,
            poll_freq=poll_freq)
        self._quality_popover_subsections = ComponentPiece(
            locator=self._POPOVER_SUBSECTION_LOCATOR,
            driver=driver,
            parent_locator_list=self._quality_popover.locator_list,
            poll_freq=poll_freq)
        self._raise_exception_for_overlay = raise_exception_for_overlay

    def click_quality_overlay_popover_icon(self) -> None:
        """
        Click the popover icon of the quality overlay for this component.

        This click occurs every time because there is no way to know what component any open popover belongs to.
        """
        if self.quality_overlay_is_in_micro_mode():
            # fallback to "first"
            self._micro_overlay_icons.click(wait_after_click=0.1)
        else:
            self._header_popover_badges.click(wait_after_click=0.1)

    def find(self, timeout: Optional[float] = None):
        component = super().find(timeout=timeout)  # we have to wait for the component before checking for the overlay!
        if self._raise_exception_for_overlay and self.quality_overlay_is_displayed():
            raise BasicPerspectiveComponent.QualityException(full_locator=self.get_full_css_locator()[1])
        return component

    def get_column_span(self) -> int:
        """
        Get the count of columns this component spans inside a Column Container.

        :returns: The count of columns this component spans inside a Column Container as an integer.

        :raises IndexError: If the component is not inside a Column Container.
        :raises TimeoutException: If no element matches the locator of this component.
        """
        return int(self.find().value_of_css_property('grid-column-end').split('span ')[1])

    def get_display_column(self) -> int:
        """
        Get the column in which this component begins to display. Note that components may span multiple columns, but
        this function only returns the first column in which this component is displayed.

        :returns: The index of the column in which this component begins to display.

        :raises IndexError: If the component is not inside a Column Container.
        :raises TimeoutException: If no element matches the locator of this component.
        """
        return int(self.find().value_of_css_property(property_name="grid-column").split(" / span")[0])

    def get_display_row(self) -> int:
        """
        Get the row in which this component is displayed.

        :returns: The row in which this component is displayed.

        :raises IndexError: If the component is not inside a Column Container.
        :raises TimeoutException: If no element matches the locator of this component.
        """
        return int(self.find().find_element(By.XPATH, "..").get_attribute("data-row-index"))

    def get_display_span(self) -> int:
        """
        Get the count of columns this component spans.

        :returns: The count of columns this component spans.

        :raises IndexError: If the component is not inside a Column Container.
        :raises TimeoutException: If no element matches the locator of this component.
        """
        return int(self.find().value_of_css_property(property_name="span"))

    def get_origin_within_coordinate_parent(self) -> Point:
        """
        Get the origin of the component within its parent Coordinate Container. Distinct from get_origin which provides
        the origin within the viewport.

        :returns: The origin of the component within its parent Coordinate Container.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        left = self.find().value_of_css_property('left')
        top = self.find().value_of_css_property('top')
        left = left.split("px")[0]
        top = top.split("px")[0]
        return Point(x=float(left), y=float(top))

    def get_quality_overlay_footer_text(self) -> str:
        """
        Get the text of the footer of the Quality Overlay of this component.

        :returns: The text of the footer of the Quality Overlay of this component.

        :raises TimeoutException: If the component has no Quality Overlay, or if the Quality Overlay is in Micro mode.
        """
        return self._quality_overlay_footer.find().text

    def get_quality_popover_description(self) -> str:
        """
        Get the text of the description of the Quality Overlay Popover for this component.

        :returns: The text of the description of the Quality Overlay Popover for this component.

        :raises TimeoutException: If the component has no Quality Overlay, or if the Quality Overlay is in Micro mode.
        """
        self.click_quality_overlay_popover_icon()
        return self._quality_popover_subsections.find_all()[self._POPOVER_DESCRIPTION_INDEX].text

    def get_quality_popover_property(self) -> str:
        """
        Get the text of the quality property of the Quality Overlay Popover for this component.

        :returns: The text of the quality property of the Quality Overlay Popover for this component.

        :raises TimeoutException: If the component has no Quality Overlay, or if the Quality Overlay is in Micro mode.
        """
        self.click_quality_overlay_popover_icon()
        return self._quality_popover_subsections.find_all()[self._POPOVER_PROPERTY_INDEX].text

    def get_quality_popover_subcode(self) -> str:
        """
        Get the text of the quality sub-code of the Quality Overlay Popover for this component.

        :returns: The text of the quality sub-code of the Quality Overlay Popover for this component.

        :raises TimeoutException: If the component has no Quality Overlay, or if the Quality Overlay is in Micro mode.
        """
        self.click_quality_overlay_popover_icon()
        return self._quality_popover_subsections.find_all()[self._POPOVER_SUBCODE_INDEX].text

    def is_in_percent_mode(self) -> bool:
        """
        Determine if the component is a direct child of a Coordinate Container which is using percent mode to render
        children.

        :returns: True, if the component is a direct child of a Coordinate Container which is using percent mode to
            render children - False otherwise.

        :raises TimeoutException: If no element matches the locator of this component.
        """
        # When working on QA-1563, we found that .get_css_property() always returns px value instead of %
        # This issue is on the Selenium side so this method remains using .get_attribute('style') for it to work.
        return '%' in self.find().get_attribute('style').split('width: ')[1].split(';')[0]

    def quality_overlay_contains_quality(self, quality: PerspectiveQuality) -> bool:
        """
        Determine if the quality status is present within the quality overlay for this component.

        :returns: True, if the supplied quality is present - False otherwise.

        :param quality: The quality status to check for that is present on the quality overlay of this component.
        """
        if self.quality_overlay_is_in_micro_mode():
            targets = self._micro_overlay_icons.find_all()
        else:
            targets = self._header_popover_badges.find_all()
        for target in targets:
            if quality.value in target.get_attribute("class"):
                return target.is_displayed()
        return False

    def quality_overlay_footer_text_is_displayed(self) -> bool:
        """
        Determine if the quality overlay footer text is present within the quality overlay for this component.

        :returns: True, if quality overlay is present - False otherwise.
        """
        try:
            return len(self.get_quality_overlay_footer_text()) > 0
        except TimeoutException:
            return False

    def quality_popover_is_displayed(self) -> bool:
        """
        Determine if the quality popover is displayed.

        :returns: True, if the quality popover is displayed - False otherwise.
        """
        try:
            return self._quality_popover.find(timeout=0) is not None
        except TimeoutException:
            return False

    def quality_overlay_is_in_micro_mode(self) -> bool:
        """
        Determine if the quality overlay is in micro mode.

        :returns: True, if the quality overlay is in micro mode - False otherwise.
        """
        try:
            # fallback to "first"
            return self._micro_overlay_icons.find(timeout=0).is_displayed()
        except TimeoutException:
            return False

    def quality_overlay_is_displayed(self) -> bool:
        """
        Determine if the quality overlay is displayed.

        :returns: True, if the quality overlay is displayed - False otherwise.
        """
        try:
            return self._quality_overlay_state_div.find(timeout=0) is not None
        except TimeoutException:
            return False

    def wait_for_no_overlay(
            self, timeout: int = 5, raise_exception: bool = False, wait_after_overlay_removed: float = 0) -> bool:
        """
        Wait for any overlay attached to this component to be removed.

        :param timeout: The amount of time (in seconds) to wait for the overlay to disappear.
        :param raise_exception: If True, will raise a TimeoutException exception when encountered. Otherwise,
            TimeoutException will be ignored.
        :param wait_after_overlay_removed: The amount of time to wait after the overlay disperses. This can be useful
            to ensure that OPC Tag writes make it to the PLC and that all bindings are returning the current value
            on the PLC.

        :raises TimeoutException: If the overlay is still present in the DOM after the value supplied to time_to_wait
            expires.
        """
        try:
            WebDriverWait(driver=self.driver, timeout=timeout).until_not(
                IAec.function_returns_true(custom_function=self.quality_overlay_is_displayed, function_args={}))
            self.wait_some_time(time_to_wait=wait_after_overlay_removed)
            return True
        except TimeoutException as toe:
            if raise_exception:
                raise toe
            else:
                return False


class _LocatorBuilder:
    @staticmethod
    def get_css_locator(locators: list) -> Tuple[Union[By, str], str]:
        css_list = []
        complex_css_list = []
        comma_locator_pattern = '(?![^[]*[\'"][^[]*),(?![^[]*[\'"][^[]*])'

        def append_value_for_lists(new_value):
            nonlocal css_list
            nonlocal complex_css_list
            if complex_css_list:
                complex_css_list = [f'{_} {new_value}' for _ in complex_css_list]
            else:
                css_list.append(new_value)

        for locator in locators:
            if isinstance(locator, tuple):
                by, value = locator
            else:
                by, value = By.CSS_SELECTOR, locator

            match by:
                case By.XPATH:
                    raise TypeError(
                        f'Locator: {locator} has a By type of XPATH which is incompatible with '
                        'the css_selector builder.')
                case By.ID:
                    append_value_for_lists(f'[id="{value}"]')
                case By.CLASS_NAME:
                    append_value_for_lists(f'.{value}')
                case By.NAME:
                    append_value_for_lists(f'[name="{value}"]')
                case _:
                    split_locator_list = re.split(comma_locator_pattern, value)
                    if len(split_locator_list) > 1:
                        complex_list_already_exists = True if complex_css_list else False
                        locators_to_add = []
                        locators_to_remove = set()
                        for split_locator in split_locator_list:
                            if split_locator[0] == ' ':
                                split_locator = split_locator[1:]
                            if complex_list_already_exists:
                                for string_locator_list in complex_css_list:
                                    locators_to_remove.add(string_locator_list)
                                    locators_to_add.append(f'{string_locator_list} {split_locator}')
                            else:
                                complex_css_list.append(
                                    ' '.join(css_list) + (' ' + split_locator if css_list else split_locator))
                        complex_css_list += locators_to_add
                        for remove_item in locators_to_remove:
                            complex_css_list.remove(remove_item)
                    else:
                        append_value_for_lists(value)
        css_string = f'{", " if complex_css_list else " "}'.join(complex_css_list if complex_css_list else css_list)
        return By.CSS_SELECTOR, css_string

    @staticmethod
    def get_xpath_locator(locators: list) -> Tuple[Union[By, str], str]:
        xpath_list = []
        for locator in locators:
            by = locator[0]
            value = locator[1]
            if by == By.CSS_SELECTOR:
                raise TypeError(
                    f'Locator: {locator} has a By type of CSS_SELECTOR which is incompatible with the xpath builder.')
            elif by == By.ID:
                xpath_list.append(f'//*[@id="{value}"]')
            elif by == By.CLASS_NAME:
                xpath_list.append(f'//*[contains(concat(" ", normalize-space(@class), " "),"{value}")]')
            elif by == By.NAME:
                xpath_list.append(f'//*[@name="{value}"]')
            elif by == By.LINK_TEXT:
                xpath_list.append(f'//a[normalize-space()="{value}"]')
            elif by == By.PARTIAL_LINK_TEXT:
                xpath_list.append(f'//a[contains(normalize-space(),"{value}")]')
            elif by == By.TAG_NAME:
                xpath_list.append(f'//{value}')
            else:
                xpath_list.append(value)
        return By.XPATH, "".join(xpath_list)
