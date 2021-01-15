# Student Rosters
# Austin Arnett
# 
# Read a list of the entire student roster and display it in the window.
# Allow the user to filter based on classes and status

import urllib.request
import sys
import re
import os
from pathlib import Path

# Qt includes
from PyQt5.QtWidgets import (QApplication, QWidget)
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem)
from PyQt5.QtWidgets import (QPushButton, QLabel, QComboBox, QMenuBar, QAction, QDialog, QDialogButtonBox)
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QGridLayout)
from PyQt5.QtGui import (QColor)
from PyQt5.QtCore import (Qt, pyqtSlot)

# Accessing test roster
from github import Github

# Column Indices
LAST_NAME = 0
FIRST_NAME = 1
STATUS = 2
COLUMN_COUNT = 3

# Const string definitions
LABELS = ["Last Name", "First Name", "Status", "Change Status"]

# Title for each class
FIRST_LABEL = "1st Period"
SECOND_LABEL = "2nd Period"
THIRD_LABEL = "3rd Period"
FOURTH_LABEL = "4th Period"
FIFTH_LABEL = "5th Period"
SIXTH_LABEL = "6th Period"
SEVENTH_LABEL = "7th Period"

# Student Status
UNKNOWN_LABEL = "Unknown"
IN_LABEL = "In-Person"
ONLINE_LABEL = "Online"

# Class to display
CURRENT_CLASS = "1"

# Filters
UNKNOWN = "U"
IN = "I"
ONLINE = "O"
ALL = "A"
CURRENT_FILTER = ALL

# Github information
USERNAME = "<username>"
PASSWORD = "<password>"


STUDENT_DATA = ""

# Status indices for the combo box
UNKNOWN_INDEX = 0
IN_INDEX = 1
ONLINE_INDEX = 2

# Highlight color for online students
ONLINE_COLOR = QColor(125,213,240)

# Track unsaved changes
CHANGES_MADE = False

# Main Window
class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        self.setWindowTitle("Student Rosters")
        
        # Set up Menu
        menu = QMenuBar()
        
        # File Menu
        fileActions = menu.addMenu("File")
        save = fileActions.addAction("Save")
        save.triggered.connect(self.saveClicked)
        exitAction = fileActions.addAction("Exit")
        exitAction.triggered.connect(self.exitClicked)
        
        # Class Menu
        classActions = menu.addMenu("Class")
        first = classActions.addAction("1st Period")
        second = classActions.addAction("2nd Period")
        # Hide third period since it is a conference period and has no students
        #third = classActions.addAction("3rd Period")
        fourth = classActions.addAction("4th Period")
        fifth = classActions.addAction("5th Period")
        sixth = classActions.addAction("6th Period")
        seventh = classActions.addAction("7th Period")
        
        # Set up connections
        first.triggered.connect(self.firstClicked)
        second.triggered.connect(self.secondClicked)
        #third.triggered.connect(self.thirdClicked)
        fourth.triggered.connect(self.fourthClicked)
        fifth.triggered.connect(self.fifthClicked)
        sixth.triggered.connect(self.sixthClicked)
        seventh.triggered.connect(self.seventhClicked)
        
        # Filter Menu
        filterMenu = menu.addMenu("Filters")
        unknown = filterMenu.addAction("Unknown")
        unknown.triggered.connect(self.unknownClicked)
        inperson = filterMenu.addAction("In-person")
        inperson.triggered.connect(self.inpersonClicked)
        online = filterMenu.addAction("Online")
        online.triggered.connect(self.onlineClicked)
        clearFilters = filterMenu.addAction("Clear Filters")
        clearFilters.triggered.connect(self.clearFiltersClicked)
        
        # Class Period Label
        self.classLabel = QLabel(FIRST_LABEL)
        self.classLabel.setAlignment(Qt.AlignCenter)
        
        # Student Table
        self.table = QTableWidget()
        self.table.setColumnCount(COLUMN_COUNT)
        self.table.setHorizontalHeaderLabels(LABELS)
        
        # Export Online Students
        exportOnlineButton = QPushButton("Export Online Students")
        exportOnlineButton.pressed.connect(self.createOnlineStudentSpreadsheet)
        
        # Add widgets to the window
        self.layout = QGridLayout()
        self.layout.addWidget(menu, 0, 0)
        self.layout.addWidget(self.classLabel, 1, 0)
        self.layout.addWidget(self.table, 2, 0)
        self.layout.addWidget(exportOnlineButton, 3, 0)
        self.setLayout(self.layout)
        
        try:
            # Set up and connect to the github test repo
            self.github = Github(USERNAME, PASSWORD)
            self.repo = self.github.get_repo("<repo_name>")
        
            # Download the student data from the repo and load it into the table
            self.loadData()
        except:
            print("Could not connect to github repository")
        
    # Override for save dialog
    def closeEvent(self, event):
        global CHANGES_MADE
        
        if(CHANGES_MADE):
            self.saveDialog()
        
        event.accept()
        
    # Save menu item clicked
    def saveClicked(self):
        global STUDENT_DATA
        global CHANGES_MADE
        global CURRENT_FILTER
        
        # Iterate through the rows and gather the data to save
        for row in range(0, self.table.rowCount()):
            original = self.table.item(row, 0).text()
            replacement = self.table.item(row, 0).text()
            original += "," + self.table.item(row, 1).text()
            replacement += "," + self.table.item(row, 1).text()
            original += "," + CURRENT_CLASS
            replacement += "," + CURRENT_CLASS
            original += ",."
            
            status = self.table.cellWidget(row, 2).currentText()
            
            if(status == UNKNOWN_LABEL):
                replacement += ",U"
            elif(status == IN_LABEL):
                replacement += ",I"
            elif(status == ONLINE_LABEL):
                replacement += ",O"
            
            # Find the original line for the student and replace it
            STUDENT_DATA = re.sub(original, replacement, STUDENT_DATA)            
        
        try:
            # Update the test data repository
            contents = self.repo.get_contents("<file_name>")
            self.repo.update_file(contents.path, "Updating student info", STUDENT_DATA, contents.sha)
        
            CHANGES_MADE = False
            self.loadData(CURRENT_FILTER)
        except:
            print("Could not commit changes to repository")
        
        
    # Create and launch the save dialog
    def saveDialog(self):
        self.dialog = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint )
        self.dialog.setWindowTitle("Save changes?")
        button = QDialogButtonBox.Yes | QDialogButtonBox.No
        buttonBox = QDialogButtonBox(button)
        buttonBox.accepted.connect(self.saveDialogClicked)
        buttonBox.rejected.connect(self.cancelDialogClicked)
        dialogLayout = QVBoxLayout()
        dialogLayout.addWidget(buttonBox)
        self.dialog.setLayout(dialogLayout)
        self.dialog.setMinimumSize(300, 75)
        self.dialog.exec()
    
    
    # User clicked save
    def saveDialogClicked(self):
        self.dialog.close()
        self.saveClicked()
        
        
    # User clicked cancel or closed the window
    def cancelDialogClicked(self):
        self.dialog.close()
        
        
    # User tried to close the window
    def exitClicked(self):
        global CHANGES_MADE
        
        if(CHANGES_MADE):
            self.saveDialog()
        sys.exit()
        
        
    # Display first period
    def firstClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
        
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "1"
        self.loadData()
        
    
    # Display second period
    def secondClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "2"
        self.loadData()
        
    
    # Display third period
    def thirdClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "3"
        self.loadData()
        
    
    # Display fourth period
    def fourthClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "4"
        self.loadData()
        
    
    # Display fifth period
    def fifthClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "5"
        self.loadData()
        
    
    # Display sixth period
    def sixthClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "6"
        self.loadData()
        
    
    # Display seventh period
    def seventhClicked(self):
        global CURRENT_CLASS
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        CURRENT_CLASS = "7"
        self.loadData()
        
    
    # Display only unknown status students
    def unknownClicked(self):
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = UNKNOWN
        self.loadData(UNKNOWN)
        
       
    # Display only In persion students
    def inpersonClicked(self):
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = IN
        self.loadData(IN)
        
        
    # Display only Online students
    def onlineClicked(self):
        global CHANGES_MADE
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ONLINE
        self.loadData(ONLINE)
        
    
    # Clear all filters
    def clearFiltersClicked(self):
        global CHANGES_MADE
        global CURRENT_FILTER
        
        if(CHANGES_MADE):
            self.saveDialog()
            
        CURRENT_FILTER = ALL
        self.loadData()
        
     
    # Grab the test file
    def getStudentListUrl(self):
        contents = self.repo.get_contents("<file_name>")
        return contents.download_url
        
        
    # Get the label based on the current type
    def getStatus(self, type):
        if(type == "I"):
            return IN_LABEL
        elif(type == "O"):
            return ONLINE_LABEL
        return UNKNOWN_LABEL
        
        
    # Create and display the export confirmation
    def okayDialog(self):
        self.okayDialog = QDialog(None, Qt.WindowSystemMenuHint | Qt.WindowTitleHint )
        self.okayDialog.setWindowTitle("Names Exported to Desktop")
        button = QDialogButtonBox.Ok
        buttonBox = QDialogButtonBox(button)
        buttonBox.accepted.connect(self.okayDialogClicked)
        dialogLayout = QHBoxLayout()
        dialogLayout.addWidget(buttonBox)
        self.okayDialog.setLayout(dialogLayout)
        self.okayDialog.setMinimumSize(450, 60)
        self.okayDialog.exec()
        
        
    # Close the dialog when the button is pressed
    def okayDialogClicked(self):
        self.okayDialog.close()
        

    # Export all online students to a spreadshet
    def createOnlineStudentSpreadsheet(self):
        try:
            url = self.getStudentListUrl()
        
            output = "Last Name,First Name,Present\n"
        
            for student in urllib.request.urlopen(url):
                student_info = student.decode().split(',')
                        
                if(student_info[3].strip() == "O"):
                    output += student_info[0].strip() + "," + student_info[1].strip() + "\n"
                
            home = str(Path.home())
            file_location = os.path.join(home, "Desktop", "<file_name>")
            file = open(file_location, 'w')
            file.write(output)
            file.close()
            self.okayDialog()
        except:
            print("Saving online student roster failed")
            

    # Change value of item changed
    def itemChanged(self):
        global CHANGES_MADE
        CHANGES_MADE = True
        
        
    # Get the data from github and load into the table
    def loadData(self, filter_type = ALL):
        global CURRENT_CLASS
        global STUDENT_DATA
        global CHANGES_MADE
        
        # Set the table title based on the current filter
        if(filter_type == UNKNOWN):
            self.classLabel.setText("Unknown Students")
        elif(filter_type == IN):
            self.classLabel.setText("In-person Students")
        elif(filter_type == ONLINE):
            self.classLabel.setText("Online Students")
        elif(CURRENT_CLASS == "1"):
            self.classLabel.setText(FIRST_LABEL)
        elif(CURRENT_CLASS == "2"):
            self.classLabel.setText(SECOND_LABEL)
        elif(CURRENT_CLASS == "3"):
            self.classLabel.setText(THIRD_LABEL)
        elif(CURRENT_CLASS == "4"):
            self.classLabel.setText(FOURTH_LABEL)
        elif(CURRENT_CLASS == "5"):
            self.classLabel.setText(FIFTH_LABEL)
        elif(CURRENT_CLASS == "6"):
            self.classLabel.setText(SIXTH_LABEL)
        elif(CURRENT_CLASS == "7"):
            self.classLabel.setText(SEVENTH_LABEL)
        

        try:
            url = self.getStudentListUrl()
        except:
            print("Could not connect to github repository")
                        
        # Remove everything from the table
        self.table.clearContents()
        while(self.table.rowCount() > 0):
            self.table.removeRow(0)
        
        STUDENT_DATA = ""
    
        studentCount = 0
        
        try:
            # Iterate through students adding them to the table if they match the filters
            for student in urllib.request.urlopen(url):
                # Add student to the master list to upload if we save
                STUDENT_DATA += student.decode()
            
                # Split up the data (last name, first name, class, status)
                student_info = student.decode().split(',')

                # There is a filter applied
                if(filter_type != ALL):
                    student_status = student_info[3].strip()
                
                    if(filter_type == student_status):
                        # Insert row
                        self.table.insertRow(studentCount)
                    
                        # Student Name
                        lastItem = QTableWidgetItem(student_info[0].strip())
                        lastItem.setFlags(Qt.ItemIsEnabled)
                        self.table.setItem(studentCount, LAST_NAME, lastItem)
                        firstItem = QTableWidgetItem(student_info[1].strip())
                        firstItem.setFlags(Qt.ItemIsEnabled)
                        self.table.setItem(studentCount, FIRST_NAME, firstItem)
                    
                        # Status
                        student_status = student_info[3].strip()
                            
                        comboBox = QComboBox()
                        comboBox.addItems([UNKNOWN_LABEL, IN_LABEL, ONLINE_LABEL])
                            
                        if(student_status == UNKNOWN):
                            comboBox.setCurrentIndex(UNKNOWN_INDEX)
                        elif(student_status == IN):
                            comboBox.setCurrentIndex(IN_INDEX)
                        else:
                            comboBox.setCurrentIndex(ONLINE_INDEX)
                            self.table.item(studentCount, 0).setBackground(ONLINE_COLOR)
                            self.table.item(studentCount, 1).setBackground(ONLINE_COLOR)

                        comboBox.currentIndexChanged.connect(self.itemChanged)
                        self.table.setCellWidget(studentCount, STATUS, comboBox)
                        
                        studentCount += 1
                
                # Show all students for the class
                elif(student_info[2].strip() == CURRENT_CLASS):
                    # Insert Row
                    self.table.insertRow(studentCount)
                    
                    # Student Name
                    lastItem = QTableWidgetItem(student_info[0].strip())
                    lastItem.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(studentCount, LAST_NAME, lastItem)
                    firstItem = QTableWidgetItem(student_info[1].strip())
                    firstItem.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(studentCount, FIRST_NAME, firstItem)
                
                    # Status (Online, In-person, Unknown)
                    student_status = student_info[3].strip()
                                    
                    # Status
                    comboBox = QComboBox()
                    comboBox.addItems([UNKNOWN_LABEL, IN_LABEL, ONLINE_LABEL])
                                
                    if(student_status == UNKNOWN):
                        comboBox.setCurrentIndex(UNKNOWN_INDEX)
                    elif(student_status == IN):
                        comboBox.setCurrentIndex(IN_INDEX)
                    elif(student_status == ONLINE):
                        comboBox.setCurrentIndex(ONLINE_INDEX)
                        self.table.item(studentCount, 0).setBackground(ONLINE_COLOR)
                        self.table.item(studentCount, 1).setBackground(ONLINE_COLOR)
                
                    comboBox.currentIndexChanged.connect(self.itemChanged)
                    self.table.setCellWidget(studentCount, STATUS, comboBox) 

                    studentCount += 1
            CHANGES_MADE = False
        except:
            print("Could not load student information")


# Main - Start the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    widget = MainWindow()
    widget.resize(800, 900)
    widget.show()
    
    sys.exit(app.exec_())