from tkinter import *
import tkinter.font as tkFont
from .. import minimal_widget

class TitleWidget(minimal_widget.MinimalWidget):
    """ A simple widget containing only text, intended for making a big-text title for a dashboard. 
    Uses the MinimalWidget superclass, since all of the GenericWidget machinery is unnecessary.\n

    :param parent_dashboard: The dashboard object to which this device will be added
    :type parent_dashboard: pyopticon.dashboard.PyOpticonDashboard
    :param title: The text to be displayed within this widget, called 'title' because it's likely to be the title of the entire dashboard.
    :type title: str
    :param font_size: The size of font to be used in the text, as an integer.
    :type font_size: int
    """

    def __init__(self,parent_dashboard,title,font_size):
        """ Constructor for a title widget."""
        super().__init__(parent_dashboard)
        fontStyle = tkFont.Font(size=font_size)
        Label(self.frame, font = fontStyle, text = title).pack()
