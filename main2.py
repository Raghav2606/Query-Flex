import sys
import os
import duckdb
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QTextEdit, QFileDialog, QLabel,
    QSplitter, QMessageBox, QInputDialog, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont


class SQLExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Query Gen 2.0")
        self.resize(1400, 900)

        self.conn = duckdb.connect()
        self.tables = {}  # alias -> {"df": DataFrame, "file": str, "sheet": str}
        self.current_result_df = None

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # Left: sidebar
        sidebar_layout = QVBoxLayout()
        self.add_file_btn = QPushButton("➕ Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        sidebar_layout.addWidget(self.add_file_btn)

        self.table_list = QTableWidget(0, 4)
        self.table_list.setHorizontalHeaderLabels(["Alias", "File", "Sheet", "Rows"])
        self.table_list.cellClicked.connect(self.on_table_clicked)
        self.table_list.horizontalHeader().setStretchLastSection(True)
        self.table_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sidebar_layout.addWidget(self.table_list)

        self.schema_label = QLabel("Schema Preview")
        self.schema_label.setFont(QFont("Consolas", 10, QFont.Bold))
        sidebar_layout.addWidget(self.schema_label)

        self.schema_info = QTextEdit()
        self.schema_info.setReadOnly(True)
        self.schema_info.setFont(QFont("Consolas", 14))
        sidebar_layout.addWidget(self.schema_info)

        # Right: editor + results
        right_splitter = QSplitter(Qt.Vertical)

        # SQL editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        self.sql_editor = QTextEdit()
        self.sql_editor.setFont(QFont("Consolas", 14))
        editor_layout.addWidget(self.sql_editor)

        run_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Run Query")
        self.run_btn.clicked.connect(self.run_query)
        self.clear_btn = QPushButton("✖ Clear")
        self.clear_btn.clicked.connect(lambda: self.sql_editor.clear())
        run_layout.addWidget(self.run_btn)
        run_layout.addWidget(self.clear_btn)
        editor_layout.addLayout(run_layout)

        right_splitter.addWidget(editor_widget)

        # Results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        self.result_label = QLabel("Query Results")
        self.result_label.setFont(QFont("Consolas", 10, QFont.Bold))
        results_layout.addWidget(self.result_label)

        self.result_table = QTableWidget(0, 0)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.result_table)

        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("⬇ Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_xlsx_btn = QPushButton("⬇ Export Excel")
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.export_xlsx_btn)
        results_layout.addLayout(export_layout)

        right_splitter.addWidget(results_widget)
        right_splitter.setSizes([500, 400])  # editor/results default ratio
        right_splitter.setHandleWidth(4)

        # Assemble main layout
        main_splitter = QSplitter(Qt.Horizontal)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        main_splitter.addWidget(sidebar_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([400, 1000])  # sidebar/main ratio
        main_splitter.setHandleWidth(4)

        main_layout.addWidget(main_splitter)

    # --- Functions ---
    def add_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Data Files (*.csv *.xlsx *.xls)"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        alias, ok = QInputDialog.getText(
            self, "Alias", f"Enter alias for table ({os.path.basename(file_path)}):"
        )
        if not ok or not alias.strip():
            return
        alias = alias.strip()

        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
                self.register_alias(alias, df, file_path, sheet="-")
            elif ext in (".xlsx", ".xls"):
                xls = pd.ExcelFile(file_path)
                sheet, ok2 = QInputDialog.getText(
                    self, "Sheet", f"Enter sheet name (default={xls.sheet_names[0]}):"
                )
                if not ok2:
                    return
                sheet = sheet.strip()
                if not sheet:
                    sheet = xls.sheet_names[0]
                if sheet not in xls.sheet_names:
                    QMessageBox.warning(self, "Error", f"Sheet '{sheet}' not found")
                    return
                df = pd.read_excel(file_path, sheet_name=sheet)
                self.register_alias(alias, df, file_path, sheet=sheet)
            else:
                QMessageBox.warning(self, "Error", "Unsupported file type")
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def register_alias(self, alias, df, file_path, sheet="-"):
        if alias in self.tables:
            self.conn.unregister(alias)
        self.conn.register(alias, df)
        self.tables[alias] = {"df": df, "file": os.path.basename(file_path), "sheet": sheet}

        row = self.table_list.rowCount()
        self.table_list.insertRow(row)
        self.table_list.setItem(row, 0, QTableWidgetItem(alias))
        self.table_list.setItem(row, 1, QTableWidgetItem(os.path.basename(file_path)))
        self.table_list.setItem(row, 2, QTableWidgetItem(sheet))
        self.table_list.setItem(row, 3, QTableWidgetItem(str(len(df))))

        self.show_schema(alias)

    def on_table_clicked(self, row, col):
        alias_item = self.table_list.item(row, 0)
        if alias_item:
            alias = alias_item.text()
            self.show_schema(alias)

    def show_schema(self, alias):
        df = self.tables[alias]["df"]
        text = "\n".join(f"{c}: {df[c].dtype}" for c in df.columns)
        self.schema_info.setPlainText(text)

    def run_query(self):
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return
        try:
            df = self.conn.execute(sql).df()
            self.current_result_df = df
            self.display_results(df)
        except Exception as ex:
            QMessageBox.critical(self, "Query Error", str(ex))

    def display_results(self, df):
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(len(df.columns))
        self.result_table.setHorizontalHeaderLabels(df.columns)

        for i, row in df.iterrows():
            self.result_table.insertRow(i)
            for j, val in enumerate(row):
                self.result_table.setItem(i, j, QTableWidgetItem(str(val)))

    def export_csv(self):
        if self.current_result_df is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if path:
            self.current_result_df.to_csv(path, index=False)

    def export_xlsx(self):
        if self.current_result_df is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "", "Excel Files (*.xlsx)")
        if path:
            self.current_result_df.to_excel(path, index=False)


# ---- Dark Theme Styling ----
def apply_dark_theme(app: QApplication):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(100, 150, 250))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    app.setStyleSheet("""
        QPushButton {
            background-color: #2d89ef;
            border: none;
            padding: 6px 12px;
            color: white;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1b5fbd;
        }
        QTextEdit, QTableWidget {
            border: 1px solid #555;
            border-radius: 4px;
            padding: 4px;
        }
        QLabel {
            color: #ddd;
        }
    """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SQLExplorer()
    win.show()
    sys.exit(app.exec_())
