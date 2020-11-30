import os
import glob
import logging
from pathlib import Path


class File:
    @staticmethod
    def exists(path: str):
        """
        check path exists
        :param path:
        :return:
        """
        path = path.strip()
        if os.path.exists(path) is True:
            return True
        else:
            return False

    @staticmethod
    def is_file(path: str):
        path = path.strip()
        if File.exists(path) is True and os.path.isfile(path) is True:
            return True
        else:
            return False

    @staticmethod
    def is_link(path: str):
        path = path.strip()
        if File.exists(path)is True and os.path.islink(path) is True:
            return True
        else:
            return False

    @staticmethod
    def is_directory(path: str):
        path = path.strip()
        if File.exists(path) is True and os.path.isdir(path) is True:
            return True
        else:
            return False

    @staticmethod
    def glob_file_paths(path: str):
        path = path.strip()
        file_paths = []
        for file_path in glob.iglob(path):
            file_paths.append(file_path)
        return file_paths

    @staticmethod
    def get_project_root_path():
        path = os.getcwd()
        return path[: path.find(os.sep + "src" + os.sep + "project" + os.sep)]

    @staticmethod
    def read_text(file_path: str, file_encoding: str = "UTF-8"):
        file_path = file_path.strip()
        if File.is_file(file_path) is False:
            logging.error("File doesn't exist! File path = [{0}]".format(file_path))
            return None
        else:
            try:
                with open(file_path, "r", encoding=file_encoding) as file:
                    text_lines = ""
                    for line in file.readlines():
                        text_lines += line
                return text_lines
            except Exception as e:
                logging.error("Failed to read text from file!"
                              "\nFile path = [{0}]"
                              "\nMore info = [{1}]"
                              .format(file_path, str(e)))

    @staticmethod
    def write_text(file_path: str, text: str, file_encoding: str = "UTF-8"):
        file_path = file_path.strip()
        if File.is_file(file_path) is False:
            logging.error("File doesn't exist! File path = [{0}]".format(file_path))
            return False
        else:
            try:
                with open(file_path, "w", encoding=file_encoding) as file:
                    file.write(text)
                return True
            except Exception as e:
                logging.error("Failed to write text from file!"
                              "\nFile path = [{0}]"
                              "\nMore info = [{1}]"
                              .format(file_path, str(e)))
                return False

    @staticmethod
    def append_text(file_path: str, text: str, file_encoding: str = "UTF-8"):
        file_path = file_path.strip()
        if File.is_file(file_path) is False:
            logging.error("File doesn't exist! File path = [{0}]".format(file_path))
            return False
        else:
            try:
                with open(file_path, "a", encoding=file_encoding) as file:
                    file.write(text)
                return True
            except Exception as e:
                logging.error("Failed to append text from file!"
                              "\nFile path = [{0}]"
                              "\nMore info = [{1}]"
                              .format(file_path, str(e)))
                return False

    @staticmethod
    def touch_file(file_path: str):
        try:
            Path(file_path).touch()
            return True
        except Exception as e:
            logging.error("Failed to touch file! Path = [{0}]."
                          "\nMore info = [{1}].".format(file_path, str(e)))
            return False
