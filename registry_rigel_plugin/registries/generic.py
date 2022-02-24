import os
from pydantic import BaseModel, PrivateAttr
from rigelcore.clients import DockerClient
from rigelcore.exceptions import UndeclaredEnvironmentVariableError
from rigelcore.loggers import MessageLogger
from typing import Any


class GenericCredentials(BaseModel):
    """
    Pair of login credentials to be used with a Dicker image registry.

    :type username: string
    :ivar username: The user to be authenticated.
    :type password: string
    :ivar password: The secret user password.
    """
    # Required fields.
    username: str
    password: str


class GenericDockerRegistryPlugin(BaseModel):
    """
    A plugin for Rigel to deploy Docker images to a Docker image registry.

    :type credentials: GenericCredentials
    :ivar credentials: The credentials to authenticate with the Docker image registry.
    :type image: string
    :ivar image: The name ofor the deployed imaged.
    :type local_image: string
    :ivar local_image: The name of the image to deploy
    :type registry: string
    :ivar registry: The Docker image registry.
    """
    # List of required fields.
    credentials: GenericCredentials
    image: str
    registry: str

    # List of optional fields.
    local_image: str = 'rigel:temp'

    # List of private fields.
    _complete_image_name: str = PrivateAttr()
    _docker_client: DockerClient = PrivateAttr()
    _logger: MessageLogger = PrivateAttr()

    def __init__(self, *args: Any, **kwargs: Any) -> None:

        self._docker_client = kwargs.pop('docker_client')
        self._logger = kwargs.pop('logger')

        super().__init__(*args, **kwargs)

        self._complete_image_name = f"{self.registry}/{self.image}"

    def tag(self) -> None:
        """
        Tag existent Docker image to the desired tag.
        """
        self._docker_client.tag(
            self.local_image,
            self._complete_image_name
        )

    def authenticate(self) -> None:
        """
        Authenticate with the specified Docker image registr.
        """
        def __get_env_var_value(env: str) -> str:
            """
            Retrieve a value stored in an environment variable.

            :type env: string
            :param env: Name of environment variable.
            :rtype: string
            :return: The value of the environment variable.
            """
            value = os.environ.get(env)
            if value is None:
                raise UndeclaredEnvironmentVariableError(env=env)
            return value

        self._docker_client.login(
            self.registry,
            __get_env_var_value(self.credentials.username),
            __get_env_var_value(self.credentials.password)
        )

    def deploy(self) -> None:
        """
        Deploy Docker image to the specified Docker image registry.
        """
        self._docker_client.push(
            self._complete_image_name
        )

    def run(self) -> None:
        """
        Plugin entrypoint.
        """
        self.tag()
        self._logger.info(f"Created Docker image {self.image} from {self.local_image}.")

        self.authenticate()
        self._logger.info(f"Authenticated with Docker image registry {self.registry}.")

        self.deploy()
        self._logger.info(f"Docker image {self._complete_image_name} was pushed with sucess to {self.registry}.")