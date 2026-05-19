import pandas as pd
from pathlib import Path
from metadata import metadata_dataframe as ms
import openpyxl
import xlsxwriter
from itertools import combinations, chain
from functools import cached_property
import dtale


class DataFrame_pipeline():
    NAMESPACE_DICT = {"Message ns": "Message:|Message-",
                "Mapi" : "mapi:",
                "dc" : "^dc:|dcterms",
                "pdf" : "^pdf:|pdfaid|pdfa:|pdfuaid",
                "xmp" : "^xmp:|xmpMM:|xmpTPg",
                "X-tika" :"X-TIKA:|tika|tika_|tika_batch",
                "meta" : "meta:",
                "Extendend properties" : "extended-properties:",
                "MSIP" : "^(?!pdf:).*MSIP_Label",
                "Exif": "Exif|exif",
                "Image" : "Image"
                } #you can add namespaces here using the following format name (key) : regex str(value). 
    
    def __init__(self, root_dir : str | Path, log_folder_path : str | Path, xlsx_path : str | Path):
        self.root_dir = root_dir
        self.log_folder_path = log_folder_path
        self.xlsx_path = xlsx_path
        self.output_options = ["basis", "Coverage (non-NA) of metadata by filetype", "Leftover fields"] + self.filetype_list + list(self.NAMESPACE_DICT.keys())
        self.function_calls = [lambda: self.df_raw,
                               lambda summary: self.field_coverage_by_filetype_df(summary = summary),
                               lambda summary: self.create_dataframe_leftover_fields(summary = summary)]
        self.function_calls.extend(lambda summary, ft = filetype: self.return_filetype_dfs(filetype = ft, summary = summary) for filetype in self.filetype_list)
        self.function_calls.extend(lambda summary, ns = namespace: self.return_namespace_dfs(namespace = ns, summary= summary) for namespace in self.NAMESPACE_DICT.keys())
        self.additional_options = ["Duplicate analysis", "Add summary columns"]
        self.output_dataframe_dict = {key: value for key, value in zip(self.output_options, self.function_calls)}

    @cached_property
    def df_raw(self):
       return pd.DataFrame(data = ms(self.root_dir, self.log_folder_path))

    @cached_property
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
            df = df.filter(axis=0, regex=regex_str) 
            df = df.reset_index()
            df_index = df.replace("", None).notna().sum(axis = 1).sort_values(ascending = False).index
            filetype_dict[regex_str] = df.reindex(df_index) ##ff indexen op bestandsnaam!
        return filetype_dict
    
    def return_filetype_dfs(self, filetype : str, summary = False):
         return self.summary_columns(self.genereren_filetype_dfs[filetype]) if summary else self.genereren_filetype_dfs[filetype]
    
    @cached_property
    def genereren_namespace_dfs(self):
        namespace_return = {}
        for name, regex_str in DataFrame_pipeline.NAMESPACE_DICT.items():
            df = self.df_raw.filter(axis = 1, regex = regex_str).replace("", None).dropna(how = "all", axis = 0) 
            df = df[df.isna().sum().sort_values(ascending=True).index] 
            column = self.df_raw.loc[df.index, "tika:file_ext"] 
            df = pd.concat([df, column], axis = 1) 
            df = df.set_index("tika:file_ext") 
            namespace_return[name] = df
        #making image namespace (all metadata (excluding exif) that are found in jpg files but not in any other filetype)
        jpeg_only = self.df_raw.set_index("tika:file_ext").index.str.lower().str.match("jpg") 
        non_jpeg = ~jpeg_only 
        has_value_in_jpg = self.df_raw[jpeg_only].notna().any(axis=0)
        has_value_in_non_jpg = self.df_raw[non_jpeg].notna().any(axis=0)
        jpg_only_cols = has_value_in_jpg & ~has_value_in_non_jpg 
        df = self.df_raw.loc[:, jpg_only_cols].dropna(how = "all", axis = 0).drop(namespace_return["Exif"].columns, axis = 1) 
        file_ext_column = self.df_raw.loc[df.index, "tika:file_ext"]
        df = pd.concat([df, file_ext_column], axis = 1)#.set_index("tika:file_ext")
        namespace_return["Image"] = df
        return namespace_return
    
    def return_namespace_dfs(self, namespace : str, summary = False):
       return self.summary_columns(self.genereren_namespace_dfs[namespace]) if summary else self.genereren_namespace_dfs[namespace]
    
    #overbodig?
    def return_namespace_columns(self):
        df_columns = []
        for namespace_columns in self.genereren_namespace_dfs.values():
            df_columns.append(namespace_columns.columns)
        return df_columns
    
    def create_dataframe_leftover_fields(self, summary = False):
        index = []
        for columns in self.genereren_namespace_dfs.values():
            index.append(columns.columns)
        index = list(set(chain.from_iterable(index)))
        return self.summary_columns(self.df_raw.drop(index, axis = 1)).set_index("tika:file_ext") if summary else self.df_raw.drop(index, axis = 1).set_index("tika:file_ext")

    def visualiseren_duplicaten_DataFrames(self, df, summary = False): 
        columns = []
        for col_a, col_b in combinations(df.columns, 2):
            overlap = (df[col_a] == df[col_b]).sum()
            percentage_overlap = overlap / len(df) * 100
            if percentage_overlap > 70: 
                columns.append((col_a, col_b))
        unpack = list(chain.from_iterable(columns))
        remove_duplicates = list(dict.fromkeys(unpack))
        df = df[remove_duplicates]
        return self.summary_columns(df) if summary else df
    
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
    def field_coverage_by_filetype_df(self, summary = False):
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
        return df if summary else df #niet heel elegant maar zo krijg je tenminste geen type-error als je hier summary invult, fixen met logging?
    
    # def df_browser_viewer(self):
    # dtale.show(df)
    
    #def output_duplicate_analysis
       #viable choices list
       # request_list
    
    def df_excel_writer(self, request_list: list, summary = False):
        self.df_raw.sample(3000).to_excel(self.xlsx_path)
        with pd.ExcelWriter(self.xlsx_path, engine = "openpyxl", mode = "a") as writer:
            for request in request_list:
               self.output_dataframe_dict.get(request)(summary = summary).to_excel(writer, sheet_name = request)



#def df_browser_viewer(self):