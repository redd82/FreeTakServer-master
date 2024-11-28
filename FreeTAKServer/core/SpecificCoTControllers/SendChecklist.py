from FreeTAKServer.core.configuration.CreateLoggerController import CreateLoggerController
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.model.SpecificCoT.SendChecklist import SendChecklist

from .SendCoTAbstractController import SendCoTAbstractController

loggingConstants = LoggingConstants()
logger = CreateLoggerController("SendChecklistController").getLogger()


class SendChecklistController(SendCoTAbstractController):
    """this class is responsible for handling Checklist type cots"""
    def __init__(self, RawCoT):
        try:
            tempObject = super().Event.disconnect()
            object = SendChecklist()
            self.fill_object(object, tempObject, RawCoT, addToDB=False)
        except Exception as e:
            logger.error("there has been an exception in the creation of the send Checklist object " + str(e))
            return -1
