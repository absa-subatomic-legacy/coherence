from enum import Enum

from asciimatics.exceptions import StopApplication
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.widgets import Button, Layout, Divider, Frame, Text


class MenuOption(Button):
    def __init__(self, text, on_click, **kwargs):
        super(MenuOption, self).__init__(text, on_click, None, **kwargs)
        self._text = text


class TestingStage(Enum):
    startup = 0
    idle = 1
    run_all_tests = 2
    quit = 3


class TestStatus(object):
    def __init__(self, test_suite):
        self.can_run_tests = False
        self.is_recording = False
        self.test_suite = test_suite
        self.current_operation = TestingStage.startup

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.test_suite.clear_recorded_events()
        return self.is_recording

    def count_recorded_events(self):
        return len(self.test_suite.recorded_events)


class MainMenu(Frame):
    def __init__(self, screen, model):
        super(MainMenu, self).__init__(screen,
                                       screen.height * 2 // 3,
                                       screen.width * 2 // 3,
                                       hover_focus=True,
                                       title="Coherence Testing")
        # Save off the model that accesses the contacts database.
        self._model = model
        self._current_option_count = 0
        label_original = self.palette["label"]
        self.palette["label"] = (Screen.COLOUR_WHITE, label_original[1], label_original[2])

        main_layout = Layout([1, 1])
        self.recording_status_text = Text("Recording Events:")
        self.recording_status_text.disabled = True
        self.recording_status_text.custom_colour = "button"
        self.events_recorded_text = Text("Events Recorded:")
        self.events_recorded_text.disabled = True
        self.events_recorded_text.custom_colour = "button"
        self.total_tests_text = Text("Total Tests:")
        self.total_tests_text.disabled = True
        self.total_tests_text.custom_colour = "button"

        self._set_status()
        self.add_layout(main_layout)
        main_layout.add_widget(self.recording_status_text, 1)
        main_layout.add_widget(self.events_recorded_text, 1)
        main_layout.add_widget(self.total_tests_text, 1)

        self._add_menu_option("Toggle event recording", self._toggle_recording, main_layout)
        self._add_menu_option("Run all tests", self._quit, main_layout)
        self._add_menu_option("Quit", self._quit, main_layout)

        end_layout = Layout([1])
        self.add_layout(end_layout)
        end_layout.add_widget(Divider())
        self.fix()
        self._on_pick()

    def _add_menu_option(self, text, on_selection, layout):
        self._current_option_count += 1
        menu_option = MenuOption(f"{self._current_option_count} - {text}", on_selection)
        layout.add_widget(menu_option, 0)

    def _on_pick(self):
        pass

    def _toggle_recording(self):
        self._model.toggle_recording()
        self._set_status()

    def _set_status(self):
        self.recording_status_text.value = f'{self._model.is_recording}'
        self.events_recorded_text.value = f'{len(self._model.test_suite.recorded_events)}'
        self.total_tests_text.value = f'{self._model.test_suite.total_tests}'

    def _quit(self):
        self._model.current_operation = TestingStage.quit
        raise StopApplication("QUIT")

    def _update(self, frame_no):
        self._set_status()
        super(MainMenu, self)._update(frame_no)


def initialise(test_status):
    screen = Screen.open()
    scenes = [
        Scene([MainMenu(screen, test_status)], -1, name="Main"),
    ]

    screen.set_scenes(scenes)

    test_status.current_operation = TestingStage.idle

    return screen


def update_screen(screen, test_status):
    try:
        screen.draw_next_frame(repeat=True)
        screen.force_update()
        if test_status.current_operation == TestingStage.quit:
            screen.close()
    except StopApplication as e:
        screen.close()
