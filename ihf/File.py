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
        self.relative_path = ''
        self.absolute_path = ''
        self.url_path = ''
        self.update_path()
        if not os.path.exists(self.absolute_path):
            open(self.absolute_path, 'w').close()

    def mkdir_if_necessary(self):
        path = ''
        split = self.relative_path.split('/')
        for i, s in enumerate(split):
            path += '/'+s
            full_path = f'{self.path_to_general_folder}{path}'
            if not os.path.exists(full_path) and i < len(split) - 1:
                os.mkdir(full_path)

    def update_path(self):
        self.relative_path = f'{"/temp" if self.is_temp else ""}{"/private" if self.is_private else ""}/{self.folder + "/" if self.folder else ""}{self.file_name}'
        self.absolute_path = f'{self.path_to_general_folder}{self.relative_path}'
        self.url_path = f'{self.host}{self.relative_path}'
        self.mkdir_if_necessary()

    def update(self, file_name=None, folder=None, is_temp=None, is_private=None):
        args = locals()
        for arg in args.keys():
            if args[arg] is not None:
                self.__setattr__(arg, args[arg])
        previous_path = self.absolute_path
        self.update_path()
        os.rename(previous_path, self.absolute_path)

    def open(self, mode='w'):
        return open(self.absolute_path, mode)

    def remove(self):
        os.remove(self.absolute_path)


class FileManager:
    def __init__(self, host, path_to_general_folder):
        self.host = host
        self.path_to_general_folder = path_to_general_folder
        temp_folder_path = f'{path_to_general_folder}/temp'
        if not os.path.exists(path_to_general_folder):
            os.mkdir(path_to_general_folder)
        if os.path.exists(temp_folder_path):
            shutil.rmtree(temp_folder_path)

    def get_new_file(self, file_name, folder=None, is_temp=False, is_private=False):
        return File(file_name, self.host, self.path_to_general_folder, folder, is_temp, is_private)
