import streamlit as st
from metadata_pipeline import MetaDataPipeline
from DataFrame_class_pipeline import DataFramePipeline

st.title("Metadata Tool GrA")

tab1, tab2, tab3, tab4 = st.tabs([
    "Genereren metadata (Tika)",
    "Metadata visualisatie", 
    "Metadata selectie",
    "Metadata files verwijderen"
])

with tab1:
    st.caption("Mocht er iets mis gaan, check je log folder!")
    st.caption("Paden met / invullen ipv \ ")
    root_dir = st.text_input("Root directory (pad)", key = "tika_root_dir")
    log_folder_path = st.text_input("Log folder (pad)", key = "tika_log_folder_path")
    if st.button("Pipeline starten!" ,key = "tika_pipeline_button"):
        st.session_state.tika_pipeline = MetaDataPipeline(root_dir=root_dir, log_folder_path=log_folder_path)
        st.success("Pipeline geïnitialiseerd!")
    output_dir = st.text_input("Alternatief pad voor output metadata (niet in de sidecar formaat zoals standaard)")
    if "tika_pipeline" not in st.session_state:
        st.warning("initialiseer eerst de pijplijn!")
    else: 
        if st.button("Metadata genereren"):
            with st.spinner("Bezig...", show_time = True):
                try:
                    st.session_state.tika_pipeline.metadata_genereren(output_dir = output_dir if output_dir else None)
                    st.success("Klaar!")
                except Exception as e:
                    st.error(f"Er is iets misgegaan: {e}")

with tab2:
    root_dir = st.text_input("Root directory (pad)", value = "C:/Users/m.venema/Desktop/bestanden_root_dir",  key = "visualisatie_root_dir") #value = testing
    log_folder_path = st.text_input("Log folder (pad)", value = "C:/Users/m.venema/Desktop/pipeline_test/logging_folder", key = "visualisatie_log_folder_path") #value = testing
    xlsx_path = st.text_input("Excel output folder", value = "C:/Users/m.venema/Desktop/pipeline_test/xlsx_path",  key = "visualisatie_xlsx_folder") #value = testing
    if st.button("Pipeline starten!", key = "vis_pipeline_button"):
        st.session_state.df_pipeline = DataFramePipeline(root_dir=root_dir, log_folder_path=log_folder_path, xlsx_path=xlsx_path)
        st.success("Pipeline geïnitialiseerd!")
    if "df_pipeline" not in st.session_state:
       st.warning("initialiseer eerst de pijplijn!")
    else:
        request_list = st.multiselect("selecteer outputs", options = st.session_state.df_pipeline.output_options)
        workbook_name = st.text_input("Naam .xlsx file")
        summary = st.checkbox("Beschrijvende statistiek toevoegen")
        use_sample = st.checkbox("Gebruik sample fractie")
        if use_sample:
            sample_frac = st.slider("Sample fractie", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
        else:
            sample_frac = None
        if st.button("Genereer .xlsx files van geselecteerde DataFrames"):
            st.session_state.df_pipeline.df_excel_writer(request_list = request_list,
                                                         workbook_name = workbook_name,
                                                         summary = summary,
                                                         sample_frac = sample_frac)
            
        # if st.selectbox("View DataFrame (local in browser)"):
            
        # if st.selectbox("View duplicaten analyse (local in browser)"):
            
            
            


def df_excel_writer(self, request_list: list, workbook_name: str, summary = False, sample_frac: float = None):
        logger = self.metadata.excelwriter_logger
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
                output = func(summary = summary)
                if output.empty:
                   logger.warning(f"{request} DataFrame empty! Cannot write to excel")
                   continue
                if sample_frac:
                    output.sample(frac = sample_frac).to_excel(writer, sheet_name = request)
                else:
                    output.to_excel(writer, sheet_name = request)
    
#with tab3:
#with tab4: