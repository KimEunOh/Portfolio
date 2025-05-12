# Notebooks 디렉토리 구조

이 디렉토리는 딥페이크 탐지 프로젝트의 주요 노트북 파일들을 포함하고 있습니다.

## 디렉토리 구조

### 1. model_dev/
모델 개발 및 구현 관련 노트북들이 포함되어 있습니다.

#### rag/
RAG(Retrieval-Augmented Generation) 시스템 구현 관련 노트북들:
- `CLIP_RAG.ipynb`: CLIP 모델 기반 RAG 시스템 구현
- `QwQ_rag.ipynb`: RAG 기반 딥페이크 이미지 분석 (QwQ 모델)
- `Llama_rag.ipynb`: Llama 모델 기반 RAG 시스템 
- `rag_performance_visual.ipynb`: RAG 시스템 성능 시각화

#### detection/
딥페이크 탐지 모델 구현 관련 노트북들:
- `QwQ_detection.ipynb`: 딥페이크 이미지 탐지 시스템 (QwQ 모델)
- `Llama_detection.ipynb`: Llama 모델 기반 탐지 시스템

#### finetuning/
모델 학습 및 파인튜닝 관련 노트북들:
- `LLaVA_tuning.ipynb`: LLaVA 모델 파인튜닝
- `finetuning_model.ipynb`: 모델 학습 파이프라인
- `fine.ipynb`: 기본 파인튜닝 실험

### 2. experiments/
실험 및 테스트 관련 노트북들이 포함되어 있습니다.

#### prompt_engineering/
프롬프트 엔지니어링 실험:
- `prompt.ipynb`: 기본 프롬프트 실험
- `instruction_prompt.ipynb`: 지시문 프롬프트 실험

#### testing/
테스트 및 검증:
- `test_no_langchain.ipynb`: LangChain 없는 구현 테스트
- `test2.ipynb`: 추가 테스트 실험

### 3. evaluation/
모델 평가 및 레이블링 관련 노트북들이 포함되어 있습니다.

#### labeling/
데이터 레이블링:
- `label_LLaMA.ipynb`: LLaMA 모델 레이블링
- `GPT_label.ipynb`: GPT 레이블링
- `GPT_label_real.ipynb`: 실제 이미지 GPT 레이블링

### 4. data_prep/
데이터 전처리 및 준비:
- `json_to_DB.ipynb`: JSON 데이터 DB 변환
- `bulid_dataset.ipynb`: 데이터셋 구축

## 사용 방법

1. 각 노트북은 독립적으로 실행할 수 있지만, 일부 노트북은 다른 노트북의 결과물에 의존할 수 있습니다.
2. 노트북을 실행하기 전에 필요한 의존성이 설치되어 있는지 확인하세요.
