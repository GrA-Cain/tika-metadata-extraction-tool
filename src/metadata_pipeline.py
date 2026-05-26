from pathlib import Path
import json
import subprocess
import os
import logging
import yaml
import pandas as pd


class MetaDataPipeline():
    
    #output metadata dictionary structuur
    DOCX_METADATA_STRUCTUUR = {
    "document_id": None,
    "filename" : "resourceName",
    "path" : "tika_batch_fs:relative_path",
    "format" : "tika:file_ext",
    "Media type" : "Content-Type",
    "ingested_at" : None, 
    "origin": None,
    "title": "dc:title",
    "creator" : "dc:creator", 
    "create date" : "dcterms:created",
    "summary" : None, 
    "page-count": "meta:page-count",
    "word-count": "meta:word-count",
    "Template" : "extended-properties:Template"}
    
    PDF_METADATA_STRUCTUUR = {
    "document_id": None, 
    "filename" : "resourceName",
    "path" : "tika_batch_fs:relative_path",
    "format" : "tika:file_ext",
    "Media type" : "Content-Type", 
    "Producer software" : "pdf:producer",
    "ingested_at" : None, 
    "origin": None, 
    "title": "dc:title",
    "language" : "dc:language",
    "description" : "dc:description", 
    "creator" : "dc:creator", 
    "create date" : "dcterms:created",
    "summary" : None, 
    "page-count": "xmpTPg:NPages",
    "Character per page" : "pdf:charsPerPage" ,
    "OCR page count" : "pdf:ocrPageCount",
    "creator tool" : "xmp:CreatorTool", 
    "Template" : "extended-properties:Template"}

    MSG_METADATA_STRUCTUUR = {
    "document_id": None,
    "filename": "resourceName",
    "path": "tika_batch_fs:relative_path",
    "format": "tika:file_ext",
    "media_type": "Content-Type",
    "ingested_at": None, 
    "origin": None, 
    "subject": "dc:title", 
    "sender": "Message:From", 
    "sender email": "Message:From-Email",
    "recipients_to": "Message-To",
    "recipients_cc": "Message-Cc",
    "recipient email" : "Message-Recipient-Address",
    "sent_date" : "Message:Raw-Header:Date",
    "received_date": "mapi:message-delivery-time",
    "summary": None, 
    "has_attachments": "Message:Raw-Header:X-MS-Has-Attach", 
    "body_format": "mapi:body-types-processed",  
    "reply_to": "Message:Raw-Header:In-Reply-To", 
    "message_id": "Message:Raw-Header:Message-ID",}
   
    def __init__(self, root_dir : str | Path, log_folder_path : str | Path):
        self.log_folder_path = Path(log_folder_path)
        self.root_dir = Path(root_dir)
        self.json_logger = self.make_logger(name = "JSON deleter")
        self.tika_logger = self.make_logger(name = "Tika metadata")
        self.selectie_logger = self.make_logger(name = "Metadata selectie")
        self.dataframe_logger = self.make_logger(name = "DataFrame ingest")
        self.dtale_browser_logger = self.make_logger(name = "Browser viewer")
        self.excelwriter_logger = self.make_logger(name = "Excelwriter")
        self.tika_location = Path(__file__).parents[1]
       


    def make_logger(self, name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.FileHandler(filename = self.log_folder_path / f"{name}.log")
            handler.setFormatter(logging.Formatter(("%(asctime)s - %(levelname)s - %(message)s")))
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        return logger

    def remove_json(self, alle_json_verwijderen = False, yaml_verwijderen = False):
            logger = self.json_logger
            files_deleted = 0 
            files_list = []
            if alle_json_verwijderen:
                json_files = list(self.root_dir.rglob('*.json'))
                logger.info(f"{len(json_files)} .json files found")
                files_list += json_files
            else: 
                json_metadata_files = list(self.root_dir.rglob('*.metadata.json'))
                logger.info(f"{len(json_metadata_files)} .metadata.json files found")
                files_list += json_metadata_files
            if yaml_verwijderen:
                yaml_files = list(self.root_dir.rglob('*.metadata.yaml'))
                logger.info(f"{len(yaml_files)} .yaml files found")
                files_list += yaml_files
            for file in files_list:
                try:
                   file.unlink()
                   files_deleted += 1
                except Exception as e:
                    logger.error(f"Something went wrong with {file}: {e}", exc_info = True)
            logger.info(f"{files_deleted} files deleted")
            if files_deleted == 0:
                logger.info("did not delete any files")

    def metadata_genereren(self, output_dir = None): ##working directory aanpassen
        logger = self.tika_logger
        all_paths = list(self.root_dir.rglob('*'))
        logger.info(f"Scan: {len(all_paths)} paden gevonden! (mappen en bestanden)")
        folders_list = []
        files_list_before = []
        for folders in all_paths: 
            if folders.is_dir():
                folders_list.append(folders)
            elif folders.is_file():
                files_list_before.append(folders)
        logger.info(f"Scan: {len(folders_list)} folders found!")
        logger.info(f"Scan: {len(files_list_before)} files found!")
        files_list_after = list(set(files_list_before))
        logger.info(f"Scan: warning: {len(files_list_before) - len(files_list_after)} duplicates found!")
        for index, paths in enumerate(folders_list): 
            try:
                    cmd_command = f'java -jar tika.jar -i "{paths}" -o "{output_dir if output_dir is not None else paths}" -J -excludeFilePat ".json"' 
                    subprocess.run(cmd_command, shell = True, capture_output=True, timeout= 60, check=True, text = True, cwd= self.tika_location)
            except Exception as e:
                stder_output = getattr(e, "stderr", None)
                logger.error(f"Something went wrong with {paths}: {e}, stderr: {stder_output}", exc_info=True)
            if index % 2 == 0: #modulus omhoog voor grotere datasets, anders spam je de log vol met progress meldingen!
                logger.info(f"progress: {index}/{len(folders_list)} folders processed")
           
            
    def metadata_selectie(self, output_as_yaml = False):
        logger = self.selectie_logger
        files = list(self.root_dir.rglob('*.json')) #List alle paden .json file
        logger.info(f"found {len(files)} .json file!")
        files_made = 0
        if not files:
            logger.warning("Geen json file gevonden in de map")
        for index, file in enumerate(files):
            new_dict = None 
            with open(file, mode = 'r', encoding = 'UTF-8') as f:
                if file.suffixes[-2] == ".metadata": 
                    continue
                if file.suffixes[-2] == ".docx":  
                    tika_json_file = json.load(f)
                    new_dict = {k: tika_json_file[0].get(v) for k, v in self.DOCX_METADATA_STRUCTUUR.items()} 
                elif file.suffixes[-2] == ".pdf":
                    tika_json_file = json.load(f)
                    new_dict = {k: tika_json_file[0].get(v) for k, v in self.PDF_METADATA_STRUCTUUR.items()}
                elif file.suffixes[-2] == ".msg":
                    tika_json_file = json.load(f)
                    new_dict = {k: tika_json_file[0].get(v) for k, v in self.MSG_METADATA_STRUCTUUR.items()}
                else:
                    continue
            if new_dict is None:
                continue
            try:
                if output_as_yaml:
                    sidecar_file_name_extension = file.stem + '.metadata.yaml'
                else:
                    sidecar_file_name_extension = file.stem + '.metadata.json'
                file_match = [match for match in list(self.root_dir.rglob(f"{file.stem}*")) if match.is_file()]
                if not file_match:
                    logger.warning(f"geen match voor {file.stem} gevonden, bestand overgeslagen!")
                    continue
                output_directory = file_match[0].parent
                side_car_path = output_directory / sidecar_file_name_extension
                with open(side_car_path, "w", encoding='utf-8') as path:
                    if output_as_yaml:
                        yaml.dump(new_dict, path, encoding = "utf-8", allow_unicode = True)
                    else:
                        json.dump(new_dict, path, indent=2, ensure_ascii=False)
                files_made += 1
            except Exception as e:
                logger.error(f"error: {e}")
            if index % 50 == 0:
                logger.info(f"progress: {index} of {len(files)} file processed!")
                logger.info(f"finished: {files_made} metadata file created!")

    def metadata_dataframe(self):
        logger = self.dataframe_logger
        if not self.root_dir.exists():
            logger.error(f"{self.root_dir} does not exist!")
            logger.info("aborting!")
            return None
        files = list(self.root_dir.rglob('*.json'))
        if not files:
            logger.error("did not find any json files")
            logger.info("aborting!")
            return None
        logger.info(f"found {len(files)} json files")
        metadata = []
        for file in files:
            try:
                with open(file, mode = 'r', encoding = 'UTF-8') as f:
                    all_metadata = json.load(f)
                    if not all_metadata:
                        logger.error(f"PATH: {file} does not exist or could not be loaded, skipping")
                        continue
                    primary_metadata = all_metadata[0]
                    metadata.append(primary_metadata)
            except Exception as e:
                    logger.error(f"Something went wrong with {file}: {e}", exc_info = True)
        return pd.DataFrame(metadata)