import json
import tkinter as tk
import tkinter.ttk as ttk
from faker_function_list import FAKER_FUNCTION_LIST
from tkinter import messagebox as messagebox
from tkinter.scrolledtext import ScrolledText

from ddlparse import DdlParse
from pyparsing import ParseException


class MainWindow(tk.Frame):
    """Main Window"""

    def __init__(self, parent):
        super().__init__(parent)
        self.config(
            padx=5,
            pady=5,
        )
        self.tables = []

        self.title = tk.Label(self,
                              text='Fake SQL Generator',
                              font=("Times New Roman", 16),
                              anchor="w"
                              )

        self.ddl_input = SchemaInputWidget(self, schema_update_handler=self.set_schema)
        self.table_list = TableListWidget(self, self.tables)

        self.title.pack(side="top", fill="x")
        self.ddl_input.pack(side="top", fill="x")
        self.table_list.pack(side="top", fill="x")

    def set_schema(self, tables):
        """set table values from SchemaInputWidget"""
        self.tables = tables
        self.table_list.update_table_list(tables)
        self.log_schema()

    def log_schema(self):
        """Log information about schema"""
        print(json.dumps(self.tables, indent=2))


class SchemaInputWidget(tk.Frame):
    """Input ddl script from users"""

    def __init__(self, parent, schema_update_handler):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)

        self.set_schema = schema_update_handler

        self.instruction = tk.Label(self, text="Paste the SQL DDL script here: ", anchor="w")
        self.input = ScrolledText(self, relief=tk.SUNKEN, width=20, height=10)
        self.button = tk.Button(self, text="Update Schema", command=self.input_update_handler)

        self.instruction.grid(row=0, column=0, sticky="w")
        self.button.grid(row=0, column=1, sticky="e")
        self.input.grid(row=1, columnspan=2, sticky="we")

    def input_update_handler(self):
        """parse input script and pass result into schema_update_handler"""
        ddl_script = self.input.get("1.0", "end")
        try:
            # splitting each statement
            table_definitions = ['CREATE ' + script.strip() for script in ddl_script.split("CREATE") if
                                 script.strip() != '']
            tables = []
            # parsing ddl
            for dfn in table_definitions:
                table = DdlParse().parse(dfn)
                cols = []
                # setting table columns
                for col in table.columns.values():
                    col_info = {
                        "name": col.name,
                        "data_type": col.data_type,
                        "length": col.length,
                        "precision(=length)": col.precision,
                        "scale": col.scale,
                        "is_unsigned": col.is_unsigned,
                        "constraint": col.constraint,
                        "not_null": col.not_null,
                        "PK": col.primary_key,
                        "unique": col.unique,
                        "auto_increment": col.auto_increment,
                        "default": col.default,
                        "character_set": col.character_set,
                        "comment": col.comment,
                        "description(=comment)": col.description,
                    }
                    cols.append(col_info)
                tables.append({'name': table.name, 'columns': cols})
        except ParseException:
            messagebox.showerror("Invalid SQL", "Please check you SQL syntax")
        else:
            self.set_schema(tables[:])


class TableListWidget(tk.Frame):
    """Shows all input tables in a list"""

    def __init__(self, parent, tables):
        super().__init__(parent)
        self.tables = tables
        self.parent = parent

        self.table_list_title = tk.Label(self,
                                         text="Tables",
                                         font=("Times New Roman", 16)
                                         )
        self.table_list = tk.Listbox(self, selectmode="single")

        self.button_frame = tk.Frame(self)
        self.select_col_type_btn = tk.Button(
            self.button_frame, text="Set Column Values", command=self.open_table_window)
        self.delete_table_btn = tk.Button(
            self.button_frame, text="Delete", command=self.delete_table, )
        self.update_table_list()

        self.table_list_title.grid(row=0, column=0, columnspan=2)

        self.table_list.grid(row=1, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)

        self.button_frame.grid(row=1, column=1)
        self.select_col_type_btn.pack(side="top", fill="x")
        self.delete_table_btn.pack(side="top", fill="x")

    def update_table_list(self, tables=None):
        if tables:
            self.tables = tables
        else:
            tables = self.tables

        self.table_list.delete(0, "end")
        for table in tables:
            self.table_list.insert("end", table["name"].title())

    def delete_table(self):
        selected_indexes = self.table_list.curselection()
        if selected_indexes:
            del self.tables[selected_indexes[0]]
            self.table_list.delete(selected_indexes[0])

    def open_table_window(self):
        selected_indexes = self.table_list.curselection()
        if selected_indexes:
            TableWindow(self.parent, schema=self.tables, table=self.tables[selected_indexes[0]])


class TableWindow(tk.Toplevel):
    """Show table details with columns"""

    def __init__(self, parent, schema, table):
        super().__init__(parent)
        self.schema = schema
        self.table = table
        self.title(table["name"].title())

        self.window_heading = tk.Label(self,
                                       text=table["name"].title() + " Table Columns",
                                       font=("Times New Roman", 16))
        # column view
        self.table_column_list = ColumnList(self, table["columns"])

        # button groups
        self.column_control_btn_grp = tk.Frame(self, padx=5)
        self.edit_column_btn = tk.Button(
            self.column_control_btn_grp,
            text="Edit Columns",
            command=self.open_selected_column_window
        )
        self.delete_column_btn = tk.Button(
            self.column_control_btn_grp,
            text="Delete Column",
            command=self.table_column_list.delete_selected_column
        )

        self.window_heading.grid(row=0, column=0, columnspan=2)
        self.table_column_list.grid(row=1, column=0)

        self.column_control_btn_grp.grid(row=1, column=1, sticky="news")
        self.edit_column_btn.pack(side="top", fill="x")
        self.delete_column_btn.pack(side="top", fill="x")

    def open_selected_column_window(self):
        selected_column = self.table_column_list.get_selected_index()
        if selected_column:
            ColumnWindow(self,
                         schema=self.schema,
                         table_name=self.table["name"],
                         column=self.table["columns"][selected_column['index']])


class ColumnList(tk.Frame):
    """Show a list of all available column in a table"""

    def __init__(self, parent, table_columns):
        super().__init__(parent)
        self.parent = parent
        self.table_columns = table_columns

        self.tree_view = ttk.Treeview(self, selectmode="browse")
        # Attaching vertical scrollbar
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=self.scroll_y.set)

        # columns index
        self.tree_view['columns'] = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
        # setup
        self.tree_view['show'] = "headings"
        self.tree_view.column("1", width=30, anchor='sw')
        self.tree_view.column("2", width=180, anchor='sw')
        self.tree_view.column("3", width=90, anchor='sw')
        self.tree_view.column("4", width=90, anchor='sw')
        self.tree_view.column("5", width=60, anchor='sw')
        self.tree_view.column("6", width=60, anchor='sw')
        self.tree_view.column("7", width=60, anchor='sw')
        self.tree_view.column("8", width=60, anchor='sw')
        self.tree_view.column("9", width=90, anchor='sw')
        self.tree_view.column("10", width=200, anchor='sw')
        # columns heading
        self.tree_view.heading("1", text="Sn")
        self.tree_view.heading("2", text="Name")
        self.tree_view.heading("3", text="Type")
        self.tree_view.heading("4", text="Length")
        self.tree_view.heading("5", text="NN")
        self.tree_view.heading("6", text="PK")
        self.tree_view.heading("7", text="UN")
        self.tree_view.heading("8", text="AI")
        self.tree_view.heading("9", text="DEFAULT")
        self.tree_view.heading("10", text="Value/Ref")

        # inserting rows
        self.update_table_columns()

        self.tree_view.pack(side="left")
        self.scroll_y.pack(side="left", fill="y")

    def update_table_columns(self, table_columns=None):
        """Updates rows of ColumnList"""
        if table_columns:
            self.table_columns = table_columns
        else:
            table_columns = self.table_columns

        for index, columns in enumerate(table_columns):
            self.tree_view.insert("", "end",
                                  values=(
                                      index + 1,
                                      columns["name"],
                                      columns["data_type"],
                                      str(columns["length"]),
                                      str(columns["not_null"]),
                                      str(columns["PK"]),
                                      str(columns["unique"]),
                                      str(columns["auto_increment"]),
                                      str(columns["default"]),
                                      "ref"
                                  ))

    def get_selected_index(self):
        focuses = self.tree_view.selection()
        if focuses:
            return {
                'focus': focuses[0],
                'index': self.tree_view.item(focuses[0])["values"][0] - 1
            }

    def delete_selected_column(self):
        """Delete a column selected in tree view"""
        selected_item_index = self.get_selected_index()
        if selected_item_index:
            del self.table_columns[selected_item_index["index"]]
            self.tree_view.delete(*self.tree_view.get_children())
            self.update_table_columns()


class ColumnWindow(tk.Toplevel):
    """Show table details with columns"""

    def __init__(self, parent, schema, table_name, column):
        super().__init__(parent)
        self.schema = schema
        self.column = column
        self.title(table_name.title() + " / " + column["name"].title())
        self.config(padx=5, pady=5)

        self.window_heading = tk.Label(self,
                                       text=table_name.title() + " / " + column["name"].title(),
                                       font=("Times New Roman", 16))

        # checkboxes
        self.checkbox_frame = tk.Frame(self)
        self.options = {
            'pk': tk.BooleanVar(),
            'un': tk.BooleanVar(),
            'ai': tk.BooleanVar(),
            'nn': tk.BooleanVar()
        }

        self.options['pk'].set(self.column['PK'])
        self.options['un'].set(self.column['unique'])
        self.options['ai'].set(self.column['auto_increment'])
        self.options['nn'].set(self.column['not_null'])

        self.primary_key_checkbox = tk.Checkbutton(self.checkbox_frame,
                                                   text="Primary Key",
                                                   var=self.options['pk'],
                                                   )
        self.unique_key_checkbox = tk.Checkbutton(self.checkbox_frame,
                                                  text="Unique Key",
                                                  var=self.options['un'])
        self.auto_inc_checkbox = tk.Checkbutton(self.checkbox_frame,
                                                text="Auto Increment",
                                                var=self.options['ai'])
        self.not_null_checkbox = tk.Checkbutton(self.checkbox_frame,
                                                text="Auto Increment",
                                                var=self.options['nn'])

        # source selector
        self.selected_src = tk.StringVar()
        self.choose_src_title = tk.Label(self, text="Choose any of the Source")

        self.faker_chooser_frame = tk.Frame(self)
        self.faker_function = tk.StringVar()
        self.choose_src_faker = tk.Radiobutton(self.faker_chooser_frame,
                                               text="Using Faker",
                                               value="faker",
                                               var=self.selected_src)
        self.faker_chooser_title= tk.Label(self.faker_chooser_frame, text="Faker Function")
        self.faker_chooser = tk.OptionMenu(self.faker_chooser_frame,
                                           self.faker_function,
                                           *FAKER_FUNCTION_LIST)

        self.ref_chooser_frame = tk.Frame(self)
        self.choose_src_ref = tk.Radiobutton(self.ref_chooser_frame,
                                             text="Using table Reference",
                                             value="ref",
                                             var=self.selected_src)
        self.ref_table = tk.StringVar()
        self.ref_column = tk.StringVar()
        self.table_chooser_title = tk.Label(self.ref_chooser_frame, text="Ref table")
        self.table_chooser = tk.OptionMenu(self.ref_chooser_frame,
                                           self.ref_table,
                                           *[table["name"] for table in self.schema if table["name"] != table_name],
                                           command=self.update_column_chooser
                                           )
        self.column_chooser_title = tk.Label(self.ref_chooser_frame, text="Ref column")
        self.column_chooser = None

        self.window_heading.pack()
        # checkbox pack
        self.checkbox_frame.pack()
        self.primary_key_checkbox.pack(side="left")
        self.unique_key_checkbox.pack(side="left")
        self.auto_inc_checkbox.pack(side="left")
        self.not_null_checkbox.pack(side="left")

        self.choose_src_title.pack()

        self.faker_chooser_frame.pack(side="left", fill="both", expand=True)
        self.choose_src_faker.pack()
        self.faker_chooser_title.pack(side="top")
        self.faker_chooser.pack(side="top")

        self.ref_chooser_frame.pack(side="left", fill="both", expand=True)
        self.choose_src_ref.pack(side="top")
        self.table_chooser_title.pack(side="top")
        self.table_chooser.pack(side="top")

    def update_column_chooser(self, table_name):
        for index, table in enumerate(self.schema):
            if table["name"] == table_name:
                ref_table_index = index
                break
        if self.column_chooser:
            self.column_chooser.forget()
        else:
            self.column_chooser_title.pack(side="top")
        self.column_chooser = tk.OptionMenu(self.ref_chooser_frame,
                                            self.ref_column,
                                            *[column["name"] for column in self.schema[ref_table_index]['columns']],
                                            )
        self.column_chooser.pack(side="top")


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Fake SQL")
    MainWindow(root).pack(fill="both", expand=True)
    root.mainloop()
