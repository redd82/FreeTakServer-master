from FreeTAKServer.core.configuration.CreateLoggerController import CreateLoggerController
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.model.SpecificCoT.SendFederatedCoT import SendFederatedCoT

from .SendCoTAbstractController import SendCoTAbstractController

loggingConstants = LoggingConstants()
logger = CreateLoggerController("SendDisconnectController").getLogger()

class SendFederatedCoT(SendCoTAbstractController):
    def __init__(self, RawCoT):
        try:
            tempObject = super().Event.FederatedCoT()
            object = SendFederatedCoT()
            self.fill_object(object, tempObject, RawCoT, addToDB=False)
        except Exception as e:
            logger.error("there has been an exception in the creation of the send federated cot object " + str(e))
