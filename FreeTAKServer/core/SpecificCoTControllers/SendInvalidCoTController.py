from FreeTAKServer.model.SpecificCoT.SendInvalidCoT import SendInvalidCoT
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.core.configuration.CreateLoggerController import CreateLoggerController

loggingConstants = LoggingConstants()
logger = CreateLoggerController("SendInvalidCoTController").getLogger()


class SendInvalidCoTController:
    def __init__(self, RawCOT):
        try:
            self.SendInvalidCoT = SendInvalidCoT()
            self.SendInvalidCoT.clientInformation = RawCOT.clientInformation
        except Exception as e:
            logger.error("there has been an exception in the creation"
                         " of the send Invalid CoT object " + str(e))
    def getObject(self):
        return self.SendInvalidCoT