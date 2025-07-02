"""
기본 검증기 클래스

양식 데이터의 유효성 검증을 담당합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class ValidationResult:
    """검증 결과를 담는 클래스"""

    def __init__(
        self,
        is_valid: bool = True,
        errors: List[str] = None,
        warnings: List[str] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, message: str):
        """에러 추가"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """경고 추가"""
        self.warnings.append(message)

    def has_errors(self) -> bool:
        """에러가 있는지 확인"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """경고가 있는지 확인"""
        return len(self.warnings) > 0


class BaseValidator(ABC):
    """양식 검증을 위한 기본 클래스"""

    def __init__(self, form_config: Optional[Dict[str, Any]] = None):
        """
        Args:
            form_config: 양식별 설정 정보
        """
        self.form_config = form_config or {}

    def validate(self, form_data: Dict[str, Any]) -> ValidationResult:
        """전체 검증 실행

        Args:
            form_data: 검증할 폼 데이터

        Returns:
            ValidationResult: 검증 결과
        """
        logging.info(f"Starting validation with {self.__class__.__name__}")

        result = ValidationResult()

        # 1. 필수 필드 검증
        self.validate_required_fields(form_data, result)

        # 2. 날짜 형식 검증
        self.validate_date_formats(form_data, result)

        # 3. 숫자 형식 검증
        self.validate_numeric_fields(form_data, result)

        # 4. 양식별 커스텀 검증
        self.validate_custom(form_data, result)

        # 5. 비즈니스 로직 검증
        self.validate_business_rules(form_data, result)

        logging.info(
            f"Validation completed: valid={result.is_valid}, errors={len(result.errors)}, warnings={len(result.warnings)}"
        )
        return result

    def validate_required_fields(
        self, form_data: Dict[str, Any], result: ValidationResult
    ):
        """필수 필드 검증"""
        required_fields = self.form_config.get("required_fields", [])

        for field in required_fields:
            if field not in form_data or not form_data[field]:
                result.add_error(f"필수 필드가 누락되었습니다: {field}")

    def validate_date_formats(
        self, form_data: Dict[str, Any], result: ValidationResult
    ):
        """날짜 형식 검증"""
        import re

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

        date_fields = [
            "start_date",
            "end_date",
            "application_date",
            "work_date",
            "departure_date",
            "request_date",
            "draft_date",
            "statement_date",
        ]

        for field in date_fields:
            if field in form_data and form_data[field]:
                value = form_data[field]
                if isinstance(value, str) and not date_pattern.match(value):
                    result.add_error(
                        f"잘못된 날짜 형식입니다: {field} = {value} (YYYY-MM-DD 형식이어야 합니다)"
                    )

    def validate_numeric_fields(
        self, form_data: Dict[str, Any], result: ValidationResult
    ):
        """숫자 형식 검증"""
        numeric_fields = [
            "amount",
            "total_amount",
            "quantity",
            "unit_price",
            "total_price",
        ]

        for field in numeric_fields:
            if field in form_data and form_data[field]:
                value = form_data[field]
                try:
                    if isinstance(value, str):
                        int(value)
                    elif not isinstance(value, (int, float)):
                        result.add_error(f"숫자가 아닌 값입니다: {field} = {value}")
                except ValueError:
                    result.add_error(f"잘못된 숫자 형식입니다: {field} = {value}")

    # 추상 메서드들 - 각 양식별 검증기에서 구현
    @abstractmethod
    def validate_custom(self, form_data: Dict[str, Any], result: ValidationResult):
        """양식별 커스텀 검증"""
        pass

    @abstractmethod
    def validate_business_rules(
        self, form_data: Dict[str, Any], result: ValidationResult
    ):
        """비즈니스 로직 검증"""
        pass


class DefaultValidator(BaseValidator):
    """기본 검증기 (특별한 검증이 필요 없는 양식용)"""

    def validate_custom(self, form_data: Dict[str, Any], result: ValidationResult):
        pass

    def validate_business_rules(
        self, form_data: Dict[str, Any], result: ValidationResult
    ):
        pass
