from abc import ABC, abstractmethod


class EnviadorEmail(ABC):
    @abstractmethod
    def enviar(
        self, para: str, asunto: str, cuerpo_html: str
    ) -> None: ...
