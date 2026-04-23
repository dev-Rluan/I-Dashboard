from abc import ABC, abstractmethod


class AbstractPlatform(ABC):

    @abstractmethod
    def get_open_ports(self) -> list[dict]:
        """열린 포트 목록 반환. 실패 시 빈 리스트."""
        ...

    @abstractmethod
    def get_firewall_status(self) -> dict:
        """방화벽 상태 및 규칙 반환. 미지원 시 supported=False."""
        ...

    @abstractmethod
    def get_services(self) -> list[dict]:
        """시스템 서비스 목록 반환. 실패 시 빈 리스트."""
        ...

    @abstractmethod
    def get_service_logs(self, service_name: str, lines: int = 20) -> list[str]:
        """서비스 최근 로그 반환. 실패 시 빈 리스트."""
        ...

    @abstractmethod
    def get_logs(self, log_type: str = "system", lines: int = 100) -> list[dict]:
        """시스템 로그 반환. 실패 시 빈 리스트."""
        ...
