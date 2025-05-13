import os
import subprocess
import tempfile
import atexit
import time
from typing import List, Dict, Optional, Union


class PrometheusServer:
    """
    Prometheus 서버를 관리하는 클래스
    외부 Prometheus 바이너리를 사용하며, 설정 파일 생성 및 프로세스 관리 기능 제공
    """

    def __init__(
        self,
        port: int = 9090,
        storage_path: str = "./prometheus_data",
        binary_path: Optional[str] = None,
    ):
        """
        PrometheusServer 인스턴스 초기화

        Args:
            port: Prometheus 웹 인터페이스 및 API 포트 (기본값: 9090)
            storage_path: Prometheus TSDB 저장 경로 (기본값: ./prometheus_data)
            binary_path: Prometheus 바이너리 경로 (없으면 PATH에서 검색)
        """
        self.port = port
        self.storage_path = storage_path
        self.binary_path = binary_path
        self.process = None
        self.config_path = None
        self._is_running = False

    def add_scrape_config(self, config_data: Dict[str, Union[str, List[Dict]]]) -> None:
        """
        스크레이프 설정을 추가합니다.

        Args:
            config_data: Prometheus 설정을 담은 Dictionary
        """
        self.scrape_configs = config_data.get("scrape_configs", [])

    def set_default_configs(
        self, metrics_exporter_port: int = 8080, vllm_host: Optional[str] = None
    ):
        """
        기본 스크레이프 설정을 생성합니다.

        Args:
            metrics_exporter_port: 애플리케이션 메트릭 익스포터 포트
            vllm_host: vLLM 서버 호스트 주소 (없으면 vLLM 메트릭 스크레이핑 비활성화)
        """
        # 기본 스크레이프 설정 생성
        scrape_configs = [
            {
                "job_name": "app_metrics",
                "static_configs": [{"targets": [f"localhost:{metrics_exporter_port}"]}],
            }
        ]

        # vLLM 호스트가 제공된 경우 추가
        if vllm_host:
            scrape_configs.append(
                {
                    "job_name": "vllm_metrics",
                    "metrics_path": "/metrics",
                    "static_configs": [{"targets": [vllm_host]}],
                }
            )

        self.scrape_configs = scrape_configs

    def _create_config_file(self) -> str:
        """
        Prometheus 설정 파일을 생성합니다.

        Returns:
            str: 생성된 설정 파일 경로
        """
        # 임시 설정 파일 생성
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as config_file:
            config_path = config_file.name

            # 설정 파일 헤더 작성
            config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
"""
            # 스크레이프 설정 추가
            import yaml

            for scrape_config in self.scrape_configs:
                config += yaml.dump(
                    [scrape_config], sort_keys=False, default_flow_style=False
                )

            config_file.write(config)
            return config_path

    def start(self) -> bool:
        """
        Prometheus 서버를 시작합니다.

        Returns:
            bool: 성공적으로 시작되었는지 여부
        """
        if self._is_running:
            print("Prometheus 서버가 이미 실행 중입니다.")
            return True

        # 기본 스크레이프 설정이 없으면 생성
        if not hasattr(self, "scrape_configs"):
            self.set_default_configs()

        # 설정 파일 생성
        self.config_path = self._create_config_file()

        # Prometheus 시작
        try:
            # 저장 디렉토리 확인
            os.makedirs(self.storage_path, exist_ok=True)

            # Prometheus 바이너리 경로 확인
            prometheus_bin = self.binary_path
            if not prometheus_bin:
                try:
                    # PATH에서 prometheus 찾기 (Windows)
                    which_result = subprocess.run(
                        ["where", "prometheus"], capture_output=True, text=True
                    )
                    if which_result.returncode == 0 and which_result.stdout.strip():
                        prometheus_bin = "prometheus"
                    else:
                        # PATH에서 prometheus 찾기 (Unix)
                        which_result = subprocess.run(
                            ["which", "prometheus"], capture_output=True, text=True
                        )
                        if which_result.returncode == 0 and which_result.stdout.strip():
                            prometheus_bin = "prometheus"
                        else:
                            print("❌ Prometheus 바이너리를 찾을 수 없습니다.")
                            # 내장 서버 모드로 전환 - 메트릭만 출력
                            print(
                                "✓ Prometheus 서버 시작을 건너뛰고 메트릭 내보내기만 활성화합니다."
                            )
                            return False
                except FileNotFoundError:
                    print("❌ 'where' 또는 'which' 명령어를 찾을 수 없습니다.")
                    print(
                        "✓ Prometheus 서버 시작을 건너뛰고 메트릭 내보내기만 활성화합니다."
                    )
                    return False

            prom_cmd = [
                prometheus_bin,
                f"--config.file={self.config_path}",
                f"--web.listen-address=0.0.0.0:{self.port}",
                f"--storage.tsdb.path={self.storage_path}",
            ]

            # 서브프로세스로 실행 (백그라운드)
            print(f"Prometheus 실행 명령어: {' '.join(prom_cmd)}")
            self.process = subprocess.Popen(
                prom_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # 시작 확인 (짧은 시간 대기)
            time.sleep(1)
            if self.process.poll() is None:  # None이면 프로세스가 실행 중
                self._is_running = True
                print(f"✅ Prometheus 서버가 포트 {self.port}에서 실행 중입니다.")

                # 프로그램 종료 시 Prometheus도 종료
                atexit.register(self.stop)
                return True
            else:
                stderr = self.process.stderr.read().decode("utf-8")
                print(f"❌ Prometheus 서버 시작 실패: {stderr}")
                return False

        except FileNotFoundError:
            print(
                "❌ Prometheus 바이너리를 찾을 수 없습니다. 시스템에 Prometheus가 설치되어 있는지 확인하세요."
            )
            print("✓ Prometheus 서버 시작을 건너뛰고 메트릭 내보내기만 활성화합니다.")
            return False
        except Exception as e:
            print(f"❌ Prometheus 서버 시작 중 오류 발생: {e}")
            if self.config_path and os.path.exists(self.config_path):
                os.unlink(self.config_path)
            return False

    def stop(self) -> None:
        """Prometheus 서버를 종료합니다."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)  # 최대 5초간 종료 대기
            print("✅ Prometheus 서버가 종료되었습니다.")
            self._is_running = False

            # 임시 설정 파일 삭제
            if self.config_path and os.path.exists(self.config_path):
                os.unlink(self.config_path)
                self.config_path = None

    def is_running(self) -> bool:
        """
        Prometheus 서버가 실행 중인지 확인합니다.

        Returns:
            bool: 실행 중이면 True, 아니면 False
        """
        if self.process and self.process.poll() is None:
            return True
        return False

    def get_api_url(self) -> str:
        """
        Prometheus API URL을 반환합니다.

        Returns:
            str: Prometheus API URL
        """
        return f"http://localhost:{self.port}/api/v1"
