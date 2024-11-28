import os
from FreeTAKServer.core.configuration.DataPackageServerConstants import DataPackageServerConstants
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from pathlib import PurePath
from FreeTAKServer.core.configuration.MainConfig import MainConfig
config = MainConfig.instance()

class CreateStartupFilesController:
    def __init__(self):
        self.file_dir = os.path.dirname(os.path.realpath(__file__))
        self.dp_directory = PurePath(self.file_dir, DataPackageServerConstants().DATAPACKAGEFOLDER)
        self.logs_directory = PurePath(config.LogFilePath)
        self.client_package = config.ClientPackages
        self.createFolder()

    def createFolder(self):
        try:
            os.mkdir(self.dp_directory)
        except:
            pass
        try:
            os.mkdir(self.logs_directory)
        except:
            pass
        try:
            if not os.path.exists(self.client_package):
                os.makedirs(self.client_package)
        except:
            raise Exception("failed to create client packages directory at "+str(config.ClientPackages))
        ERRORLOG = open(LoggingConstants().ERRORLOG, "w+")
        ERRORLOG.close()
        HTTPLOG = open(LoggingConstants().HTTPLOG, "w+")
        HTTPLOG.close()
        DEBUGLOG = open(LoggingConstants().DEBUGLOG, "w+")
        DEBUGLOG.close()
        INFOLOG = open(LoggingConstants().INFOLOG, "w+")
        INFOLOG.close()

    def create_daemon(self):
        f = open("/etc/systemd/system/FreeTAKServer.service", "w+")
        f.write("""
[Unit]
Description=FreeTAK Server service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
ExecStart=/usr/bin/python3 -m FreeTAKServer.controllers.services.FTS -DataPackageIP 0.0.0.0 -AutoStart True

[Install]
WantedBy=multi-user.target""")
        f.close()