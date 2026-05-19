from pathlib import Path
import json
import subprocess
import os
import logging
import yaml


class metadata_pipeline():
   
   def __init__(self, log_folder_path, root_dir):
       self.log_folder_path = log_folder_path
       self.root_dir = root_dir
       self.json_logger = self.make_logger(name = "remove_json")
       self.tika_logger = self.make_logger(name = "tika_metadata")
       self.selectie_logger = self.make_logger(name = "metadata_selectie")
       self.dataframe_logger = self.make_logger(name = "DataFrame_ingest")
       

   def make_logger(self, name: str):
    logger = logging.getLogger(name)
    self.log_folder_path = Path(self.log_folder_path)
    if not logger.handlers:
        handler = logging.FileHandler(filename = self.log_folder_path / f"{name}.log")
        handler.setFormatter(logging.Formatter(("%(asctime)s - %(levelname)s - %(message)s")))
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
    return logger


##Selectie metadatavelden
#zie metadata_toframe.ipynb voor context
docx_metadata = {
#technical"
    "document_id": None, #populate at ingest
    "filename" : "resourceName",
    "path" : "tika_batch_fs:relative_path",
    "format" : "tika:file_ext",
    "Media type" : "Content-Type", #recente term voor MIME-type
    "ingested_at" : None, #populate at ingest
    "origin": None, #source location, system, URL? Departement, organisatie?
#descriptive"
    "title": "dc:title",
    "creator" : "dc:creator", 
    "create date" : "dcterms:created",
    "summary" : None, #fill with summerization output
#structural"
    "page-count": "meta:page-count",
    "word-count": "meta:word-count",
    "Template" : "extended-properties:Template" #alleen wanneer dit veld structureel gevuld is en een betekenisvolle naam heeft 
}
    

pdf_metadata = {
#technical"
    "document_id": None, #populate at ingest
    "filename" : "resourceName",
    "path" : "tika_batch_fs:relative_path",
    "format" : "tika:file_ext",
    "Media type" : "Content-Type", #recente term voor MIME-type
    "Producer software" : "pdf:producer",
    "ingested_at" : None, #populate at ingest
    "origin": None, #source location, system, URL? Departement, organisatie?
#descriptive"
    "title": "dc:title",
    "language" : "dc:language",
    "description" : "dc:description", #laag gevuld, misschien weghalen
    "creator" : "dc:creator", 
    "create date" : "dcterms:created",
    "summary" : None, #fill with summerization output
#structural"
    "page-count": "xmpTPg:NPages",
    "Character per page" : "pdf:charsPerPage" ,
    "OCR page count" : "pdf:ocrPageCount",
    "creator tool" : "xmp:CreatorTool", #low signal?
    "Template" : "extended-properties:Template"
}

msg_metadata = {
#technical
        "document_id": None, #omitten en vervangen door message-id?
        "filename": "resourceName",
        "path": "tika_batch_fs:relative_path",
        "format": "tika:file_ext",
        "media_type": "Content-Type",
        "ingested_at": None, #populate at ingest
        "origin": None, #source location, system, URL? Departement, organisatie?
#descriptive
        "subject": "dc:title", #dc:subject geeft dezelfde waarden m.u.v het missen van "RE:" op reply emails
        "sender": "Message:From", #Message:Raw-Header:From -> voor naam + emailadres
        "sender email": "Message:From-Email",
        "recipients_to": "Message-To",
        "recipients_cc": "Message-Cc",
        "recipient email" : "Message-Recipient-Address",
        "sent_date" : "Message:Raw-Header:Date",
        "received_date": "mapi:message-delivery-time",
        "summary": None, #fill with summerization output #deze nodig voor emails?
#structural"
        "has_attachments": "Message:Raw-Header:X-MS-Has-Attach", #BOOL
        "body_format": "mapi:body-types-processed",  # plain text of HTML body
        "reply_to": "Message:Raw-Header:In-Reply-To",  #ID van email 
        "message_id": "Message:Raw-Header:Message-ID",   # for thread reconstruction
}

#note: de invoer van paden met '/' ipv '\' en als string 
def remove_json(root_dir: str | Path, log_folder_path: str | Path, alle_json_verwijderen = False, yaml_verwijderen = False):
        root_dir = Path(root_dir)
        logger = make_logger("remove_json", log_folder_path)
        files_verwijderd = 0 
        if alle_json_verwijderen:
            files = list(root_dir.rglob('*.json'))
            type = "json"
            logger.info(f"{len(files)} {type} files found")
        else: 
            files = list(root_dir.rglob('*.metadata.json'))
            type = "metadata.json"
            logger.info(f"{len(files)} {type} files found")
        if yaml_verwijderen:
            files = list(root_dir.rglob('*.metadata.yaml'))
            type = "metadata.yaml"
            logger.info(f"{len(files)} {type} files found")
        for file in files:
            try:
               file.unlink()
               files_verwijderd += 1
            except Exception as e:
                logger.error(f"Something went wrong with {file}: {e}", exc_info = True)
        logger.info(f"{files_verwijderd} {type} files verwijderd")
        if files_verwijderd == 0:
            logger.info("did not delete any files")

#if java is installed,
def metadata_genereren(root_dir: str | Path, logging_folder_path: str | Path): ##working directory aanpassen
    root_dir = Path(root_dir)
    logger = make_logger("metadata_genereren", logging_folder_path)
    all_paths = list(root_dir.rglob('*'))
    logger.info(f"Scan: {len(all_paths)} paden gevonden! (mappen en bestanden)")
    folders_list = []
    files_list = []
    for folders in all_paths: #loop door alle paden, mapjes afvangen
        if folders.is_dir():
            folders_list.append(folders)
        elif folders.is_file():
            files_list.append(folders)
    logger.info(f"Scan: {len(folders_list)} folders found!")
    logger.info(f"Scan: {len(files_list)} files found!")
    files_list = list(set(files_list))
    logger.info(f"Scan: {len(files_list)} files left after removing duplicates")
    for index, paths in enumerate(folders_list): #tika werkt met folders, dus folders lijst als input voor de cmd call
        try:
            cmd_command = f'call configure.bat && java -jar tika.jar -i "{paths}" -o "{paths}" -J -excludeFilePat ".json"'  #output path optie!
            subprocess.run(cmd_command, shell = True, capture_output=True, timeout= 60, check=True, text = True, cwd='C:/Users/m.venema') #tika in de cmd uitvoeren
        except Exception as e:
            stder_output = getattr(e, "stderr", None)
            logger.error(f"Something went wrong with {paths}: {e}, stderr: {stder_output}", exc_info=True)
        if index % 2 == 0: #set modulus number higher when when working with large datasets
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