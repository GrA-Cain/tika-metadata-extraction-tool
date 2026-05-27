import streamlit as st
from metadata_pipeline import MetaDataPipeline
from DataFrame_class_pipeline import DataFramePipeline
import time

st.title("Metadata Tool GrA")

tab1, tab2, tab3, tab4 = st.tabs([
    "Genereren metadata (Tika)",
    "Metadata visualisatie", 
    "Metadata selectie",
    "Metadata files verwijderen"
])

with tab1:
    st.markdown("### **Pipeline starten**")
    st.caption("Mocht er iets mis gaan, check je log folder!")
    st.caption("Paden met / invullen ipv \ ")
    root_dir = st.text_input("Root directory (pad)", key = "tika_root_dir")
    log_folder_path = st.text_input("Log folder (pad)", key = "tika_log_folder_path")
    if st.button("Pipeline starten!" ,key = "tika_pipeline_button"):
        st.session_state.tika_pipeline = MetaDataPipeline(root_dir=root_dir, log_folder_path=log_folder_path)
        st.success("Pipeline geïnitialiseerd!")
    if "tika_pipeline" not in st.session_state:
        st.warning("initialiseer eerst de pijplijn!")
    else: 
        st.markdown("### **Metadata genereren met Apachi Tika**")
        output_dir = st.text_input("Alternatief pad voor output metadata (niet in de sidecar formaat zoals standaard)")
        if st.button("Metadata genereren"):
            with st.spinner("Bezig...", show_time = True):
                try:
                    st.session_state.tika_pipeline.metadata_genereren(output_dir = output_dir if output_dir else None)
                    st.success("Klaar!")
                except Exception as e:
                    st.error(f"Er is iets misgegaan: {e}")
                    st.warning("vergeet niet je logfolder te checken!")
        confirm = st.checkbox("Pipeline resetten?", key = "tika_reset_checkbox")
        st.markdown("### **Reset de streamlit session state**")
        if st.button("Reset pipeline", disabled=not confirm, key = "tika_reset_button"):
            del st.session_state.df_pipeline
            st.success("Pipeline gereset!")

with tab2:
    st.markdown("### **Pipeline starten**")
    root_dir = st.text_input("Root directory (pad)", value = "C:/Users/m.venema/Desktop/bestanden_root_dir",  key = "visualisatie_root_dir") #value = testing
    log_folder_path = st.text_input("Log folder (pad)", value = "C:/Users/m.venema/Desktop/pipeline_test/logging_folder", key = "visualisatie_log_folder_path") #value = testing
    xlsx_path = st.text_input("Excel output folder", value = "C:/Users/m.venema/Desktop/pipeline_test/xlsx_path",  key = "visualisatie_xlsx_folder")
    if st.button("Pipeline starten!", key = "vis_pipeline_button"):
        st.session_state.df_pipeline = DataFramePipeline(root_dir=root_dir, log_folder_path=log_folder_path, xlsx_path=xlsx_path)
        st.success("Pipeline geïnitialiseerd!")
    st.markdown("### **Excel output genereren**")
    if "df_pipeline" not in st.session_state:
       st.warning("initialiseer eerst de pijplijn!")
    else:
        st.caption(f"Note: het DataFrame [Percentage of non-NA fields per filetype] is niet compatibel met statistieken of sample fractie")
        excel_request = st.multiselect("selecteer outputs", options = st.session_state.df_pipeline.output_options)
        incompatible_selected = "Percentage of non-NA fields per filetype" in excel_request
        workbook_name = st.text_input("Naam .xlsx file")
        summary = st.checkbox("Beschrijvende statistiek toevoegen", key = "excel_summary_checkbox", disabled=incompatible_selected )
        use_sample = st.checkbox("Gebruik sample fractie", key = "sample_fractie_checkbox", disabled=incompatible_selected)
        if use_sample:
            sample_frac = st.slider("Sample fractie", min_value=0.05, max_value=1.0, value=0.5, step=0.05)
        else:
            sample_frac = None
        if st.button("Genereer .xlsx files van geselecteerde DataFrames"):
            st.session_state.df_pipeline.df_excel_writer(request_list = excel_request,
                                                         workbook_name = workbook_name,
                                                         summary = summary,
                                                         sample_frac = sample_frac)
        st.markdown("### **Previewer**")
        preview_request = st.selectbox("Selecteer DataFrame", key = "preview_request", options=st.session_state.df_pipeline.output_options)
        incompatible_request = preview_request == "Percentage of non-NA fields per filetype"
        incompatible_request_2 = preview_request == "Full DataFrame"
        duplicate_check = st.checkbox("Duplicaten analyse", key = "preview_request_duplicate", disabled = incompatible_request)
        summary_browser = st.checkbox("Beschrijvende statistiek", key="browser_summary_checkbox", disabled = incompatible_request or incompatible_request_2 or duplicate_check)
        st.caption("duplicate check DataFrames zijn zwaar om te berekenen en kunnen even duren!")
        if st.button("Preview DataFrame"):
            start = time.time()
            with st.spinner("DataFrame laden...!"):
                output = st.session_state.df_pipeline.df_browser_viewer(
                preview_request=preview_request,
                summary=summary_browser,
                duplicate_check=duplicate_check)
            st.dataframe(output)
            elapsed = time.time() - start
            st.caption(f"Geladen in {elapsed:.1f} seconden")

        confirm = st.checkbox("Pipeline resetten?", key = "DataFramepipeline_reset_checkbox")
        st.markdown("### **Reset de streamlit session state**")
        if st.button("Reset pipeline", disabled=not confirm, key = "DataFrame_reset_button"):
            del st.session_state.df_pipeline
            st.success("Pipeline gereset!")

with tab3:
    st.markdown("### **Pipeline starten**")
    st.caption("Mocht er iets mis gaan, check je log folder!")
    st.caption("Paden met / invullen ipv \ ")
    root_dir = st.text_input("Root directory (pad)", key = "selectie_root_dir")
    log_folder_path = st.text_input("Log folder (pad)", key = "selectie_log_folder_path")
    if st.button("Pipeline starten!" ,key = "selectie_pipeline_button"):
        st.session_state.selectie_pipeline = MetaDataPipeline(root_dir=root_dir, log_folder_path=log_folder_path)
        st.success("Pipeline geïnitialiseerd!")
    if "selectie_pipeline" not in st.session_state:
        st.warning("initialiseer eerst de pijplijn!")
    else:
        st.markdown("### **.metadata bestanden genereren**")
        st.caption("standaard output formaat: .json")
        output_as_yaml = st.checkbox("output metadata files als .yaml")
        if st.button("Metadata selectie genereren", key="selectie_button"):
            with st.spinner("Bezig..."):
                st.session_state.selectie_pipeline.metadata_selectie(output_as_yaml=output_as_yaml)
            st.success("Klaar!")
        st.markdown("### **Reset de streamlit session state**")
        confirm = st.checkbox("Pipeline resetten?", key = "selectie_pipeline_reset_checkbox")
        if st.button("Reset pipeline", disabled=not confirm, key = "selectie_reset_button"):
            del st.session_state.df_pipeline
            st.success("Pipeline gereset!")
with tab4:
    st.markdown("### **Pipeline starten**")
    st.caption("Mocht er iets mis gaan, check je log folder!")
    st.caption("Paden met / invullen ipv \ ")
    root_dir = st.text_input("Root directory (pad)", key = "verwijderaar_root_dir")
    log_folder_path = st.text_input("Log folder (pad)", key = "verijderaar_log_folder_path")
    if st.button("Pipeline starten!" ,key = "jsonverwijderen_pipeline_button"):
        st.session_state.verwijderaar_pipeline = MetaDataPipeline(root_dir=root_dir, log_folder_path=log_folder_path)
        st.success("Pipeline geïnitialiseerd!")
    if "verwijderaar_pipeline" not in st.session_state:
        st.warning("initialiseer eerst de pijplijn!")
    else:
        st.markdown("### **JSON en YAML files verwijderen**")
        st.caption("standaard gedrag: verwijderd alleen .metadata.json files en laat je .json files (gemaakt door tika) met rust")
        alle_json_verwijderen = st.checkbox("alle json files verwijderen (.json en .metadata.json)", key = "verwijderaar_.metadatacheckbox")
        yaml_verwijderen = st.checkbox("Alle yaml files verwijderen", key = "verwijderaar_yamlcheckbox")
        if st.button("Metadata files verwijderen", key="verwijderaar_button"):
            with st.spinner("Bezig..."):
                st.session_state.verwijderaar_pipeline.remove_json(alle_json_verwijderen=alle_json_verwijderen ,yaml_verwijderen=yaml_verwijderen)
            st.success("Klaar!")
        st.markdown("### **Reset de streamlit session state**")
        confirm = st.checkbox("Pipeline resetten?", key = "verwijderaar_pipeline_reset_checkbox")
        if st.button("Reset pipeline", disabled=not confirm, key = "verwijderaar_reset_button"):
            del st.session_state.df_pipeline
            st.success("Pipeline gereset!")
