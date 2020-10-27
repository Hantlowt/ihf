import os
import shutil


class File:
    def __init__(self, file_name, host, path_to_general_folder, folder=None, is_temp=False, is_private=False):
        self.file_name = file_name
        self.folder = folder
        self.is_temp = is_temp
        self.is_private = is_private
        self.host = host
        self.path_to_general_folder = path_to_general_folder
        self.relative_path = f'{"/temp" if self.is_temp else ""}{"/private" if self.is_private else ""}/{self.folder + "/" if self.folder else ""}{file_name}'
        self.absolute_path = f'{path_to_general_folder}{self.relative_path}'
        self.url_path = f'{host}{self.relative_path}'

    def open(self, mode='w'):
        return open(self.absolute_path, mode)


class FileManager:
    def __init__(self, host, path_to_general_folder):
        self.host = host
        self.path_to_general_folder = path_to_general_folder
        temp_folder_path = f'{path_to_general_folder}/temp'
        private_temp_folder_path = f'{temp_folder_path}/private'
        private_folder_path = f'{path_to_general_folder}/private'
        if not os.path.exists(path_to_general_folder):
            os.mkdir(path_to_general_folder)
        if os.path.exists(temp_folder_path):
            shutil.rmtree(temp_folder_path)
        os.mkdir(temp_folder_path)
        os.mkdir(private_temp_folder_path)
        if not os.path.exists(private_folder_path):
            os.mkdir(private_folder_path)

    def get_new_file(self, file_name, folder=None, is_temp=False, is_private=False):
        return File(file_name, self.host, self.path_to_general_folder, folder, is_temp, is_private)
