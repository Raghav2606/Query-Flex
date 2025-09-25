import sys
import os
import duckdb
import pandas as pd
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import mplcursors

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QTextEdit, QFileDialog, QLabel,
    QSplitter, QMessageBox, QInputDialog, QHeaderView, QCheckBox,
    QComboBox, QTabWidget, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QFont, QIcon

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# Load OpenAI client (expects OPENAI_API_KEY in env)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ["OPENAI_BASE_URL"])


def clean_sql_output(raw: str) -> str:
    sql = raw.strip()
    if sql.startswith("```"):
        sql = sql.strip("`")
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()
    return sql.strip("`").strip()


def generate_sql_from_prompt(prompt: str, schema_tables: dict) -> str:
    schema_desc, samples_desc, context_desc = [], [], []
    for alias, meta in schema_tables.items():
        df = meta["df"]
        cols = ", ".join([f"{c} ({df[c].dtype})" for c in df.columns])
        schema_desc.append(f"Table {alias}: {cols}")
        sample_df = df.head(3)
        samples_desc.append(f"Samples from {alias}:\n{sample_df.to_csv(index=False)}")
        if meta.get("context"):
            context_desc.append(f"Context for {alias}: {meta['context']}")
    schema_text = "\n".join(schema_desc)
    samples_text = "\n".join(samples_desc)
    context_text = "\n".join(context_desc)
    full_prompt = f"""
You are a SQL assistant. Convert the natural language question into a valid DuckDB SQL query.

Schema:
{schema_text}

Sample data:
{samples_text}

Additional context:
{context_text}

Question: {prompt}

Rules:
- Only use the provided tables/columns.
- Qualify ambiguous column names with table alias if needed.
- Return ONLY the SQL query (no explanations, no markdown, no ``` fences).
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0,
        )
        raw_sql = resp.choices[0].message.content.strip()
        return clean_sql_output(raw_sql)
    except Exception as ex:
        return f"-- Error generating SQL: {ex}"


class SQLExplorer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Query Gen 2.0")
        self.resize(1600, 900)

        self.conn = duckdb.connect()
        self.tables = {}
        self.current_result_df = None
        self.dark_mode = True

        # --- Layout ---
        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar_layout = QVBoxLayout()
        self.add_file_btn = QPushButton("➕ Add File")
        self.add_file_btn.clicked.connect(self.add_file)
        sidebar_layout.addWidget(self.add_file_btn)

        self.table_list = QTableWidget(0, 6)
        self.table_list.setHorizontalHeaderLabels(["Alias", "File", "Sheet", "Rows", "Edit", "Remove"])
        self.table_list.horizontalHeader().setStretchLastSection(True)
        self.table_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sidebar_layout.addWidget(self.table_list)

        self.schema_label = QLabel("Schema Preview")
        self.schema_label.setFont(QFont("Consolas", 10, QFont.Bold))
        sidebar_layout.addWidget(self.schema_label)

        self.schema_info = QTextEdit()
        self.schema_info.setReadOnly(True)
        self.schema_info.setFont(QFont("Consolas", 12))
        sidebar_layout.addWidget(self.schema_info)

        self.context_label = QLabel("Data Context (optional)")
        self.context_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        sidebar_layout.addWidget(self.context_label)

        self.context_editor = QTextEdit()
        self.context_editor.setFont(QFont("Segoe UI", 10))
        self.context_editor.textChanged.connect(self.save_context)
        sidebar_layout.addWidget(self.context_editor)

        # Right: editor + results
        right_splitter = QSplitter(Qt.Vertical)

        # Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        theme_btn = QPushButton("🌗 Toggle Theme")
        theme_btn.clicked.connect(self.toggle_theme)
        editor_layout.addWidget(theme_btn, alignment=Qt.AlignRight)

        self.sql_editor = QTextEdit()
        self.sql_editor.setFont(QFont("Consolas", 13))
        editor_layout.addWidget(self.sql_editor)

        self.use_llm_checkbox = QCheckBox("Use Natural Language (LLM)")
        editor_layout.addWidget(self.use_llm_checkbox)

        btn_layout = QHBoxLayout()
        self.preview_btn = QPushButton("👁 Preview Query")
        self.preview_btn.clicked.connect(self.preview_llm_query)
        self.run_btn = QPushButton("▶ Run Query")
        self.run_btn.clicked.connect(self.run_query)
        self.clear_btn = QPushButton("✖ Clear")
        self.clear_btn.clicked.connect(lambda: self.sql_editor.clear())
        btn_layout.addWidget(self.preview_btn)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_btn)
        editor_layout.addLayout(btn_layout)

        right_splitter.addWidget(editor_widget)

        # Results Tabs
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        self.tabs = QTabWidget()

        # Table Tab
        self.result_table = QTableWidget(0, 0)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        table_layout.addWidget(self.result_table)

        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("⬇ Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_xlsx_btn = QPushButton("⬇ Export Excel")
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.export_xlsx_btn)
        table_layout.addLayout(export_layout)

        self.tabs.addTab(table_tab, "Table")

        # Visualization Tab
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        control_layout = QHBoxLayout()
        self.x_dropdown = QComboBox()
        self.y_dropdown = QComboBox()
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar", "Line", "Scatter"])
        self.plot_btn = QPushButton("📊 Plot")
        self.plot_btn.clicked.connect(self.plot_chart)
        control_layout.addWidget(QLabel("X-axis"))
        control_layout.addWidget(self.x_dropdown)
        control_layout.addWidget(QLabel("Y-axis"))
        control_layout.addWidget(self.y_dropdown)
        control_layout.addWidget(QLabel("Type"))
        control_layout.addWidget(self.chart_type)
        control_layout.addWidget(self.plot_btn)
        viz_layout.addLayout(control_layout)

        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.canvas)
        viz_layout.addWidget(self.scroll_area)

        self.tabs.addTab(viz_tab, "Visualization")
        results_layout.addWidget(self.tabs)
        right_splitter.addWidget(results_widget)

        # Split main
        main_splitter = QSplitter(Qt.Horizontal)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        main_splitter.addWidget(sidebar_widget)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([450, 1150])
        main_splitter.setHandleWidth(4)

        main_layout.addWidget(main_splitter)

        # Start dark theme
        apply_dark_theme(QApplication.instance())

    # --- File mgmt ---
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
            else:
                xls = pd.ExcelFile(file_path)
                sheet, ok2 = QInputDialog.getText(
                    self, "Sheet", f"Enter sheet name (default={xls.sheet_names[0]}):"
                )
                if not ok2:
                    return
                sheet = sheet.strip() or xls.sheet_names[0]
                df = pd.read_excel(file_path, sheet_name=sheet)
                self.register_alias(alias, df, file_path, sheet=sheet)
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def register_alias(self, alias, df, file_path, sheet="-"):
        if alias in self.tables:
            self.conn.unregister(alias)
        self.conn.register(alias, df)
        # ✅ Store DataFrame for schema preview
        self.tables[alias] = {"df": df, "file": os.path.basename(file_path), "sheet": sheet, "context": ""}
        self.refresh_file_table()
        self.show_schema(alias)

    def refresh_file_table(self):
        self.table_list.setRowCount(0)
        for alias, meta in self.tables.items():
            row = self.table_list.rowCount()
            self.table_list.insertRow(row)
            self.table_list.setItem(row, 0, QTableWidgetItem(alias))
            self.table_list.setItem(row, 1, QTableWidgetItem(meta["file"]))
            self.table_list.setItem(row, 2, QTableWidgetItem(meta["sheet"]))
            self.table_list.setItem(row, 3, QTableWidgetItem(str(len(meta["df"]))))

            # Edit icon
            btn_edit = QPushButton()
            btn_edit.setIcon(QIcon.fromTheme("document-edit"))
            if btn_edit.icon().isNull():
                btn_edit.setText("✏")
            btn_edit.setToolTip("Edit alias/sheet")
            btn_edit.setFlat(True)
            btn_edit.setStyleSheet("background-color: transparent; border: none;")
            btn_edit.clicked.connect(lambda _, a=alias: self.edit_table(a))
            self.table_list.setCellWidget(row, 4, btn_edit)

            # Remove icon
            btn_remove = QPushButton()
            btn_remove.setIcon(QIcon.fromTheme("edit-delete"))
            if btn_remove.icon().isNull():
                btn_remove.setText("🗑")
            btn_remove.setToolTip("Remove table")
            btn_remove.setFlat(True)
            btn_remove.setStyleSheet("background-color: transparent; border: none;")
            btn_remove.clicked.connect(lambda _, a=alias: self.remove_table(a))
            self.table_list.setCellWidget(row, 5, btn_remove)

    def edit_table(self, alias):
        meta = self.tables[alias]
        new_alias, ok = QInputDialog.getText(self, "Edit Alias", "Alias:", text=alias)
        if not ok or not new_alias.strip():
            return
        new_alias = new_alias.strip()
        df = meta["df"]
        self.conn.unregister(alias)
        self.conn.register(new_alias, df)
        self.tables.pop(alias)
        self.tables[new_alias] = meta
        self.refresh_file_table()
        self.show_schema(new_alias)

    def remove_table(self, alias):
        if alias in self.tables:
            self.conn.unregister(alias)
            self.tables.pop(alias)
            self.refresh_file_table()
            self.schema_info.clear()
            self.context_editor.clear()

    def on_table_clicked(self, row, col):
        alias_item = self.table_list.item(row, 0)
        if alias_item:
            alias = alias_item.text()
            self.show_schema(alias)
            self.context_editor.setText(self.tables[alias].get("context", ""))

    def show_schema(self, alias):
        df = self.tables[alias]["df"]
        text = "\n".join(f"{c}: {df[c].dtype}" for c in df.columns)
        self.schema_info.setPlainText(text)

    def save_context(self):
        row = self.table_list.currentRow()
        if row >= 0:
            alias = self.table_list.item(row, 0).text()
            self.tables[alias]["context"] = self.context_editor.toPlainText()

    # --- Query ---
    def preview_llm_query(self):
        if not self.use_llm_checkbox.isChecked():
            QMessageBox.information(self, "Info", "Enable LLM first.")
            return
        prompt = self.sql_editor.toPlainText().strip()
        if not prompt:
            return
        sql = generate_sql_from_prompt(prompt, self.tables)
        QMessageBox.information(self, "Preview Generated SQL", sql)

    def run_query(self):
        if self.use_llm_checkbox.isChecked():
            prompt = self.sql_editor.toPlainText().strip()
            if not prompt:
                return
            sql_to_run = generate_sql_from_prompt(prompt, self.tables)
        else:
            sql_to_run = self.sql_editor.toPlainText().strip()
        if not sql_to_run:
            return
        try:
            df = self.conn.execute(sql_to_run).df()
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
        self.x_dropdown.clear()
        self.y_dropdown.clear()
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        self.x_dropdown.addItems(cat_cols + num_cols)
        self.y_dropdown.addItems(num_cols)
        if cat_cols:
            self.x_dropdown.setCurrentText(cat_cols[0])
        if num_cols:
            self.y_dropdown.setCurrentText(num_cols[0])

    # --- Visualization ---
    def plot_chart(self):
        if self.current_result_df is None or self.current_result_df.empty:
            QMessageBox.warning(self, "No Data", "Run a query first.")
            return
        x_col = self.x_dropdown.currentText()
        y_col = self.y_dropdown.currentText()
        chart_type = self.chart_type.currentText()
        if not x_col or not y_col:
            return
        n = len(self.current_result_df[x_col].unique())
        width = max(8, n * 0.5)
        self.figure.set_size_inches(width, 6)
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        if chart_type == "Bar":
            ax.bar(self.current_result_df[x_col], self.current_result_df[y_col])
        elif chart_type == "Line":
            ax.plot(self.current_result_df[x_col], self.current_result_df[y_col])
        elif chart_type == "Scatter":
            ax.scatter(self.current_result_df[x_col], self.current_result_df[y_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(f"{chart_type} Chart of {y_col} vs {x_col}")
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        mplcursors.cursor(ax, hover=True)
        self.canvas.draw()

    # --- Export ---
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

    # --- Theme toggle ---
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            apply_dark_theme(QApplication.instance())
        else:
            apply_light_theme(QApplication.instance())


# ---- Themes ----
def apply_dark_theme(app: QApplication):
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(100, 150, 250))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    app.setStyleSheet("""
        QPushButton { background-color: #2d89ef; border: none; padding: 6px 12px; color: white; border-radius: 4px; }
        QPushButton:hover { background-color: #1b5fbd; }
        QTextEdit, QTableWidget { border: 1px solid #555; border-radius: 4px; padding: 4px; }
        QLabel, QCheckBox { color: #ffffff; }
        QCheckBox { font-size: 11pt; }
        QComboBox { background-color: #2d2d30; color: #ffffff; border: 1px solid #555; border-radius: 4px; padding: 4px; }
        QComboBox QAbstractItemView { background-color: #2d2d30; color: #ffffff; selection-background-color: #444; selection-color: #ffffff; }
        QTabBar::tab { background: #2d2d30; color: #ccc; padding: 6px 12px; }
        QTabBar::tab:selected { background: #0078D4; color: white; }
    """)


def apply_light_theme(app: QApplication):
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(255, 255, 255))
    light_palette.setColor(QPalette.WindowText, Qt.black)
    light_palette.setColor(QPalette.Base, QColor(245, 245, 245))
    light_palette.setColor(QPalette.Text, Qt.black)
    light_palette.setColor(QPalette.Button, QColor(16, 124, 16))
    light_palette.setColor(QPalette.ButtonText, Qt.white)
    light_palette.setColor(QPalette.Highlight, QColor(16, 124, 16))
    light_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(light_palette)
    app.setStyleSheet("""
        QPushButton { background-color: #107C10; border: none; padding: 6px 12px; color: white; border-radius: 4px; }
        QPushButton:hover { background-color: #0B6A0B; }
        QTextEdit, QTableWidget { border: 1px solid #ccc; border-radius: 4px; padding: 4px; background: white; }
        QLabel, QCheckBox { color: #323130; }
        QCheckBox { font-size: 11pt; }
        QComboBox { background-color: #ffffff; color: #323130; border: 1px solid #ccc; border-radius: 4px; padding: 4px; }
        QComboBox QAbstractItemView { background-color: #ffffff; color: #323130; selection-background-color: #e5f1fb; selection-color: #000000; }
        QTabBar::tab { background: #f3f2f1; color: #323130; padding: 6px 12px; }
        QTabBar::tab:selected { background: #107C10; color: white; }
    """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SQLExplorer()
    win.show()
    sys.exit(app.exec_())
