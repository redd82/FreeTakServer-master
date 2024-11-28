from FreeTAKServer.core.configuration.CreateLoggerController import CreateLoggerController
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.model.SpecificCoT.SendExcheckUpdate import SendExcheckUpdate

from FreeTAKServer.core.SpecificCoTControllers.SendCoTAbstractController import SendCoTAbstractController

loggingConstants = LoggingConstants()
logger = CreateLoggerController("SendExcheckUpdateController").getLogger()

class SendExcheckUpdateController(SendCoTAbstractController):
    def __init__(self, RawCoT):
        try:
            tempObject = super().Event.ExcheckUpdate()
            object = SendExcheckUpdate()
            self.fill_object(object, tempObject, RawCoT, addToDB=False)
        except Exception as e:
            logger.error("there has been an exception in the creation of the send Emergency object " + str(e))
