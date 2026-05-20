from pathlib import Path
import json
import subprocess
import os
import logging
import yaml


class metadata_pipeline():
    
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
   
    def __init__(self, log_folder_path, root_dir):
        self.log_folder_path = Path(log_folder_path)
        self.root_dir = Path(root_dir)
        self.json_logger = self.make_logger(name = "Remove_json")
        self.tika_logger = self.make_logger(name = "Tika_metadata")
        self.selectie_logger = self.make_logger(name = "Metadata_selectie")
        self.dataframe_logger = self.make_logger(name = "DataFrame_ingest")
        self.tika_location = Path(__file__).parent
       


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
            files_verwijderd = 0 
            files_list = []
            if alle_json_verwijderen:
                json_files = list(self.root_dir.rglob('*.json'))
                json_type = "json"
                logger.info(f"{len(json_files)} {json_type} files found")
                files_list += json_files
            else: 
                json_metadata_files = list(self.root_dir.rglob('*.metadata.json'))
                json_metadata_type = "metadata.json"
                logger.info(f"{len(json_metadata_files)} {json_metadata_type} files found")
                files_list += json_metadata_files
            if yaml_verwijderen:
                yaml_files = list(self.root_dir.rglob('*.metadata.yaml'))
                yaml_type = "metadata.yaml"
                logger.info(f"{len(yaml_files)} {yaml_type} files found")
                files_list += yaml_files
            for file in files_list:
                try:
                   file.unlink()
                   files_verwijderd += 1
                except Exception as e:
                    logger.error(f"Something went wrong with {file}: {e}", exc_info = True)
            logger.info(f"{files_verwijderd} files verwijderd")
            if files_verwijderd == 0:
                logger.info("did not delete any files")

    def metadata_genereren(self, output_dir = None): ##working directory aanpassen
        logger = self.tika_logger
        all_paths = list(self.root_dir.rglob('*'))
        logger.info(f"Scan: {len(all_paths)} paden gevonden! (mappen en bestanden)")
        folders_list = []
        files_list = []
        for folders in all_paths: 
            if folders.is_dir():
                folders_list.append(folders)
            elif folders.is_file():
                files_list.append(folders)
        logger.info(f"Scan: {len(folders_list)} folders found!")
        logger.info(f"Scan: {len(files_list)} files found!")
        files_list = list(set(files_list))
        logger.info(f"Scan: {len(files_list)} files left after removing duplicates")
        for index, paths in enumerate(folders_list): 
            try:
                    cmd_command = f'call configure.bat && java -jar tika.jar -i "{paths}" -o "{output_dir if output_dir is not None else paths}" -J -excludeFilePat ".json"' 
                    subprocess.run(cmd_command, shell = True, capture_output=True, timeout= 60, check=True, text = True, cwd= self.tika_location)
            except Exception as e:
                stder_output = getattr(e, "stderr", None)
                logger.error(f"Something went wrong with {paths}: {e}, stderr: {stder_output}", exc_info=True)
            if index % 2 == 0: #modulus omhoog voor grotere datasets, anders spam je de log vol met progress meldingen!
                logger.info(f"progress: {index}/{len(folders_list)} folders processed")
           
            
def metadata_selectie(root_dir: str | Path, log_folder_path : str | Path, output_as_yaml: False):
    logger = make_logger("metadata selectie", log_folder_path)
    root_dir = Path(root_dir) #Path conversie
    files = list(root_dir.rglob('*.json')) #List alle paden .json file
    logger.info(f"found {len(files)} .json file!")
    files_made = 0
    if not files:
        logger.warning("Geen json file gevonden in de map")
    for index, file in enumerate(files): #loop door json om metadata selectie file aan te maken
        with open(file, mode = 'r', encoding = 'UTF-8') as f:
            if file.suffixes[-2] == ".metadata": #eventuele .metadata file overslaan
                continue
            if file.suffixes[-2] == ".docx":  #let op: negatief indexen op de suffixes lijst anders worden bestandsnamen met punten erin niet meegenomen
                json_object = json.load(f)
                new_dict = {k: json_object[0].get(v) for k, v in docx_metadata.items()} #dict aanmaken op basis van docx_metadata structuur en de tika metadata
            elif file.suffixes[-2] == ".pdf":
                json_object = json.load(f)
                new_dict = {k: json_object[0].get(v) for k, v in pdf_metadata.items()}
            elif file.suffixes[-2] == ".msg":
                json_object = json.load(f)
                new_dict = {k: json_object[0].get(v) for k, v in msg_metadata.items()}
            else:
                continue
            try:
               if output_as_yaml:
                   sidecar_file_name_extension = file.stem + '.metadata.yaml'
               else:
                sidecar_file_name_extension = file.stem + '.metadata.json'
               #logger.debug(f"file stem: {file.stem}")
               file_match = [f for f in list(root_dir.rglob(f"{file.stem}*")) if f.is_file()]
               if not file_match:
                   logger.warning(f"geen match voor {file.stem} gevonden, bestand overgeslagen!")
                   continue
               output_directory = file_match[0].parent
               #logger.debug(f"output directory: {output_directory}")
               side_car_path = output_directory / sidecar_file_name_extension
               #logger.debug(f"sidecar path: {side_car_path}")
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

#note: de invoer van paden met '/' ipv '\' en als string 
def metadata_dataframe(root_dir: str | Path, log_folder_path : str | Path):
    logger = make_logger("metadata_dataframe", log_folder_path)
    root_dir = Path(root_dir)
    if root_dir.exists() == False:
        logger.error(f"{root_dir} does not exist!")
    files = list(root_dir.rglob('*.json'))
    if not files:
        logger.error("did not find any json files") 
    logger.info(f"found {len(files)} json files")
    metadata = []
    for file in files:
        try:
            with open(file, mode = 'r', encoding = 'UTF-8') as f:
                all_metadata = json.load(f)
                # if not all_metadata:
                #     logger.error(f"PATH: {file} does not exist, skipping")
                primary_metadata = all_metadata[0]
                metadata.append(primary_metadata)
        except Exception as e:
                logger.error(f"Something went wrong with {file}: {e}", exc_info = True)
    return metadata

#generator ipv een list??? explore


def run_pipeline(root_dir):
    metadata_genereren(root_dir)
    metadata_selectie(root_dir)
    metadata_dataframe(root_dir)