import curses
import os
import platform
import threading


class CursesMenu(object):
    """
    A class that displays a menu and allows the user to select an option

    :cvar CursesMenu cls.currently_active_menu: Class variable that holds the currently active menu or None if no menu\
    is currently active (E.G. when switching between menus)
    """
    currently_active_menu = None  # define local class variable
    stdscr = None  # define local class variable

    def __init__(self, title=None, subtitle=None, show_exit_option=True):
        """
        :ivar str title: The title of the menu
        :ivar str subtitle: The subtitle of the menu
        :ivar bool show_exit_option: Whether this menu should show an exit item by default. Can be overridden \
        when the menu is started
        :ivar items: The list of MenuItems that the menu will display
        :vartype items: list[:class:`MenuItem<cursesmenu.items.MenuItem>`]
        :ivar CursesMenu parent: The parent of this menu
        :ivar CursesMenu previous_active_menu: the previously active menu to be restored into the class's \
        currently active menu
        :ivar int current_option: The currently highlighted menu option
        :ivar MenuItem current_item: The item corresponding to the menu option that is currently highlighted
        :ivar int selected_option: The option that the user has most recently selected
        :ivar MenuItem selected_item: The item in :attr:`items` that the user most recently selected
        :ivar returned_value: The value returned by the most recently selected item
        :ivar screen: the curses window associated with this menu
        :ivar normal: the normal text color pair for this menu
        :ivar highlight: the highlight color pair associated with this window
        """

        self.screen = None  # define class variable
        self.highlight = None  # define class variable
        self.normal = None  # define class variable

        self.title = title  # define class variable
        self.subtitle = subtitle  # define class variable
        self.show_exit_option = show_exit_option  # define class variable default True

        self.items = list()  # define items as empty list

        self.parent = None  # define class variable

        self.exit_item = ExitItem(menu=self) # ??? define class variable

        self.current_option = 0  # define class variable
        self.selected_option = -1  # define class variable

        self.returned_value = None  # define class variable

        self.should_exit = False  # define class variable as False

        self.previous_active_menu = None  # define class variable

        self._main_thread = None  # define main thread as frequently changed class variable

        self._running = threading.Event()  # define class variable as Event in threading

    def __repr__(self):
        return "%s: %s. %d items" % (self.title, self.subtitle, len(self.items))  # define repr of class

    @property
    def current_item(self):  # define current item as property of class
        """
        :rtype: MenuItem|None
        """
        if self.items:  # if items exists DO:
            return self.items[self.current_option]  # return item of current option
        else:
            return None  # if not exists return None

    @property
    def selected_item(self):  # define selected item as property of the class
        """
        :rtype: MenuItem|None
        """
        if self.items and self.selected_option != -1:  # if items and selected options is not -1
            return self.items[self.current_option]  # return value from items
        else:
            return None  # returns none

    def append_item(self, item):
        """
        Add an item to the end of the menu before the exit item

        :param MenuItem item: The item to be added
        """
        did_remove = self.remove_exit()  # remove exit item
        item.menu = self  # ???
        self.items.append(item)  # append new item in menu
        if did_remove:  #  if did remove exit item
            self.add_exit()  # add exit at end of items
        if self.screen:  # if screen exists
            max_row, max_cols = self.screen.getmaxyx()  # get terminal size
            if max_row < 6 + len(self.items):  # if screen is too small
                self.screen.resize(6 + len(self.items), max_cols)  # screen resize
            self.draw()  # draw screen

    def add_exit(self):
        """
        Add the exit item if necessary. Used to make sure there aren't multiple exit items

        :return: True if item needed to be added, False otherwise
        :rtype: bool
        """
        if self.items:  # if items exists
            if self.items[-1] is not self.exit_item: # if last item is not exit
                self.items.append(self.exit_item)  # append exit
                return True  # return True -
        return False

    def remove_exit(self):
        """
        Remove the exit item if necessary. Used to make sure we only remove the exit item, not something else

        :return: True if item needed to be removed, False otherwise
        :rtype: bool
        """
        if self.items:  # if items exists
            if self.items[-1] is self.exit_item:  # if last item in menu is exit
                del self.items[-1]  # delete exit from items
                return True  # return True
        return False

    def _wrap_start(self):  # start wrap menu
        if self.parent is None:  # if parent is none
            curses.wrapper(self._main_loop)  # start wrapping main loop menu
        else:  # if main loop has parent - wrapper
            self._main_loop(None)  # start mainloop
        CursesMenu.currently_active_menu = None  # active menu is None
        self.clear_screen()  # clear screen for rendering
        clear_terminal()  # clear terminal
        CursesMenu.currently_active_menu = self.previous_active_menu  # setting menu to previous active

    def start(self, show_exit_option=None):
        """
        Start the menu in a new thread and allow the user to interact with it.
        The thread is a daemon, so :meth:`join()<cursesmenu.CursesMenu.join>` should be called if there's a possibility\
        that the main thread will exit before the menu is done

        :param bool show_exit_option: Whether the exit item should be shown, defaults to\
        the value set in the constructor
        """

        self.previous_active_menu = CursesMenu.currently_active_menu  # setting previosu active to currently active
        CursesMenu.currently_active_menu = None  # setting currently active menu as none

        self.should_exit = False  # setting should exit as False

        if show_exit_option is None:  # if show exit is none
            show_exit_option = self.show_exit_option  # set method variable to class variable

        if show_exit_option:
            self.add_exit()  # add exit
        else:
            self.remove_exit()  # remove exit

        try:  # try start wrapper as new thread
            self._main_thread = threading.Thread(target=self._wrap_start, daemon=True)  # main threas
        except TypeError:  # if typeerror is raised
            self._main_thread = threading.Thread(target=self._wrap_start)  # start new thread
            self._main_thread.daemon = True  # as a deamon

        self._main_thread.start()  # thread start

    def show(self, show_exit_option=None):
        """
        Calls start and then immediately joins.

        :param bool show_exit_option: Whether the exit item should be shown, defaults to the value set \
        in the constructor
        """
        self.start(show_exit_option)  # start thread
        self.join()  # join

    def _main_loop(self, scr):  # method main loop
        if scr is not None:  # if screen exists
            CursesMenu.stdscr = scr  # defines screen as scr parameter
        self.screen = curses.newpad(len(self.items) + 6, CursesMenu.stdscr.getmaxyx()[1])  # start newpad plus menu
        self._set_up_colors()  # setup colors
        curses.curs_set(0)  # set cursor
        CursesMenu.stdscr.refresh()  # refresh window
        self.draw()  # self draw screen
        CursesMenu.currently_active_menu = self  # ????
        self._running.set()  # set running
        while self._running.wait() is not False and not self.should_exit: #when running wait is True or None and is not exit
            self.process_user_input()  # waiting for input

    def draw(self):
        """
        Redraws the menu and refreshes the screen. Should be called whenever something changes that needs to be redrawn.
        """

        self.screen.border(0)  # setting screen border
        if self.title is not None:  # if screen title exists
            self.screen.addstr(2, 2, self.title, curses.A_STANDOUT)  # write it to screen
        if self.subtitle is not None:  # if subtitle exists
            self.screen.addstr(4, 2, self.subtitle, curses.A_BOLD)  # write it to screen

        for index, item in enumerate(self.items):  # index all items in menu
            if self.current_option == index:  # if current is index
                text_style = self.highlight  # highlight item
            else:
                text_style = self.normal  # if not current render normal text
            self.screen.addstr(5 + index, 4, item.show(index), text_style) # render menu

        screen_rows, screen_cols = CursesMenu.stdscr.getmaxyx()  # get terminal size
        top_row = 0  # firs row is set to zero
        if 6 + len(self.items) > screen_rows: # if menu is bigger than terminal
            if screen_rows + self.current_option < 6 + len(self.items):  # if render is normal
                top_row = self.current_option  # stays with current setting
            else:
                top_row = 6 + len(self.items) - screen_rows  # ???

        self.screen.refresh(top_row, 0, 0, 0, screen_rows - 1, screen_cols - 1)  # screen refresh

    def is_running(self):
        """
        :return: True if the menu is started and hasn't been paused
        """
        return self._running.is_set()  # checks if menu is runnig

    def wait_for_start(self, timeout=None):
        """
        Block until the menu is started

        :param timeout: How long to wait before timing out
        :return: False if timeout is given and operation times out, True otherwise. None before Python 2.7
        """
        return self._running.wait(timeout)  # waits to restart of menu

    def is_alive(self):
        """
        :return: True if the thread is still alive, False otherwise
        """
        return self._main_thread.is_alive()  # checks if main thread is alive

    def pause(self):
        """
        Temporarily pause the menu until resume is called
        """
        self._running.clear()  # pause menu until resume

    def resume(self):
        """
        Sets the currently active menu to this one and resumes it
        """
        CursesMenu.currently_active_menu = self  # sets currently active to self (object)
        self._running.set()  # set running

    def join(self, timeout=None):
        """
        Should be called at some point after :meth:`start()<cursesmenu.CursesMenu.start>` to block until the menu exits.
        :param Number timeout: How long to wait before timing out
        """
        self._main_thread.join(timeout=timeout)  # join main thread

    def get_input(self):
        """
        Can be overridden to change the input method.
        Called in :meth:`process_user_input()<cursesmenu.CursesMenu.process_user_input>`

        :return: the ordinal value of a single character
        :rtype: int
        """
        return CursesMenu.stdscr.getch()  # get input from user

    def process_user_input(self):
        """
        Gets the next single character and decides what to do with it
        """
        user_input = self.get_input()  # define user input as get input

        go_to_max = ord("9") if len(self.items) >= 9 else ord(str(len(self.items))) # max value is 9 items ???

        if ord('1') <= user_input <= go_to_max:  # if user enters number go there in menu
            self.go_to(user_input - ord('0') - 1) # go there
        elif user_input == curses.KEY_DOWN:  # if user gives KEY DOWN go down by 1
            self.go_down()
        elif user_input == curses.KEY_UP:  # if user gives KEY UP go up by 1
            self.go_up()
        elif user_input == ord("\n"):  # if user gives ENTER select and execute
            self.select()

        return user_input  # return user input

    def go_to(self, option):
        """
        Go to the option entered by the user as a number

        :param option: the option to go to
        :type option: int
        """
        self.current_option = option
        self.draw()

    def go_down(self):
        """
        Go down one, wrap to beginning if necessary
        """
        if self.current_option < len(self.items) - 1:
            self.current_option += 1
        else:
            self.current_option = 0
        self.draw()

    def go_up(self):
        """
        Go up one, wrap to end if necessary
        """
        if self.current_option > 0:
            self.current_option += -1
        else:
            self.current_option = len(self.items) - 1
        self.draw()

    def select(self):
        """
        Select the current item and run it
        """
        self.selected_option = self.current_option
        self.selected_item.set_up()
        self.selected_item.action()
        self.selected_item.clean_up()
        self.returned_value = self.selected_item.get_return()
        self.should_exit = self.selected_item.should_exit

        if not self.should_exit:
            self.draw()

    def exit(self):
        """
        Signal the menu to exit, then block until it's done cleaning up
        """
        self.should_exit = True
        self.join()

    def _set_up_colors(self):
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.highlight = curses.color_pair(1)
        self.normal = curses.A_NORMAL

    def clear_screen(self):
        """
        Clear the screen belonging to this menu
        """
        self.screen.clear()


class MenuItem(object):
    """
    A generic menu item
    """

    def __init__(self, text, menu=None, should_exit=False):
        """
        :ivar str text: The text shown for this menu item
        :ivar CursesMenu menu: The menu to which this item belongs
        :ivar bool should_exit: Whether the menu should exit once this item's action is done
        """
        self.text = text
        self.menu = menu
        self.should_exit = should_exit

    def __str__(self):
        return "%s %s" % (self.menu.title, self.text)

    def show(self, index):
        """
        How this item should be displayed in the menu. Can be overridden, but should keep the same signature.

        Default is:

            1 - Item 1

            2 - Another Item

        :param int index: The index of the item in the items list of the menu
        :return: The representation of the item to be shown in a menu
        :rtype: str
        """
        return "%d - %s" % (index + 1, self.text)

    def set_up(self):
        """
        Override to add any setup actions necessary for the item
        """
        pass

    def action(self):
        """
        Override to carry out the main action for this item.
        """
        pass

    def clean_up(self):
        """
        Override to add any cleanup actions necessary for the item
        """
        pass

    def get_return(self):
        """
        Override to change what the item returns.
        Otherwise just returns the same value the last selected item did.
        """
        return self.menu.returned_value


class ExitItem(MenuItem):
    """
    Used to exit the current menu. Handled by :class:`cursesmenu.CursesMenu`
    """

    def __init__(self, text="Exit", menu=None):
        super(ExitItem, self).__init__(text=text, menu=menu, should_exit=True)

    def show(self, index):
        """
        This class overrides this method
        """
        if self.menu and self.menu.parent:
            self.text = "Return to %s menu" % self.menu.parent.title
        else:
            self.text = "Exit"
        return super(ExitItem, self).show(index)


def clear_terminal():
    """
    Call the platform specific function to clear the terminal: cls on windows, reset otherwise
    """
    if platform.system().lower() == "windows":
        os.system('cls')
    else:
        os.system('reset')
