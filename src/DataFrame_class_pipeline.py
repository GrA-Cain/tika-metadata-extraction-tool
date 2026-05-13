import pandas as pd
from pathlib import Path
from metadata import metadata_dataframe as ms
import openpyxl
import xlsxwriter
from itertools import combinations, chain
from functools import cached_property


class DataFrame_pipeline():
    NAMESPACE_DICT = {"Message": "Message:|Message-",
                "Mapi" : "mapi:",
                "dc" : "^dc:|dcterms",
                "pdf" : "^pdf:|pdfaid|pdfa:|pdfuaid",
                "xmp" : "^xmp:|xmpMM:|xmpTPg",
                "X-tika" :"X-TIKA:|tika|tika_|tika_batch",
                "meta" : "meta:",
                "extendend_properties" : "extended-properties:",
                "MSIP" : "^(?!pdf:).*MSIP_Label",
                "Exif": "Exif|exif"
                } #you can add namespaces here
    
    DATAFRAME_RETURNS = ["raw", "filetype_dict(all unique filetypes)", 
                         "Namespace dict (all namespace dfs)", 
                         "leftover fields df (all fields not belonging to a namespace)",
                         "percentage_df"]
    
    OPTIONS = ["stats", "duplicate_values"]
    
    

    def __init__(self, root_dir : str | Path, log_folder_path : str | Path, xlsx_path : str | Path):
        self.root_dir = root_dir
        self.log_folder_path = log_folder_path
        self.xlsx_path = xlsx_path

    @cached_property
    def df_raw(self):
       return pd.DataFrame(data = ms(self.root_dir, self.log_folder_path))

    def filetype_list(self): 
        return list(self.df_raw["tika:file_ext"].unique())
    
    @staticmethod
    def summary_columns(df):
        missing_values_percentage = (df.isna().sum() / len(df) * 100).round(1)
        missing_values_percentage = missing_values_percentage.astype(str) + "%" 
        columns =  pd.DataFrame({
            "unique values" : df.astype(str).nunique(),
            "Non-NA values" : df.notna().sum(),
            "NA values" : df.isna().sum(),
            "NA values (%)" : missing_values_percentage
        })
        output = pd.concat([df, columns.T]) 
        output = pd.concat([output.iloc[-4:], output.iloc[:-4]]) 
        return output
    
    @cached_property
    def genereren_filetype_dfs(self):
        filetype_dict = {}
        for regex_str in self.filetype_list:
            df = self.df_raw
            df = df.set_index("tika:file_ext")
            df = df.filetype(axis=0, regex=regex_str) 
            df = df.reset_index()
            df_index = df.replace("", None).notna().sum(axis = 1).sort_values(ascending = False).index
            filetype_dict[regex_str] = df.reindex(df_index)
            return filetype_dict
    
    def return_filetype_dfs(self, filetype : str, summary = False):
         return self.summary_columns(self.genereren_filetype_dfs[filetype]) if summary else self.genereren_filetype_dfs[filetype]
    
    @cached_property
    def genereren_namespace_dfs(self):
        namespace_return = {}
        for name, regex_str in DataFrame_pipeline.NAMESPACE_DICT.items():
            df = self.df_raw.filetype(axis = 1, regex = regex_str).replace("", None).dropna(how = "all", axis = 0) 
            df = df[df.isna().sum().sort_values(ascending=True).index] 
            column = self.df_raw.loc[df.index, "tika:file_ext"] 
            df = pd.concat([df, column], axis = 1) 
            df = df.set_index("tika:file_ext") 
            namespace_return[name] = df
        jpeg_only = self.df_raw.set_index("tika:file_ext").index.str.lower().str.match("jpg") 
        non_jpeg = ~jpeg_only 
        has_value_in_jpg = self.df_raw[jpeg_only].notna().any(axis=0)
        has_value_in_non_jpg = self.df_raw[non_jpeg].notna().any(axis=0) 
        jpg_only_cols = has_value_in_jpg & ~has_value_in_non_jpg 
        df = self.df_raw.loc[:, jpg_only_cols].dropna(how = "all", axis = 0).drop(namespace_return["Exif"].columns, axis = 1) 
        file_ext_column = self.df_raw.loc[df.index, "tika:file_ext"]
        df = pd.concat([df, file_ext_column], axis = 1)#.set_index("tika:file_ext")
        namespace_return["Image"] = df
        return self.summary_columns(namespace_return)
    
    #overbodig?
    def return_namespace_columns(self):
        df_columns = []
        for namespace_columns in self.genereren_namespace_dfs.values():
            df_columns.append(namespace_columns.columns)
        return df_columns
    
    def create_dataframe_leftover_fields(self):
        index = []
        for columns in self.genereren_namespace_dfs.values():
            index.append(columns.columns)
        index = list(set(chain.from_iterable(index)))
        return self.summary_columns(self.df_raw.drop(index, axis = 1).set_index("tika:file_ext")) 
    
    def visualiseren_duplicaten_DataFrames(self, df): 
        columns = []
        for col_a, col_b in combinations(df.columns, 2):
            overlap = (df[col_a] == df[col_b]).sum()
            percentage_overlap = overlap / len(df) * 100
            if percentage_overlap > 70: 
                columns.append((col_a, col_b))
        unpack = list(chain.from_iterable(columns))
        remove_duplicates = list(dict.fromkeys(unpack))
        df = df[remove_duplicates]
        return self.summary_columns(df)
    
    ##funcs for percentage non-NA values per namespace
    def make_namespace_series(self): 
        combined = []
        for name, df in self.genereren_namespace_dfs.items():
            series = pd.Series(name, index = df.columns)
            combined.append(series)
        combined.append(pd.Series("Restant", index = self.create_dataframe_leftover_fields().columns)) 
        combined = pd.concat(combined)
        return combined
    
    @cached_property
    def berekenen_percentages(self):
        percentage_dict = {}
        for filetype in self.filetype_list:
            filetype_df = self.df_raw.set_index("tika:file_ext").filter(axis = 0, regex = filetype)
            percentage = filetype_df.notna().sum() / len(filetype_df) * 100
            percentage_dict[filetype] = percentage
        df = pd.DataFrame(percentage_dict)
        df = df.round(1)
        df_mean_values = df.mean(axis = 1).round(1)
        df = pd.concat([df, df_mean_values], axis=1).rename({0 : 'gemiddelde'}, axis = 1).sort_values(axis = 0, by = ['gemiddelde'] , ascending= False)
        namespace_series = self.make_namespace_series()
        df = df.assign(namespace = namespace_series)
        return df
    
    def df_browser_viewer(self):
        
    def df_excel_writer(self):
        excelwriter_options = ["df_raw", "df_percentage", "df_leftover_fields"]
        options = ["visualiseren duplicaten", "summary_columns"]
        excelwriter_options.extend(self.genereren_filetype_dfs.keys())
        excelwriter_options.extend(self.genereren_namespace_dfs.keys())
        self.df_raw.to_excel(self.xlsx_path)
        with pd.ExcelWriter(self.xlsx_path, engine = "openpyxl", mode = "a") as writer:


# df_raw.to_excel("C:/Users/m.venema/Desktop/test/dataframe_test.xlsx")
# with pd.ExcelWriter("C:/Users/m.venema/Desktop/test/dataframe_test.xlsx", engine = "openpyxl", mode = "a") as writer:
#     df_msg_selectie.to_excel(writer, sheet_name = "selectie_msg")
#     df_pdf_selectie.to_excel(writer, sheet_name = "pdf_selectie")
#     df_docx_selectie.to_excel(writer, sheet_name = "docx_selectie")
#     df_percentage.to_excel(writer, sheet_name = f"%bestandstype")
#     df_distributie_T.to_excel(writer, sheet_name = "distributie van namespaces")
#     df_docx.to_excel(writer, sheet_name = "docx")
#     df_msg.to_excel(writer, sheet_name = "msg")
#     df_pdf.to_excel(writer, sheet_name = "pdf")
#     df_jpg.to_excel(writer, sheet_name = "jpg")
#     df_xlsx.to_excel(writer, sheet_name = "xlsx")
#     df_message_ns.to_excel(writer, sheet_name = "message ns")
#     df_Mapi_ns.to_excel(writer, sheet_name = "mapi ns")
#     df_meta_ns.to_excel(writer, sheet_name = "meta ns")
#     df_dc_ns.to_excel(writer, sheet_name= "dc ns")
#     df_ExtendedProperties_ns.to_excel(writer, sheet_name= "extentedproperties ns")
#     df_xmp_ns.to_excel(writer, sheet_name= "xmp ns")
#     df_exif_ns.to_excel(writer, sheet_name = "exif ns")
#     df_pdf_ns.to_excel(writer, sheet_name= "pdf ns")
#     df_Xtika_ns.to_excel(writer, sheet_name= "X-tika ns")
#     df_MSIP_ns.to_excel(writer, sheet_name = "MSIP ns")
#     df.to_excel(writer, sheet_name = "image ns")
#     df_restant.to_excel(writer, sheet_name = "overige kolommen")
#     df_raw.to_excel(writer, sheet_name = "volledig dataframe")