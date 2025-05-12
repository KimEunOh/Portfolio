# CLIP 유사도 기반 Multimodal RAG 검증 기법

## 프로젝트 소개
이 프로젝트는 CLIP 유사도를 활용한 Multimodal RAG 검증 기법을 구현한 것입니다. LLaMA, LLaVA, CLIP 등의 멀티모달 모델을 활용하여 이미지와 텍스트의 의미적 유사도를 분석하고, 이를 통해 RAG 시스템의 응답 신뢰도를 검증합니다. 특히 GradCAM++, LayerCAM 등의 시각화 기법을 통해 모델의 판단 근거를 해석 가능하게 제시합니다.

## 주요 기능
- **CLIP 기반 분석**
  - 이미지-텍스트 간 의미적 유사도 계산
  - 멀티모달 임베딩 추출 및 비교
  - GradCAM++, LayerCAM을 통한 판단 근거 시각화
- **LLaVA 모델 활용**
  - 이미지 내용 자연어 설명 생성
  - 커스텀 데이터셋 기반 파인튜닝
  - 설명 생성 결과의 신뢰도 평가
- **RAG 파이프라인**
  - 멀티모달 검색 및 검증
  - 응답 신뢰도 평가
  - 결과 시각화 및 해석

## 기술 스택
- **기본 환경**: Python 3.11
- **딥러닝 프레임워크**
  - PyTorch
  - transformers
  - together-cli (API 통합)
- **멀티모달 모델**
  - CLIP (openai/clip-vit-large-patch14)
  - LLaVA
  - YOLOv8
- **시각화 도구**
  - GradCAM++
  - LayerCAM
  - EigenGradCAM
  - matplotlib
- **유틸리티**
  - pandas, numpy (데이터 처리)
  - captum (모델 해석)

## 설치 방법
1. 저장소 클론
```bash
git clone <repository_url>
cd deepfake
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 모델 다운로드
- LLaVA 모델은 HuggingFace에서 다운로드됩니다
- CLIP 모델은 transformers를 통해 자동으로 다운로드됩니다
- YOLOv8 모델은 프로젝트에 포함되어 있습니다

## 프로젝트 구조
```
deepfake/
├── data/                      # 데이터셋 디렉토리
│   ├── raw/                  # 원본 데이터
│   ├── processed/           # 처리된 데이터
│   └── test/               # 테스트 데이터
├── notebooks/               # 주피터 노트북 파일
│   ├── data_prep/         # 데이터 준비 코드
│   ├── model_dev/        # 파인튜닝, RAG, 탐지 코드
│   ├── experiments/     # 실험 노트북
│   └── evaluation/     # 평가 노트북
├── src/                 # 소스 코드
│   ├── data/          # 데이터 처리 모듈
│   ├── models/       # 모델 구현
│   └── utils/       # 유틸리티 함수
├── results/          # 실험/탐지 결과
├── docs/           # 문서
└── README.md      # 프로젝트 설명
```

## 사용 방법
1. RAG 성능 검증:
```python
# notebooks/model_dev/rag_performance_visual.ipynb 실행
from pytorch_grad_cam import GradCAM, GradCAMPlusPlus, LayerCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

# CLIP 모델 로드
model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

# CAM 시각화
cam = GradCAMPlusPlus(model=model, target_layer=model.visual.transformer.resblocks[-1])
grayscale_cam = cam(input_tensor=image_tensor)
```

2. 객체 탐지:
```python
# notebooks/model_dev/QwQ_detection.ipynb 실행
from ultralytics import YOLO

# YOLOv8 모델 로드
model = YOLO('yolov8n.pt')

# 객체 탐지 실행
results = model(image)
```

## 주요 결과물
- GradCAM++ 시각화: 모델이 주목하는 이미지 영역 표시
- LayerCAM 분석: 레이어별 특징 활성화 패턴
- EigenGradCAM: 주요 특징 벡터 시각화
- 객체 탐지 결과: YOLOv8 기반 객체 인식


## 한계점 및 개선 방향
- **모델 한계**
  - 복잡한 배경에서 객체 탐지 정확도 저하
  - 실시간 처리 시 지연 발생
  - 다중 객체 상황에서 성능 저하
- **개선 방향**
  - 모델 경량화 및 최적화
  - 배치 처리 파이프라인 개선
  - 앙상블 기법 도입 검토

## 참고 자료
- [CLIP 논문](https://arxiv.org/abs/2103.00020)
- [GradCAM++ 논문](https://arxiv.org/abs/1710.11063)
- [LayerCAM 논문](https://arxiv.org/abs/2104.06643)
- [YOLOv8 문서](https://docs.ultralytics.com/) 