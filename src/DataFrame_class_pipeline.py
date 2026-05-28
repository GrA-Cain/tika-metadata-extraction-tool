import pandas as pd
from pathlib import Path
from metadata_pipeline import MetaDataPipeline
import openpyxl
import xlsxwriter
from itertools import combinations, chain
from functools import cached_property
import dtale
from openpyxl import Workbook

#note: namespaces en groups zijn synoniemen voor groeperingen van metadatavelden
class DataFramePipeline():
    METADATA_GROUPS_DICT = {"Message group": "Message:|Message-",
                "Mapi group" : "mapi:",
                "dc group" : "^dc:|dcterms",
                "pdf group" : "^pdf:|pdfaid|pdfa:|pdfuaid",
                "xmp group" : "^xmp:|xmpMM:|xmpTPg",
                "X-tika group" :"X-TIKA:|tika|tika_|tika_batch",
                "meta group" : "meta:",
                "Extendend properties group" : "extended-properties:",
                "MSIP group" : "^(?!pdf:).*MSIP_Label",
                "Exif group": "Exif|exif",
                "Image group" : "Image"
                } #you can add metadata groups here using the following format "name" (key) : "regex str"(value). May require some tweaking to get the right regex, use LLMs for this! 
    
    def __init__(self, root_dir : str | Path, log_folder_path : str | Path, xlsx_path : str | Path):
        self.metadata = MetaDataPipeline(root_dir, log_folder_path)
        self.xlsx_path = Path(xlsx_path)
        self.output_options = ["Full DataFrame", "Percentage of non-NA fields per filetype", "Ungrouped fields(not part of a group, so leftovers)"] + self.filetype_list + list(self.METADATA_GROUPS_DICT.keys())
        self.function_calls = [lambda summary = False: self.df_raw,
                               lambda summary = False: self.field_coverage_by_filetype_df,
                               lambda summary = False: self.create_dataframe_leftover_fields(summary = summary)]
        self.function_calls.extend(lambda summary = False, ft = filetype: self.return_filetype_dfs(filetype = ft, summary = summary) for filetype in self.filetype_list)
        self.function_calls.extend(lambda summary = False, ns = namespace: self.return_namespace_dfs(namespace = ns, summary= summary) for namespace in self.METADATA_GROUPS_DICT.keys())
        self.additional_options = ["Duplicate analysis", "Add summary columns"] #unused
        self.output_dataframe_dict = {key: value for key, value in zip(self.output_options, self.function_calls)}

    @cached_property
    def df_raw(self):
       return pd.DataFrame(data = self.metadata.metadata_dataframe())

    @cached_property
    def filetype_list(self): 
        return list(self.df_raw["tika:file_ext"].unique())
    
    @staticmethod
    def summary_columns(df): #only compatible on dataframes that have metadata fields as columns!
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
            df_index = df.replace("", None).notna().sum(axis = 0).sort_values(ascending = False).index
            df = df[df_index]
            df = df.set_index("resourceName")
            filetype_dict[regex_str] = df
        return filetype_dict
    
    def return_filetype_dfs(self, filetype : str, summary = False):
         return self.summary_columns(self.genereren_filetype_dfs[filetype]) if summary else self.genereren_filetype_dfs[filetype]
    
    @cached_property
    def genereren_namespace_dfs(self):
        namespace_return = {}
        for name, regex_str in self.METADATA_GROUPS_DICT.items():
            df = self.df_raw.filter(axis = 1, regex = regex_str).replace("", None).dropna(how = "all", axis = 0) 
            df = df[df.isna().sum().sort_values(ascending=True).index] 
            column = self.df_raw.loc[df.index, "resourceName"] #"tika:file_ext",
            df = pd.concat([df, column], axis = 1) 
            df = df.set_index("resourceName") 
            namespace_return[name] = df
        #making image namespace (all metadata (excluding exif) that are found in jpg files but not in any other filetype)
        jpeg_only = self.df_raw.set_index("tika:file_ext").index.str.lower().str.match("jpg") 
        non_jpeg = ~jpeg_only 
        has_value_in_jpg = self.df_raw[jpeg_only].notna().any(axis=0)
        has_value_in_non_jpg = self.df_raw[non_jpeg].notna().any(axis=0)
        jpg_only_cols = has_value_in_jpg & ~has_value_in_non_jpg 
        df = self.df_raw.loc[:, jpg_only_cols].dropna(how = "all", axis = 0).drop(namespace_return["Exif group"].columns, axis = 1, errors ="ignore") 
        tika_filename_columns = self.df_raw.loc[df.index, "resourceName"]
        df = pd.concat([df, tika_filename_columns], axis = 1).set_index("resourceName")
        namespace_return["Image group"] = df
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
        return self.summary_columns(self.df_raw.drop(index, axis = 1)).set_index("resourceName") if summary else self.df_raw.drop(index, axis = 1).set_index("resourceName")



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
        combined.append(pd.Series("Leftover", index = self.create_dataframe_leftover_fields().columns)) 
        combined.append(pd.Series("X-tika group", index = ["resourceName"]))
        combined = pd.concat(combined)
        return combined
    
    @cached_property
    def field_coverage_by_filetype_df(self):
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
    
    def df_browser_viewer(self, preview_request, summary = False, duplicate_check = False):
        logger =  self.metadata.make_logger(name = "Browser viewer")
        if preview_request not in self.output_dataframe_dict:
            logger.warning(f"Requested ({preview_request}) DataFrame does not exist")
            return
        return self.visualiseren_duplicaten_DataFrames(self.output_dataframe_dict.get(preview_request)()) if duplicate_check else self.output_dataframe_dict.get(preview_request)(summary = summary)

    def df_excel_writer(self, request_list: list, workbook_name: str, summary = False, sample_frac: float = None):
        logger = self.metadata.make_logger(name = "Excelwriter")
        xlsx_path = self.xlsx_path / (workbook_name if workbook_name.endswith(".xlsx") else workbook_name + ".xlsx")
        if sample_frac and not 0 < sample_frac <= 1:
            logger.warning("Sample_frac needs to be between 0 and 1 (float)")
            return
        request_dict = {request: DataFrame for request, DataFrame in self.output_dataframe_dict.items() if request in request_list}
        if not xlsx_path.exists():
            wb = Workbook()
            wb.save(xlsx_path)
        with pd.ExcelWriter(xlsx_path, engine = "openpyxl", mode = "a") as writer:
            for request, func in request_dict.items():
                output = func(summary = False)
                if output.empty:
                   logger.warning(f"{request} DataFrame empty! Cannot write to excel")
                   continue
                if sample_frac:
                    self.summary_columns(output.sample(frac = sample_frac)).to_excel(writer, sheet_name = request) if summary else output.sample(frac = sample_frac).to_excel(writer, sheet_name = request)
                else:
                    self.summary_columns(output).to_excel(writer, sheet_name = request) if summary else output.to_excel(writer, sheet_name = request)


