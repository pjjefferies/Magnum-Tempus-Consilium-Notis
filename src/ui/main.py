from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

from kivy.uix.recycleview import RecycleView


class NotisWidget(Widget):
    def __init__(self, **kwargs):
        super(NotisWidget, self).__init__(**kwargs)
        # Clock.schedule_once(self.build_rv)

    # def build_rv(self, dt):
    #     self.data = [{"text": str(x)} for x in range(100)]

    pass


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """Adds selection and focus behaviour to the view."""


class SelectableLabel(RecycleDataViewBehavior, Label):
    """Add selection support to the Label"""

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            print("selection changed to {0}".format(rv.data[index]))
        else:
            print("selection removed for {0}".format(rv.data[index]))


class TwoThings(BoxLayout):
    left_text = StringProperty()
    right_text = StringProperty()


class RV(RecycleView):
    data = ListProperty()

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = [
            {"left_text": f"Left {x}", "right_text": f"Right {x}"} for x in range(20)
        ]

    def add(self):
        l = len(self.data)
        self.data.append({"left_text": f"Left {l}", "right_text": f"Right {l}"})
        print(self.data)


class NotisApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.data = [{"text": str(x)} for x in range(30)]

    def build(self):
        return NotisWidget()


if __name__ == "__main__":
    NotisApp().run()
