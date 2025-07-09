"""
프로세서 팩토리 클래스

양식 타입에 따라 적절한 프로세서를 생성하고 반환합니다.
"""

import logging
from typing import Dict, Any, Optional

from .base_processor import BaseFormProcessor, DefaultFormProcessor
from .annual_leave_processor import AnnualLeaveProcessor
from .personal_expense_processor import PersonalExpenseProcessor
from .dinner_expense_processor import DinnerExpenseProcessor
from .transportation_expense_processor import TransportationExpenseProcessor
from .inventory_purchase_processor import InventoryPurchaseProcessor
from .purchase_approval_processor import PurchaseApprovalProcessor
from .corporate_card_processor import CorporateCardProcessor
from .dispatch_report_processor import DispatchReportProcessor


class ProcessorFactory:
    """양식별 프로세서를 생성하는 팩토리 클래스"""

    # 양식 타입별 프로세서 매핑
    PROCESSOR_MAP = {
        "연차 신청서": AnnualLeaveProcessor,
        "annual_leave": AnnualLeaveProcessor,
        "개인 경비 사용내역서": PersonalExpenseProcessor,
        "개인 경비 사용 내역서": PersonalExpenseProcessor,
        "personal_expense_report": PersonalExpenseProcessor,
        "야근식대비용 신청서": DinnerExpenseProcessor,
        "dinner_expense": DinnerExpenseProcessor,
        "교통비 신청서": TransportationExpenseProcessor,
        "transportation_expense": TransportationExpenseProcessor,
        "비품/소모품 구입내역서": InventoryPurchaseProcessor,
        "inventory_purchase_report": InventoryPurchaseProcessor,
        "구매 품의서": PurchaseApprovalProcessor,
        "purchase_approval_form": PurchaseApprovalProcessor,
        "법인카드 지출내역서": CorporateCardProcessor,
        "corporate_card_statement": CorporateCardProcessor,
        "파견 및 출장 보고서": DispatchReportProcessor,
        "dispatch_businesstrip_report": DispatchReportProcessor,
    }

    @classmethod
    def create_processor(
        cls, form_type: str, form_config: Optional[Dict[str, Any]] = None
    ) -> BaseFormProcessor:
        """양식 타입에 맞는 프로세서 생성

        Args:
            form_type: 양식 타입 (한국어 또는 영어)
            form_config: 양식 설정 정보

        Returns:
            BaseFormProcessor: 해당 양식의 전용 프로세서 또는 기본 프로세서
        """
        processor_class = cls.PROCESSOR_MAP.get(form_type, DefaultFormProcessor)

        if processor_class != DefaultFormProcessor:
            logging.info(
                f"Creating specialized processor for form_type: {form_type} -> {processor_class.__name__}"
            )
        else:
            logging.info(
                f"Creating default processor for unsupported form_type: {form_type}"
            )

        return processor_class(form_config)

    @classmethod
    def get_supported_forms(cls) -> list:
        """지원되는 양식 타입 목록 반환"""
        return list(cls.PROCESSOR_MAP.keys())

    @classmethod
    def add_processor(cls, form_type: str, processor_class: type):
        """새로운 프로세서 등록

        Args:
            form_type: 양식 타입
            processor_class: 프로세서 클래스
        """
        cls.PROCESSOR_MAP[form_type] = processor_class
        logging.info(
            f"Registered new processor: {form_type} -> {processor_class.__name__}"
        )


def get_form_processor(
    form_type: str, form_config: Optional[Dict[str, Any]] = None
) -> BaseFormProcessor:
    """편의 함수: 양식 프로세서 생성

    Args:
        form_type: 양식 타입
        form_config: 양식 설정 정보

    Returns:
        BaseFormProcessor: 양식 프로세서
    """
    return ProcessorFactory.create_processor(form_type, form_config)
