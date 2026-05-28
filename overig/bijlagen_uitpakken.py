import extract_msg
from pathlib import Path
import os


##globbed door root_dir en saved in één centraal mapje (save_directory)
### cybersecurity -> 

def bijlagen_uitpakken(root_dir, save_directory):
   root_dir = Path(root_dir)
   save_directory = Path(save_directory)
   all_directories = root_dir.rglob('*')
   folders_list = []
   msg_files = []
   for folders in all_directories:
       if folders.is_dir():
          folders_list.append(folders)
   for directories in folders_list: 
       files = os.listdir(directories) 
       for file in files: 
           if file.endswith('.msg'): 
               x = os.path.join(directories, file)
               msg_files.append(x)
   #print(msg_files) #debug paden checken
   #print(folders_list) #debug paden checken
   for items in msg_files:
      with extract_msg.openMsg(items) as msg:
           for attachment in msg.attachments:
        # Define the path to save the attachment
              file_path = save_directory 
        # Save the attachment
              attachment.save(customPath=file_path)
              print(f'Saved attachment to {file_path}')


#bijlagen_uitpakken("C:/Users/m.venema/Desktop/bestanden_root_dir/formaten", "C:/Users/m.venema/Desktop/test/bijlagen/")
