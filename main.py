import json
import tkinter as tk
from tkinter import messagebox as messagebox

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

        self.title.pack(fill="x")
        self.ddl_input.pack(fill="x")

    def set_schema(self, tables):
        """set table values from SchemaInputWidget"""
        self.tables = tables
        self.log_schema()

    def log_schema(self):
        """Log information about schema"""
        for table in self.tables:
            print(table.name)
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

                print(json.dumps(col_info, indent=2, ensure_ascii=False))


class SchemaInputWidget(tk.Frame):
    """Input ddl script from users"""

    def __init__(self, parent, schema_update_handler):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)

        self.set_schema = schema_update_handler

        self.instruction = tk.Label(self, text="Paste the SQL DDL script here: ", anchor="w")
        self.input = tk.Text(self, relief=tk.SUNKEN, width=20, height=10)
        self.button = tk.Button(self, text="Update Schema", command=self.input_update_handler)

        self.instruction.grid(row=0, column=0, sticky="w")
        self.button.grid(row=0, column=1, sticky="e")
        self.input.grid(row=1, columnspan=2, sticky="we")

    def input_update_handler(self):
        """parse input script and pass result into schema_update_handler"""
        parser = DdlParse()
        ddl_script = self.input.get("1.0", "end")
        try:
            table_definitions = ['CREATE' + script for script in ddl_script.split("CREATE") if script.strip() != '']
            tables = [parser.parse(dfn) for dfn in table_definitions]
        except ParseException:
            messagebox.showerror("Invalid SQL", "Please check you SQL syntax")
        else:
            self.set_schema(tables)


if __name__ == '__main__':
    root = tk.Tk()
    root.title("Fake SQL")
    MainWindow(root).pack(fill="both", expand=True)
    root.mainloop()
