# -*- coding: utf-8 -*-
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import QSettings, QSize, Qt
import sys
import math
import uuid
import sqlite3
import qt_material
import json


IMAGES_PATH = "images/"
SETTINGS_JSON = "settings.json"

ICONS = []
with open(SETTINGS_JSON, "r") as file:
    ICONS.extend(json.load(file)["images"])


class Date:
    def __init__(self, day, mounth, year, title="", description="", icon=None, id=None, group="all") -> None:
        if id is None:
            self._id = int(uuid.uuid4())
        else:
            self._id = id
        self._group = group
        self._day = int(day)
        self._mounth = int(mounth)
        self._year = int(year)
        self._title = title
        self._description = description
        self._icon_name = icon.rstrip()
        if self._icon_name != "None":
            icon_path = str(IMAGES_PATH + self._icon_name)
            self._icon = QtGui.QIcon(icon_path)
        else:
            self._icon = None

    @property
    def day(self):
        return self._day

    @property
    def mounth(self):
        return self._mounth

    @property
    def year(self):
        return self._year

    @property
    def id(self):
        return self._id

    @property
    def group(self):
        return self._group

    @property
    def description(self):
        return self._description

    @property
    def title(self):
        return self._title

    @property
    def icon(self):
        return self._icon

    @property
    def icon_name(self):
        return self._icon_name

    @property
    def days_to(self):
        today_qtdate = QtCore.QDate(QtCore.QDateTime.currentDateTime().date())
        this_date = QtCore.QDate()
        this_date.setDate(self.year, self.mounth, self.day)
        if self.group == "_birthdays":
            this_date.setDate(today_qtdate.year(), self.mounth, self.day)
            if QtCore.QDate.daysTo(today_qtdate, this_date) <= -1:
                this_date.setDate(today_qtdate.year() + 1,
                                  self.mounth, self.day)
        return QtCore.QDate.daysTo(today_qtdate, this_date)

    def __str__(self) -> str:
        return f"{self.days_to} (дней). {self.title}"


class Calendar:
    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.con = sqlite3.connect(self.file_name)
        self.cur = self.con.cursor()
        self.con.execute(
            '''CREATE TABLE IF NOT EXISTS dates (day INTEGER ,
             mounth INTEGER , year INTEGER ,
              title TEXT, description TEXT, icon_name TEXT,
               id INTEGER, date_group TEXT);''')

    def add_date(self, date):
        self.con.execute(
            '''INSERT INTO dates VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
            (date.day, date.mounth, date.year, date.title,
             date.description, date.icon_name, str(date.id), date.group)
        )
        self.con.commit()

    def remove_date(self, date_id) -> bool:
        self.con.execute(
            '''DELETE FROM dates WHERE id=?;''',
            (str(date_id), )
        )
        self.con.commit()

    @property
    def all_dates(self):
        self.cur.execute("SELECT * FROM dates;")
        results = self.cur.fetchall()
        all_dates = []
        for e in results:
            e = list(e)
            e[6] = int(e[6])
            all_dates.append(Date(*e))
        return all_dates


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, app) -> None:
        super().__init__()
        self.app = app

        self.resize(QSize(200, 600))

        self.calendar = Calendar("dates.bd")

        self.tabs = QtWidgets.QTabWidget()
        self.date_tab = DateTab(self.calendar, self)
        self.tabs.addTab(self.date_tab, "Date")
        self.add_tab = AddTab(self.calendar, self.dates_update_funch)
        self.tabs.addTab(self.add_tab, "Add")
        self.settings_tab = SettignsTab(self)
        self.tabs.addTab(self.settings_tab, "Settings")

        self.setCentralWidget(self.tabs)

        self.set_settings()

        self.show()

    def set_settings(self):
        self.settigns = {}
        with open(SETTINGS_JSON, "r") as file:
            self.settings = json.load(file)
        qt_material.apply_stylesheet(self.app, self.settings["color_theme"])

    def dates_update_funch(self):
        self.date_tab = DateTab(self.calendar, self)
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, self.date_tab, "Date")
        self.tabs.setCurrentIndex(0)

        self.add_tab = AddTab(self.calendar, self.dates_update_funch)
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, self.add_tab, "Add")

    def update_date_tab(self):
        self.date_tab = DateTab(self.calendar, self)
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, self.date_tab, "Date")
        self.tabs.setCurrentIndex(0)

    def read_description(self, date):
        self.description_tab = ReadDescriptionTab(date, self)
        self.tabs.removeTab(0)
        self.tabs.insertTab(0, self.description_tab, "Description")
        self.tabs.setCurrentIndex(0)

    def out_description(self):
        self.dates_update_funch()

    def edit_date(self, date):
        self.edit_tab = EditTab(date, self.calendar, self.dates_update_funch)
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, self.edit_tab, "Edit")
        self.tabs.setCurrentIndex(1)


class DeleteDateDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("===")

        self.box = QtWidgets.QVBoxLayout()

        self.title = QtWidgets.QLabel()
        self.title.setText("Are you sure you want to remove this event")
        self.box.addWidget(self.title)

        buttons = QtWidgets.QDialogButtonBox.StandardButton.Cancel | QtWidgets.QDialogButtonBox.StandardButton.Ok

        self.btn = QtWidgets.QDialogButtonBox(buttons)
        self.btn.accepted.connect(self.accept)
        self.btn.rejected.connect(self.reject)
        self.box.addWidget(self.btn)

        self.setLayout(self.box)


class DateLayout(QtWidgets.QWidget):
    def __init__(self, date:  Date, calendar, window):
        super().__init__()

        self.lbl_box = QtWidgets.QHBoxLayout()
        self.setLayout(self.lbl_box)

        self.calendar = calendar
        self.date = date
        self.window = window

        self.icon_lbl = QtWidgets.QLabel()
        if date.icon is not None:
            icon_path = IMAGES_PATH + date.icon_name
            ic = QtGui.QImage(icon_path).scaled(20, 20)
            self.icon_lbl.setPixmap(QtGui.QPixmap.fromImage(ic))
        self.lbl_box.addWidget(self.icon_lbl, stretch=0)

        self.lbl = QtWidgets.QLabel()
        if len(str(date)) >= 33:
            self.lbl.setText(str(date)[:30] + "...")
        else:
            self.lbl.setText(str(date))
        self.lbl.setFixedHeight((date.description.count("\n") + 1) * 20)
        self.lbl_box.addWidget(self.lbl, stretch=1)

        self.edit_button = QtWidgets.QPushButton()
        self.edit_button.setText("E")
        self.edit_button.clicked.connect(self.edit_date)
        self.edit_button.setFixedSize(QSize(20, 20))
        self.edit_button.setToolTip("Edit event")
        self.lbl_box.addWidget(self.edit_button)

        self.description_button = QtWidgets.QPushButton()
        self.description_button.setText("D")
        self.description_button.clicked.connect(self.read_description)
        self.description_button.setFixedSize(QSize(20, 20))
        self.description_button.setToolTip("Read description")
        self.lbl_box.addWidget(self.description_button)

        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setText("X")
        self.delete_button.clicked.connect(self.delete_date)
        self.delete_button.setFixedSize(QSize(20, 20))
        self.delete_button.setToolTip("Delete event")
        self.lbl_box.addWidget(self.delete_button)

    def delete_date(self):
        if self.date.days_to <= 0:
            self.calendar.remove_date(self.date.id)
            self.close()
            return
        dialog_window = DeleteDateDialog()
        if dialog_window.exec():
            self.close()
            self.calendar.remove_date(self.date.id)

    def read_description(self):
        self.window.read_description(self.date)

    def edit_date(self):
        self.window.edit_date(self.date)


class DateTab(QtWidgets.QWidget):
    def __init__(self, calendar, window):
        super().__init__()
        self.box = QtWidgets.QVBoxLayout()
        self.my_window = window
        self.calendar = calendar

        self.category_widget = QtWidgets.QWidget()
        self.categories_box = QtWidgets.QHBoxLayout()

        self.title = QtWidgets.QLabel()
        today_qtdate = QtCore.QDate(QtCore.QDateTime.currentDateTime().date())
        self.title.setText(f"Today: {today_qtdate.toString()}")
        self.title.setFixedHeight(50)
        self.categories_box.addWidget(self.title, 2)

        self.categories_combobox = QtWidgets.QComboBox()
        with open(SETTINGS_JSON, "r") as file:
            self.settings = json.load(file)
        for e in self.settings["categories"]:
            self.categories_combobox.addItem(e)
        self.categories_combobox.activated.connect(self.change_category)
        self.categories_box.addWidget(self.categories_combobox)

        self.category_widget.setLayout(self.categories_box)
        self.box.addWidget(self.category_widget, 0,
                           alignment=Qt.AlignmentFlag.AlignTop)

        self.calendar = calendar

        self.date_widgets = []
        self.label = QtWidgets.QLabel()
        self.box.addWidget(self.label, 3)
        self.change_category()

        self.setLayout(self.box)

    def change_category(self):
        for e in self.date_widgets:
            self.box.removeWidget(e)
        self.date_widgets.clear()

        self.box.removeWidget(self.label)

        category = self.settings["categories"][self.categories_combobox.currentIndex(
        )]
        for date in sorted(self.calendar.all_dates, key=lambda d: d.days_to):
            if date.group != category and category not in ["_all", "_week", "_events"]:
                continue
            if category == "_week" and date.days_to > 7 and date.group != "_week":
                continue
            if category == "_events" and date.group == "_birthdays":
                continue
            w = DateLayout(date, self.calendar, self.my_window)
            self.date_widgets.append(w)
            self.box.addWidget(w,
                               0,  alignment=Qt.AlignmentFlag.AlignTop)
        self.box.addWidget(self.label, 3)
        self.update()


class ReadDescriptionTab(QtWidgets.QWidget):
    def __init__(self, date: Date, window):
        super().__init__()
        self.box = QtWidgets.QVBoxLayout()
        self.setLayout(self.box)

        self.window = window

        self.title = QtWidgets.QLabel()
        self.title.setText(
            f"Data:\n{date.day}.{date.mounth}.{date.year}\nTitle:\n{self.len_format_text(30, date.title)}")
        self.box.addWidget(self.title, 0)

        self.description = QtWidgets.QLabel()
        self.description.setText(
            "Description:\n" + self.len_format_text(30, date.description))
        self.box.addWidget(self.description, 0)

        self.stretch_label = QtWidgets.QLabel()
        self.box.addWidget(self.stretch_label, 5)

        self.other_info_label = QtWidgets.QLabel()
        self.other_info_label.setText("Other info\n" +
                                      f"ID: {date.id}\nGroup: {date.group}")
        self.box.addWidget(self.other_info_label, 0)

        self.out_button = QtWidgets.QPushButton()
        self.out_button.setText("out")
        self.out_button.clicked.connect(self.out)
        self.box.addWidget(self.out_button, 0,
                           alignment=Qt.AlignmentFlag.AlignBottom)

    @staticmethod
    def len_format_text(max_len, text):
        new_text = ""
        line = ""
        for i in text.replace("\n", " ").split():
            if len(i) > max_len:
                new_text += "\n" + line
                for j in range(math.ceil(len(i) / (max_len - 1))):
                    new_text += "\n" + \
                        i[j * (max_len - 1): (j + 1) * (max_len - 1)] + "-"
                new_text = new_text[:-1]
                line = ""
            elif len(line + i + " ") > max_len:
                new_text += "\n" + line
                line = i
            else:
                line += " " + i if line != "" else i
        if line != "":
            new_text += "\n" + line
        return new_text

    def out(self):
        self.window.out_description()


class AddTab(QtWidgets.QWidget):
    def __init__(self, calendar: Calendar, dates_update_funch):
        super().__init__()
        self.box = QtWidgets.QVBoxLayout()

        self.calendar = calendar
        self.dates_update_funch = dates_update_funch

        self.title_label = QtWidgets.QLabel()
        self.title_label.setText("Add event")
        self.box.addWidget(self.title_label, 0)

        self.date_calendar = QtWidgets.QCalendarWidget()
        self.date_calendar.clicked.connect(self.choose_date)
        self.box.addWidget(self.date_calendar, 0)

        self.date = self.date_calendar.selectedDate()

        self.date_and_category_box = QtWidgets.QHBoxLayout()
        self.date_and_category_widget = QtWidgets.QWidget()
        self.date_and_category_widget.setLayout(self.date_and_category_box)
        self.date_label = QtWidgets.QLabel()
        self.date_and_category_box.addWidget(self.date_label, 3)
        self.category_combobox = QtWidgets.QComboBox()
        with open(SETTINGS_JSON, "r") as file:
            self.settings = json.load(file)
        self.category_combobox.addItems(self.settings["categories"])
        self.category_combobox.setCurrentIndex(0)
        self.date_and_category_box.addWidget(self.category_combobox)
        self.box.addWidget(self.date_and_category_widget, 0)
        self.choose_date(self.date)

        self.title_layout = QtWidgets.QLabel()
        self.title_layout.setText("Title:")
        self.box.addWidget(self.title_layout, 0)

        self.title_text = QtWidgets.QLineEdit()
        self.title = ""
        self.title_text.textChanged.connect(self.set_title)
        self.box.addWidget(self.title_text, 1)

        self.icon_layout = QtWidgets.QLabel()
        self.icon_layout.setText("Icon:")
        self.box.addWidget(self.icon_layout)

        self.icon_combobox = IconComboBox()
        self.box.addWidget(self.icon_combobox)

        self.description_layout = QtWidgets.QLabel()
        self.description_layout.setText("Description:")
        self.box.addWidget(self.description_layout, 0)

        self.description_text = QtWidgets.QTextEdit()
        self.description_text.setText("")
        self.description = ""
        self.description_text.textChanged.connect(self.set_description)
        self.box.addWidget(self.description_text, -1)

        self.add_button = QtWidgets.QPushButton()
        self.add_button.setText("ADD")
        self.add_button.clicked.connect(self.add)
        self.box.addWidget(self.add_button)

        self.setLayout(self.box)

    def choose_date(self, date: QtCore.QDate):
        self.date = date
        self.date_label.setText(
            f"Date:\n{date.day()}.{date.month()}.{date.year()}")

    def set_description(self):
        self.description = self.description_text.toPlainText()

    def set_title(self):
        self.title = self.title_text.text()

    def add(self):
        self.calendar.add_date(Date(self.date.day(), self.date.month(),
                                    self.date.year(), self.title, self.description, icon=self.icon_combobox.currentText(),
                                    group=self.settings["categories"][self.category_combobox.currentIndex()]))
        self.dates_update_funch()


class EditTab(AddTab):
    def __init__(self, date: Date, calendar, dates_update_funch):
        super().__init__(calendar, dates_update_funch)

        self.edit_date_date = date

        self.title_label.setText("Edit event")
        d = QtCore.QDate()
        d.setDate(date.year, date.mounth, date.day)
        self.date_calendar.setSelectedDate(d)
        self.choose_date(d)
        if date.icon_name in self.icon_combobox.icons:
            self.icon_combobox.setCurrentIndex(
                self.icon_combobox.icons.index(date.icon_name))
        self.add_button.setText("Edit")
        self.title_text.setText(date.title)
        self.description_text.setText(date.description)

        self.category_combobox.setCurrentIndex(
            self.settings["categories"].index(date.group))

        self.dancel_button = QtWidgets.QPushButton()
        self.dancel_button.setText("Dancel")
        self.dancel_button.clicked.connect(self.dancel)
        self.box.addWidget(self.dancel_button)

    def add(self):
        self.calendar.remove_date(self.edit_date_date.id)
        super().add()

    def dancel(self):
        self.dates_update_funch()


class IconComboBox(QtWidgets.QComboBox):
    def __init__(self):
        super().__init__()

        icons = self.icons

        for icon in icons:
            self.addItem(QtGui.QIcon(IMAGES_PATH + icon), icon)

    @property
    def icons(self):
        return ICONS


class SettignsTab(QtWidgets.QWidget):
    def __init__(self, my_window):
        super().__init__()
        self.my_window = my_window
        self.layout = QtWidgets.QVBoxLayout()

        self.title = QtWidgets.QLabel()
        self.title.setText("Settings")
        self.layout.addWidget(self.title)

        self.settigns = {}
        with open(SETTINGS_JSON, "r") as file:
            self.settigns = json.load(file)

        self.theme_label = QtWidgets.QLabel("Color theme:")
        self.layout.addWidget(self.theme_label)

        self.theme_combobox = QtWidgets.QComboBox()
        self.layout.addWidget(self.theme_combobox)

        for e in qt_material.list_themes():
            self.theme_combobox.addItem(e)
        self.theme_combobox.setCurrentIndex(
            qt_material.list_themes().index(self.settigns["color_theme"]))

        self.field_widget = QtWidgets.QWidget()
        self.layout.addWidget(self.field_widget, 3)

        self.theme_button = QtWidgets.QPushButton()
        self.theme_button.setText("Appy")
        self.theme_button.clicked.connect(self.change_theme)
        self.layout.addWidget(self.theme_button)

        self.setLayout(self.layout)

    def change_theme(self):
        self.settigns["color_theme"] = self.theme_combobox.itemText(
            self.theme_combobox.currentIndex())
        with open(SETTINGS_JSON, "w") as file:
            json.dump(self.settigns, file)
        self.my_window.set_settings()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MyWindow(app)

    app.exec()
