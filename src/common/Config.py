import configparser
import logging
import sys
from src.common.File import File


class Config:
    def __init__(self, path_config_file: str):
        self.path_config_file = path_config_file.strip()
        # check path of config file
        if File.exists(path_config_file) is False:
            logging.error("Config file doesn't exist! Path = [{0}].".format(path_config_file))
            sys.exit(1)
        if File.is_file(path_config_file) is False:
            logging.error("The path isn't a file! Path = [{0}].".format(path_config_file))
            sys.exit(1)

        # init instance
        self.config = configparser.ConfigParser()
        self.config.read(self.path_config_file)

    def __del__(self):
        pass

    def __write_config(self):
        """
        write config info into config file
        :return:
        """
        try:
            with open(self.path_config_file, "w") as file_config:
                self.config.write(file_config)
        except Exception as e:
            logging.error("Failed to write config info into config file [{0}]."
                          "\nMore info = [{1}].".format(self.path_config_file, str(e)))

    """  about group  """
    def add_group(self, group_name: str):
        if group_name in self.config.sections():
            logging.error("Failed to add group of config file! "
                          "Group [{0}] is already existed in config file [{1}]."
                          .format(group_name, self.path_config_file))
            return
        # add group
        self.config.add_section(group_name)
        self.__write_config()
        logging.info("Added new group [{0}] in the config file [{1}].".format(group_name, self.path_config_file))

    def delete_group(self, group_name: str):
        if group_name not in self.config.sections():
            logging.error("Failed to delete group of config file! "
                          "Group [{0}] doesn't exist in config file [{1}]."
                          .format(group_name, self.path_config_file))
            return
        # delete group
        self.config.remove_section(group_name)
        self.__write_config()
        logging.info("Deleted group [{0}] in the config file [{1}].".format(group_name, self.path_config_file))

    """  about property  """
    def add_property(self, group_name: str, property_name: str):
        if group_name not in self.config.sections():
            logging.error("Failed to add property of config file! "
                          "Group [{0}] doesn't exist in config file [{1}].".format(group_name, self.path_config_file))
            return

        if property_name in self.config.options(group_name):
            logging.error("Failed to add property of config file! "
                          "Property [{0}] is already existed in group [{1}] in config file [{2}]."
                          .format(property_name, group_name, self.path_config_file))
            return

        # add new property
        self.config.set(group_name, property_name, "")
        self.__write_config()
        logging.info("Added new property [{0}] in group [{1}] the config file [{2}]."
                     .format(property_name, group_name, self.path_config_file))

    def delete_property(self, group_name: str, property_name: str):
        if group_name not in self.config.sections():
            logging.error("Failed to delete property of config file! "
                          "Group [{0}] doesn't exist in config file [{1}].".format(group_name, self.path_config_file))
            return

        if property_name not in self.config.options(group_name):
            logging.error("Failed to delete property of config file! "
                          "Property [{0}] doesn't exist in group [{1}] in config file [{2}]."
                          .format(property_name, group_name, self.path_config_file))
            return

        # add new property
        self.config.remove_option(group_name, property_name)
        self.__write_config()
        logging.info("Deleted property [{0}] in group [{1}] the config file [{2}]."
                     .format(property_name, group_name, self.path_config_file))

    def get_property(self, group_name: str, property_name: str):
        if group_name not in self.config.sections():
            logging.error("Failed to get property of config file! "
                          "Group [{0}] doesn't exist in config file [{1}].".format(group_name, self.path_config_file))
            return

        if property_name not in self.config.options(group_name):
            logging.error("Failed to get property of config file! "
                          "Property [{0}] doesn't exist in the group name [{1}] in config file [{2}]."
                          .format(property_name, group_name, self.path_config_file))
            return

        return self.config.get(group_name, property_name)

    def set_property(self, group_name: str, property_name: str, property_value: str):
        if group_name not in self.config.sections():
            logging.error("Failed to set property of config file! "
                          "Group [{0}] doesn't exist in config file [{1}].".format(group_name, self.path_config_file))
            return

        if property_name not in self.config.options(group_name):
            logging.error("Failed to set property of config file! "
                          "Property [{0}] doesn't exist in the group name [{1}] in config file [{2}]."
                          .format(property_name, group_name, self.path_config_file))
            return

        self.config.set(group_name, property_name, property_value)
        self.__write_config()
