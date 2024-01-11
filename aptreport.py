import sys
import logging
from functools import partial
from openpyxl.styles import Font
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtGui import QStandardItemModel, QKeySequence
from PyQt5.QtWidgets import QDialog, QMessageBox, QMenu, QShortcut
from PyQt5.QtCore import Qt
from datetime import datetime
from commonmd import *
#<--for non_ui version-->
#from aptreport_ui import UI_AptReportDialog

# customer table contents -----------------------------------------------------
class AptReportDialog(QDialog, SubWindowBase):
#for non_ui version-------------------------
#class AptReportDialog(QDialog, UI_AptReportDialog, SubWindowBase):

    def __init__(self, current_username = None, current_datetime = None):
        super().__init__()

        self.conn, self.cursor = connect_to_database4()

        # Load ui file
        uic.loadUi("aptreport.ui", self)
        #for non_ui version-------------------------
        #self.setupUi(self)

        # Add window flags
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)  

        # Initialize current_username and current_datetime directly
        self.current_username, self.current_datetime = initialize_username_and_datetime(current_username, current_datetime)

        # Enable automatic deletion on close
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  

        # Create tv_aptreport and QSortFilterProxyModel
        self.model = QStandardItemModel()
        self.proxy_model = NumericStringSortModel(self.model)
        self.proxy_model.setSourceModel(self.model)

        # Define the column types
        column_types = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",]
        
        # Set the custom delegate for the specific column
        delegate = NumericDelegate(column_types, self.tv_aptreport)
        self.tv_aptreport.setItemDelegate(delegate)
        self.tv_aptreport.setModel(self.proxy_model)
       
        # Enable sorting
        self.tv_aptreport.setSortingEnabled(True)

        # Enable alternating row colors
        self.tv_aptreport.setAlternatingRowColors(True)  
        
        # Hide the first index column
        self.tv_aptreport.verticalHeader().setVisible(False)

        # While selecting row in tv_aptreport, each cell values to displayed to designated widgets
        self.tv_aptreport.clicked.connect(self.show_selected_data)

        # Fill combobox items when the application starts
        self.get_combobox_contents()

        # Initiate display of data
        self.make_data()
        self.conn_button_to_method()
        self.connect_signal_slot()

        # Set tab order for input widgets
        self.set_tab_order()

        # Initiate CTRL+C, CTRL+V and ENTER
        self.setup_shortcuts()

        # Automatically input current date
        self.display_currentdate()

        # Disable buttons
        self.disablePushButton()

        # Make log file
        self.make_logfiles("access_aptreport.log")

    # Disable Pushbutton
    def disablePushButton(self):
        self.pb_aptreport_insert.setEnabled(False)
        self.pb_aptreport_update.setEnabled(False)
        self.pb_aptreport_delete.setEnabled(False)

    # Create a shortcut for CTRL+C/CTRL+V/ Return key
    def setup_shortcuts(self):
        self.copy_shortcut = QShortcut(QKeySequence.Copy, self.tv_aptreport, partial(self.copy_cells, self.tv_aptreport))
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self.tv_aptreport, partial(self.paste_cells, self.tv_aptreport))
        self.return_shortcut = QShortcut(Qt.Key_Return, self.tv_aptreport, partial(self.handle_return_key, self.tv_aptreport))

    # Call process_key_event and pass the event and your QTableWidget instance
    def keyPressEvent(self, event):
        tv_widget = self.tv_aptreport
        self.process_key_event(event, tv_widget)

    # Display current date only
    def display_currentdate(self):
        ddt, ddt_1 = disply_date_info()
        self.entry_aptreport_eefffrom.setText(ddt)
        self.entry_aptreport_eeffthru.setText(ddt_1)

    # Pass combobox info and sql to next method
    def get_combobox_contents(self):
        self.insert_combobox_initiate(self.cb_aptreport_aname, "SELECT DISTINCT adesc FROM apt_master ORDER BY adesc")
        self.insert_combobox_initiate(self.cb_aptreport_apttypename, "SELECT DISTINCT description FROM apt_type")
        self.insert_combobox_initiate(self.cb_aptreport_customername, "SELECT DISTINCT cdescription FROM apt_customer")
        self.insert_combobox_initiate(self.cb_aptreport_sjname, "SELECT DISTINCT cdesc FROM apt_cic_master ORDER BY cdesc")
        self.insert_combobox_initiate(self.cb_aptreport_ename, "SELECT ename FROM employee WHERE class1 <> 'r' ORDER BY ename")

    # Initiate Combo_Box 
    def insert_combobox_initiate(self, combo_box, sql_query):
        self.combobox_initializing(combo_box, sql_query) # using common module
        self.lbl_aptreport_id.setText("")
        self.entry_aptreport_acode.setText("")
        self.cb_aptreport_aname.setCurrentIndex(0) 
        self.cb_aptreport_apttypename.setCurrentIndex(0)
        self.cb_aptreport_customername.setCurrentIndex(0)
        self.cb_aptreport_sjname.setCurrentIndex(0)
        self.cb_aptreport_ename.setCurrentIndex(0)

    # Connect the button to the method
    def conn_button_to_method(self):
        self.pb_aptreport_show.clicked.connect(self.make_data)
        self.pb_aptreport_show_con.clicked.connect(self.make_data_con)
        self.pb_aptreport_search.clicked.connect(self.search_data)
        self.pb_aptreport_clear_data.clicked.connect(self.clear_data)
        self.pb_aptreport_close.clicked.connect(self.close_dialog)

        self.pb_aptreport_insert.clicked.connect(self.tb_insert)
        self.pb_aptreport_update.clicked.connect(self.tb_update)
        self.pb_aptreport_delete.clicked.connect(self.tb_delete)

    # Connect Signal to Slot
    def connect_signal_slot(self):
        self.cb_aptreport_aname.activated.connect(self.cb_aptreport_aname_changed)        
        self.cb_aptreport_customername.activated.connect(self.cb_aptreport_customername_changed)
        self.cb_aptreport_sjname.activated.connect(self.cb_aptreport_sjname_changed)
        self.cb_aptreport_ename.activated.connect(self.cb_aptreport_ename_changed)

    # Tab order for sub window
    def set_tab_order(self):
        widgets = [self.pb_aptreport_show, self.entry_aptreport_acode, self.cb_aptreport_aname,
            self.entry_aptreport_noh, self.entry_aptreport_apttypecode, self.cb_aptreport_apttypename,
            self.entry_aptreport_ciccode, self.entry_aptreport_customercode, self.cb_aptreport_customername,
            self.entry_aptreport_sjcode, self.cb_aptreport_sjname, self.entry_aptreport_contractvalue,
            self.entry_aptreport_cefffrom, self.entry_aptreport_ceffthru, self.entry_aptreport_ecode,
            self.cb_aptreport_ename, self.entry_aptreport_payment, self.entry_aptreport_eefffrom,
            self.entry_aptreport_eeffthru, self.entry_aptreport_remark, self.pb_aptreport_show_con,
            self.pb_aptreport_search, self.pb_aptreport_clear_data, self.pb_aptreport_close,
            self.pb_aptreport_insert, self.pb_aptreport_update , self.pb_aptreport_delete]

        for i in range(len(widgets) - 1):
            self.setTabOrder(widgets[i], widgets[i + 1])

    # To reduce duplications
    def common_query_statement(self):
        tv_widget = self.tv_aptreport
        self.cursor.execute("Select * From vw_apt_report WHERE 1=0")
        column_info = self.cursor.description
        column_names = [col[0] for col in column_info]

        sql_query = "Select * From vw_apt_report order by id"
        column_widths = [80, 100, 250, 100, 100, 100, 100, 120, 120, 120, 120, 120]

        return sql_query, tv_widget, column_info, column_names, column_widths 

    # Make table data
    def make_data(self):
        sql_query, tv_widget, column_info, column_names, column_widths = self.common_query_statement() 
        self.populate_dialog(self.cursor, sql_query, tv_widget, column_info, column_names,column_widths)

    # Make table data
    def make_data_con(self):
        query = "Select * From vw_apt_report Where id IS NOT NULL order by id"
        column_widths1 = [80, 100, 250, 100, 100, 100, 100, 120, 120, 120, 120, 120]

        sql_query, tv_widget, column_info, column_names, column_widths = self.common_query_statement() 
        self.populate_dialog(self.cursor, query, tv_widget, column_info, column_names,column_widths1)

    # Get the value of other variables
    def get_aptreport_input(self):
        kaptcode = str(self.entry_aptreport_acode.text())
        ecode = int(self.entry_aptreport_ecode.text())
        efffrom = str(self.entry_aptreport_eefffrom.text())
        effthru = str(self.entry_aptreport_eeffthru.text())
        #payment = int(self.entry_aptreport_payment.text())
        #payment = float(self.entry_aptreport_payment.text()) if self.entry_aptreport_payment.text().replace(".", "").isdigit() else 0
        input_val = self.entry_aptcontract_contractvalue.text()
        if input_val.replace(".", "").replace("-", "").isdigit():
            payment = float(input_val)
        else:
            payment = 0        
        
        remark = str(self.entry_aptreport_remark.text())
        return kaptcode, ecode, efffrom, effthru, payment, remark

    # Make Common values set
    def common_values_set(self):
        username = self.current_username
        user_id = self.userID_gen(username)
        formatted_datetime = self.dt_time_info()
        return username, user_id, formatted_datetime

    # insert new product data to MySQL table
    def tb_insert(self):
        confirm_dialog = self.show_insert_confirmation_dialog()
        
        if confirm_dialog == QMessageBox.Yes:
            idx = self.max_row_id("apt_contract_pic")
            username, user_id, formatted_datetime = self.common_values_set()
            kaptcode, ecode, efffrom, effthru, payment, remark = self.get_aptreport_input() 

            if (idx>0 and ecode>0) and all(len(var) > 0 for var in (kaptcode, efffrom, effthru)):
                self.cursor.execute('''INSERT INTO apt_contract_pic (id, acode, ecode, efffrom, effthru, payment, trx_date, userid, remark) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                            , (idx, kaptcode, ecode, efffrom, effthru, payment, formatted_datetime, user_id, remark))
                self.conn.commit()
                self.show_insert_success_message()
                self.refresh_data() 
                logging.info(f"User {username} inserted {idx} row to the apt contract pic table.")
            else:
                self.show_missing_message("입력 이상")
                return
        else:
            self.show_cancel_message("데이터 추가 취소")
            return    

    # revise the values in the selected row
    def tb_update(self):
        confirm_dialog = self.show_update_confirmation_dialog()

        if confirm_dialog == QMessageBox.Yes:
            username, user_id, formatted_datetime = self.common_values_set()
            kaptcode, ecode, efffrom, effthru, payment, remark = self.get_aptreport_input() 

            if self.lbl_aptreport_id.text() == 'None':
                idx = int(self.max_row_id("apt_contract_pic"))
                
                if (idx>0 and ecode>0) and all(len(var) > 0 for var in (kaptcode, efffrom, effthru)):
                    self.cursor.execute('''INSERT INTO apt_contract_pic (id, acode, ecode, efffrom, effthru, payment, trx_date, userid, remark) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
                                , (idx, kaptcode, ecode, efffrom, effthru, payment, formatted_datetime, user_id, remark))                
                else:
                    self.show_missing_message("입력 이상")
                    return
            else:
                idx = int(self.lbl_aptreport_id.text())
                if (idx>0 and ecode>0) and all(len(var) > 0 for var in (kaptcode, efffrom, effthru)):
                    self.cursor.execute('''UPDATE apt_contract_pic SET 
                                acode=?, ecode=?, efffrom=?, effthru=?, payment=?, trx_date=?, userid=?, remark=? WHERE id=?'''
                                , (kaptcode, ecode, efffrom, effthru, payment, formatted_datetime, user_id, remark, idx))
                else:
                    self.show_missing_message("입력 이상")
                    return
            self.conn.commit()
            self.show_update_success_message()
            self.refresh_data()
            logging.info(f"User {username} updated row number {idx} in the apt contract pic table.")
        else:
            self.show_cancel_message("데이터 변경 취소")
            return

    # delete row according to id selected
    def tb_delete(self):
        confirm_dialog = self.show_delete_confirmation_dialog()

        if confirm_dialog == QMessageBox.Yes:
            idx = self.lbl_aptreport_id.text()
            username, user_id, formatted_datetime = self.common_values_set()
            self.cursor.execute("DELETE FROM apt_contract_pic WHERE id=?", (idx,))
            self.conn.commit()
            self.show_delete_success_message()
            self.refresh_data()
            logging.info(f"User {username} deleted {idx} row to the apt contract pic table.")
        else:
            self.show_cancel_message("데이터 삭제 취소")
            return

    # Search data
    def search_data(self):

        aptname = self.cb_aptreport_aname.currentText()
        cusname = self.cb_aptreport_customername.currentText()
        sjname= self.cb_aptreport_sjname.currentText()
        pic = self.cb_aptreport_ename.currentText()

        conditions = {'v01': (aptname, "adesc like '%{}%'"), 'v02': (cusname, "cdescription='{}'"), 'v03': (sjname, "cdesc='{}'"), 
                      'v04': (pic, "ename='{}'"),}

        selected_conditions = []

        for key, (value, condition_format) in conditions.items():
            if len(value) > 0:
                selected_conditions.append(condition_format.format(value))

        if not selected_conditions:
            QMessageBox.about(self, "검색 조건 확인", "검색 조건이 비어 있습니다!")
            return

        # Join the selected conditions to form the SQL query
        query = f"SELECT * FROM vw_apt_report WHERE {' AND '.join(selected_conditions)} ORDER BY adesc"

        QMessageBox.about(self, "검색 조건 확인", f"아파트명: {aptname} \n거래처이름: {cusname} \n수제담당회사명: {sjname} \n담당자명: {pic} \n\n위 조건으로 검색을 수행합니다!")

        sql_query, tv_widget, column_info, column_names, column_widths = self.common_query_statement() 
        self.populate_dialog(self.cursor, query, tv_widget, column_info, column_names,column_widths)

    # Combobox apt name index changed
    def cb_aptreport_aname_changed(self):
        self.entry_aptreport_acode.clear()
        selected_item = self.cb_aptreport_aname.currentText()

        if selected_item:
            query = f"SELECT DISTINCT acode From apt_master WHERE adesc ='{selected_item}'"
            line_edit_widgets = [self.entry_aptreport_acode]
        
            # Check if any line edit widgets are provided
            if line_edit_widgets:
                self.lineEdit_contents(line_edit_widgets, query)
            else:
                pass

    # Combobox customer index changed
    def cb_aptreport_customername_changed(self):
        self.entry_aptreport_customercode.clear()
        selected_item = self.cb_aptreport_customername.currentText()

        if selected_item:
            query = f"SELECT DISTINCT taxid From apt_customer WHERE cdescription ='{selected_item}'"
            line_edit_widgets = [self.entry_aptreport_customercode]
        
            # Check if any line edit widgets are provided
            if line_edit_widgets:
                self.lineEdit_contents(line_edit_widgets, query)
            else:
                pass

    # Combobox suje index changed
    def cb_aptreport_sjname_changed(self):
        self.entry_aptreport_sjcode.clear()
        selected_item = self.cb_aptreport_sjname.currentText()

        if selected_item:
            query = f"SELECT DISTINCT code From apt_cic_master WHERE cdesc ='{selected_item}'"
            line_edit_widgets = [self.entry_aptreport_sjcode]
        
            # Check if any line edit widgets are provided
            if line_edit_widgets:
                self.lineEdit_contents(line_edit_widgets, query)
            else:
                pass

    # Combobox suje index changed
    def cb_aptreport_ename_changed(self):
        self.entry_aptreport_ecode.clear()
        selected_item = self.cb_aptreport_ename.currentText()

        if selected_item:
            query = f"SELECT DISTINCT ecode From employee WHERE ename ='{selected_item}'"
            line_edit_widgets = [self.entry_aptreport_ecode]
        
            # Check if any line edit widgets are provided
            if line_edit_widgets:
                self.lineEdit_contents(line_edit_widgets, query)
            else:
                pass

    # clear input field entry
    def clear_data(self):
        self.lbl_aptreport_id.setText("")
        clear_widget_data(self)

        self.display_currentdate()                
        self.entry_aptreport_contractvalue.setText("0")
        self.entry_aptreport_payment.setText("0")

    # table widget cell double click
    def show_selected_data(self, item):
        # Get the row index of the clicked item
        row_index = item.row()

        # Initialize a list to store the cell values
        cell_values = []

        # Loop through the columns and retrieve the text from each cell
        for column_index in range(20):  # 20columns
            cell_text = self.tv_aptreport.model().item(row_index, column_index).text()
            cell_values.append(cell_text)
            
        # Populate the input widgets with the data from the selected row
        self.lbl_aptreport_id.setText(cell_values[0])
        self.entry_aptreport_acode.setText(cell_values[1])
        self.cb_aptreport_aname.setCurrentText(cell_values[2])
        self.entry_aptreport_noh.setText(cell_values[3])
        self.entry_aptreport_apttypecode.setText(cell_values[4])
        self.cb_aptreport_apttypename.setCurrentText(cell_values[5])
        self.entry_aptreport_ciccode.setText(cell_values[6])
        self.entry_aptreport_customercode.setText(cell_values[7])
        self.cb_aptreport_customername.setCurrentText(cell_values[8])
        self.entry_aptreport_sjcode.setText(cell_values[9])
        self.cb_aptreport_sjname.setCurrentText(cell_values[10])
        self.entry_aptreport_contractvalue.setText(cell_values[11])
        self.entry_aptreport_cefffrom.setText(cell_values[12])
        self.entry_aptreport_ceffthru.setText(cell_values[13])
        self.entry_aptreport_ecode.setText(cell_values[14])
        self.cb_aptreport_ename.setCurrentText(cell_values[15])
        self.entry_aptreport_payment.setText(cell_values[16])
        self.entry_aptreport_eefffrom.setText(cell_values[17])
        self.entry_aptreport_eeffthru.setText(cell_values[18])
        self.entry_aptreport_remark.setText(cell_values[19])

    def refresh_data(self):
        self.clear_data()
        self.make_data()


if __name__ == "__main__":

    log_subfolder = "logs"
    os.makedirs(log_subfolder, exist_ok=True)
    log_file_path = os.path.join(log_subfolder, "access_AptReport.log")

    logging.basicConfig(
        filename=log_file_path,  
        level=logging.INFO,    
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = QtWidgets.QApplication(sys.argv)
    dialog = AptReportDialog()
    dialog.show()
    sys.exit(app.exec())