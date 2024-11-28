import selectors
import socket
import ssl
import threading
import uuid
from typing import Dict, List

from FreeTAKServer.core.configuration.CreateLoggerController import CreateLoggerController
from FreeTAKServer.core.configuration.LoggingConstants import LoggingConstants
from FreeTAKServer.core.configuration.MainConfig import MainConfig
from FreeTAKServer.core.persistence.DatabaseController import DatabaseController
from FreeTAKServer.core.services.federation.external_data_handlers import (
    FederationProtobufConnectionHandler,
    FederationProtobufDisconnectionHandler, FederationProtobufStandardHandler,
    FederationProtobufValidationHandler)
from FreeTAKServer.core.services.federation.federation_service_base import FederationServiceBase
from FreeTAKServer.core.services.federation.handlers import (
    DataValidationHandler, DestinationValidationHandler, DisconnectHandler,
    HandlerBase, SendConnectionDataHandler, SendDataHandler,
    SendDisconnectionDataHandler, StopHandler)
from FreeTAKServer.model.ClientInformation import ClientInformation
from FreeTAKServer.model.federate import Federate
from FreeTAKServer.model.protobufModel.fig_pb2 import FederatedEvent
from FreeTAKServer.model.SpecificCoT.SpecificCoTAbstract import SpecificCoTAbstract

loggingConstants = LoggingConstants(log_name="FTS_FederationServerService")
logger = CreateLoggerController(
    "FTS_FederationServerService", logging_constants=loggingConstants).getLogger()

# Make a connection to the MainConfig object for all routines below
config = MainConfig.instance()

loggingConstants = LoggingConstants()


class FederationServerService(FederationServiceBase):

    def __init__(self):
        self._define_command_responsibility_chain()
        self._define_connection_responsibility_chain()
        self._define_service_responsibility_chain()
        self._define_external_data_responsibility_chain()
        self._define_data_responsibility_chain()
        self.pipe = None
        self.federates: Dict[str, Federate] = {}
        self.sel = selectors.DefaultSelector()
        self.logger = logger
        self.user_dict: Dict[str, FederatedEvent] = {}

    def get_service_users(self) -> List[FederatedEvent]:
        return self.user_dict.values()

    def add_service_user(self, user: FederatedEvent) -> None:
        """ add a service user to this services user persistence mechanism

        Returns: None

        """
        self.user_dict[user.contact.uid] = user

    def remove_service_user(self, user: FederatedEvent):
        """ remove a service user from this services user persistence mechanism

        Returns: None

        """
        del self.user_dict[user.contact.uid]

    def define_responsibility_chain(self):
        pass

    def _create_context(self) -> None:
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(config.federationCert, config.federationKey,
                                     password=config.federationKeyPassword)

    def _create_listener(self, ip: str, port: int) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.bind((ip, port))
        sock.listen()
        ssock = self.context.wrap_socket(sock, server_side=True)
        ssock.setblocking(False)
        self.sel.register(ssock, selectors.EVENT_READ, data=None)

    def _define_external_data_responsibility_chain(self):
        """ this method is responsible for defining the responsibility chain which handles external data
        eg. data sent to FTS by a federate

        Returns:

        """
        fed_proto_standard_handler = FederationProtobufStandardHandler()

        fed_proto_disconnect_handler = FederationProtobufDisconnectionHandler()
        fed_proto_disconnect_handler.setNextHandler(fed_proto_standard_handler)

        fed_proto_connection_handler = FederationProtobufConnectionHandler()
        fed_proto_connection_handler.setNextHandler(
            fed_proto_disconnect_handler)

        fed_proto_validation_handler = FederationProtobufValidationHandler()
        fed_proto_validation_handler.setNextHandler(
            fed_proto_connection_handler)

        self.external_data_chain = fed_proto_validation_handler

    def _call_responsibility_chain(self, command):
        """ this method is responsible for calling the responsibility chains for all command types:
            service level commands; start, stop etc
            Connection level commands; close connection, open connection etc
            data level commands; send data x, each handler is responsible for some facet of data validation before
                the connection receives it

        Returns: output from successful handler

        """
        # if command.level == "SERVICE":
        if command == "STOP":
            self.service_chain.Handle(obj=self, command=command)

        # elif command.level == "CONNECTION":
        elif isinstance(command, tuple) and (command[1] == "DELETE" or command[1] == "CREATE" or command[1] == "UPDATE"):
            self.connection_chain.Handle(obj=self, command=command)

        # elif command.level == "DATA":
        if isinstance(command, SpecificCoTAbstract) or isinstance(command, ClientInformation):
            self.data_chain.Handle(obj=self, command=command)

    def _define_service_responsibility_chain(self):
        """ this method is responsible for defining the responsibility chain which will handle service level commands;
            or commands which effect the entire service

        Returns: the entry handler for this responsibility chain

        """
        stop_handler = StopHandler()
        self.service_chain = stop_handler

    def _define_connection_responsibility_chain(self):
        """ this method is responsible for defining the responsibility chain which will handle connection level commands;
            or commands which effect the status of a connection at the socket level

        Returns: the entry handler for this responsibility chain

        """
        disconnect_handler = DisconnectHandler()
        self.connection_chain = disconnect_handler

    def _define_data_responsibility_chain(self):
        """ this method is responsible for defining the responsibility chain which will handle data level commands;
            or commands which transfer data to a client

        Returns: the entry handler for this responsibility chain

        """

        send_data_handler = SendDataHandler()

        destination_validation_handler = DestinationValidationHandler()
        destination_validation_handler.setNextHandler(send_data_handler)

        send_disconnection_data_handler = SendDisconnectionDataHandler()
        send_disconnection_data_handler.setNextHandler(
            destination_validation_handler)

        send_connection_data_handler = SendConnectionDataHandler()
        send_connection_data_handler.setNextHandler(
            send_disconnection_data_handler)

        data_validation_handler = DataValidationHandler()
        data_validation_handler.setNextHandler(send_connection_data_handler)

        self.data_chain = data_validation_handler

    def _define_command_responsibility_chain(self) -> HandlerBase:
        self.m_StopHandler = StopHandler()

        self.m_DisconnectHandler = DisconnectHandler()
        self.m_DisconnectHandler.setNextHandler(self.m_StopHandler)

        self.m_SendDataHandler = SendDataHandler()
        self.m_SendDataHandler.setNextHandler(self.m_DisconnectHandler)

        self.m_SendDisconnectionHandler = SendDisconnectionDataHandler()
        self.m_SendDisconnectionHandler.setNextHandler(self.m_SendDataHandler)

        # first handler in chain of responsibility and should be called first
        self.m_SendConnectionHandler = SendConnectionDataHandler()
        self.m_SendConnectionHandler.setNextHandler(
            self.m_SendDisconnectionHandler)

    def main(self):
        inbound_data_thread = threading.Thread(
            target=self.inbound_data_handler)
        inbound_data_thread.start()
        outbound_data_thread = threading.Thread(
            target=self.outbound_data_handler)
        outbound_data_thread.start()
        inbound_data_thread.join()

    def serialize_data(self, data_object: FederatedEvent):
        specific_obj = self._process_protobuff_to_object(data_object)
        return specific_obj

    def outbound_data_handler(self):
        """ this is the main process responsible for receiving data from federates and sharing
        with FTS core

        Returns:

        """
        while True:
            try:
                data = self.receive_data_from_federate(1)
            except ssl.SSLWantReadError:
                data = None
            if data:
                for protobuf_object in data:
                    # TODO: clean all of this up as it's just a PoC

                    # event = etree.Element('event')
                    # SpecificCoTObj = XMLCoTController().categorize_type(protobuf_object.type)
                    try:
                        serialized_data = self.serialize_data(protobuf_object)
                        self.send_command_to_core(serialized_data)
                    except Exception as e:
                        self.logger.warning(
                            "there has been an exception thrown in the outbound_data_handler "+str(e))
                    """if isinstance(SpecificCoTObj, SendOtherController):
                        detail = protobuf_object.event.other
                        protobuf_object.event.other = ''
                        fts_obj = ProtobufSerializer().from_format_to_fts_object(protobuf_object, Event.Other())
                        protobuf_object.event.other = detail
                        SpecificCoTObj.object = fts_obj
                        SpecificCoTObj.Object =
                    else:
                        fts_obj = ProtobufSerializer().from_format_to_fts_object(protobuf_object, SpecificCoTObj().object)
                        self.pipe.send(data)"""

    def send_command_to_core(self, serialized_data):
        if self.pipe.sender_queue.full():
            print('queue full !!!')
        self.pipe.put(serialized_data)

    def inbound_data_handler(self):
        """this is the main process responsible for receiving data from FTS core

        Returns:

        """
        while True:
            try:
                command = self.pipe.get()
                if command:
                    try:
                        self._call_responsibility_chain(command)
                    except Exception as e:
                        pass
            except Exception as e:
                self.logger.error(str(e))

    def receive_data_from_federate(self, timeout):
        """called whenever data is available from any federate and immediately proceeds to
        send data through process pipe
        """
        dataarray = []
        events = self.sel.select(timeout=timeout)
        for key, mask in events:
            if key.data is None:
                self._accept_connection(key.fileobj)
            else:
                federate_data = self._receive_new_data(key)
                if federate_data:
                    dataarray.append(federate_data)
        return dataarray

    def _receive_new_data(self, key):
        try:
            conn = key.fileobj
            header = conn.recv(4)
            if header:
                try:
                    buffer = self._get_header_length(header)
                    raw_protobuf_message = conn.recv(buffer)
                    print(raw_protobuf_message)
                    protobuf_object = FederatedEvent()
                    protobuf_object.ParseFromString(raw_protobuf_message)
                    self.external_data_chain.Handle(self, protobuf_object)
                    return protobuf_object
                except Exception as e:
                    conn.recv(10000)
                    return None
            else:
                self.disconnect_client(key.data.uid)
        except OSError:
            return None
        except Exception as e:
            self.logger.warning(
                f"exception in receiving data from federate {str(e)}")
            self.disconnect_client(key.data.uid)

    def _accept_connection(self, sock) -> None:
        try:
            conn, addr = sock.accept()  # Should be ready to read
            print('accepted connection from', addr)
            conn.setblocking(False)
            data = Federate()
            data.conn = conn
            # get federate certificate CN
            # data.name = dict(x[0] for x in conn.getpeercert()["subject"])["commonName"]
            data.name = addr[0]
            data.addr = addr
            data.uid = str(uuid.uuid4())
            events = selectors.EVENT_READ
            self._send_connected_clients(conn)
            self.sel.register(conn, events, data=data)
            self.federates[data.uid] = data

            self.db.create_ActiveFederation(id = data.uid, federate = "unknown", address = addr[0], port = addr[1], initiator = "Remote")
            return None
        except Exception as e:
            print(e)
            self.logger.warning("exception thrown accepting federation " + str(e))

    def start(self, pipe, ip, port):
        self.db = DatabaseController()
        self.pipe = pipe
        self._create_context()
        self._create_listener(ip, port)
        print('started federation server service')
        self.main()

    def stop(self):
        pass
