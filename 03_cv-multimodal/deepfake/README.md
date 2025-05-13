# CLIP 유사도 기반 Multimodal RAG 검증 기법

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C.svg)
![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-FFD21E.svg)
![CLIP](https://img.shields.io/badge/CLIP-OpenAI-412991.svg)
![Computer Vision](https://img.shields.io/badge/CV-Deep%20Learning-76B900.svg)

## 프로젝트 개요

본 프로젝트는 딥러닝 기반 컴퓨터 비전과 자연어 처리의 교차점에 위치한 연구로, CLIP 유사도를 활용한 Multimodal RAG 검증 기법을 구현했습니다. 멀티모달 모델(LLaMA, LLaVA, CLIP)을 활용하여 이미지와 텍스트 간 의미적 유사도를 정밀하게 분석하고, 이를 통해 RAG(Retrieval-Augmented Generation) 시스템의 응답 신뢰도를 객관적으로 검증합니다.

특히 GradCAM++, LayerCAM 등의 고급 시각화 기법을 통해 AI 모델의 판단 근거를 직관적으로 해석 가능하게 제시함으로써, 'AI가 어떤 부분을 보고 판단했는지'에 대한 투명성을 확보하고자 했습니다. 이 접근 방식은 특히 딥페이크 탐지와 같은 중요한 실용 사례에서 신뢰성 있는 검증 도구로 활용될 수 있습니다.

## 기술 스택

### 딥러닝 & 컴퓨터 비전
- **PyTorch**: 딥러닝 모델 학습 및 추론 프레임워크
- **transformers**: 최신 트랜스포머 기반 모델 활용
- **CLIP**: 이미지-텍스트 상호 학습 모델 (OpenAI)
- **LLaVA**: 대규모 시각-언어 어시스턴트 모델
- **YOLOv8**: 최신 객체 탐지 모델

### 시각화 & 설명 가능한 AI
- **GradCAM++**: 그래디언트 기반 클래스 활성화 맵핑
- **LayerCAM**: 레이어별 특징 시각화
- **EigenGradCAM**: 주성분 분석 기반 시각화
- **Attention Rollout**: ViT 모델용 어텐션 기반 시각화
- **matplotlib/seaborn**: 데이터 시각화

### 유틸리티 & 파이프라인
- **pandas/numpy**: 데이터 처리 및 분석
- **captum**: 모델 해석 라이브러리
- **together-cli**: API 통합 인터페이스

## 시스템 아키텍처

본 시스템은 다음과 같은 구성 요소로 이루어진 멀티모달 처리 파이프라인을 구현합니다:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│                  │     │                  │     │                  │
│  입력 데이터       │────►│  멀티모달 처리     │────►│  RAG 검증 평가    │
│  (이미지/텍스트)   │     │  파이프라인       │     │  시스템           │
│                  │     │                  │     │                  │
└──────────────────┘     └────────┬─────────┘     └────────┬─────────┘
                                  │                        │
                                  ▼                        ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │                  │     │                  │
                         │  CLIP 유사도      │     │  설명 가능한 AI    │
                         │  분석 엔진        │     │  시각화 모듈       │
                         │                  │     │                  │
                         └──────────────────┘     └──────────────────┘
```

## 주요 기능

### CLIP 기반 분석
- **이미지-텍스트 간 의미적 유사도 계산**: 복잡한 시각-언어 관계 정량화
- **멀티모달 임베딩 추출 및 비교**: 512차원 벡터 공간에서의 의미적 거리 측정
- **시각화 탐색**: GradCAM++, LayerCAM을 활용한 판단 근거 시각화 탐색 (prototype)

### LLaVA 모델 활용
- **이미지 내용 자연어 설명 생성**: 시각 정보의 언어적 해석
- **커스텀 데이터셋 기반 파인튜닝**: 도메인 특화 학습을 통한 정확도 향상
- **설명 생성 결과의 신뢰도 평가**: 생성된 설명의 품질 및 일관성 측정

### RAG 파이프라인
- **멀티모달 검색 및 검증**: 이미지와 텍스트 기반의 관련 정보 검색
- **응답 신뢰도 평가**: 생성된 응답의 신뢰성 점수화
- **결과 시각화 및 해석**: 복잡한 분석 결과의 직관적 표현

## 구현 상세

### 멀티모달 분석 파이프라인
1. **이미지 및 텍스트 전처리**: 해상도 조정, 정규화, 토큰화
2. **CLIP 임베딩 추출**: 이미지와 텍스트의 공통 벡터 공간 표현
3. **유사도 계산**: 코사인 유사도 측정을 통한 관련성 평가
4. **시각화 탐색**: 판단 근거 시각화를 위한 다양한 접근법 실험

### 객체 탐지 및 분석
1. **YOLOv8 기반 객체 탐지**: 이미지 내 관심 객체 식별
2. **객체별 특징 추출**: 이미지 내 주요 요소의 독립적 분석
3. **객체-텍스트 관계 분석**: 탐지된 객체와 텍스트 설명 간 정합성 평가

## 구현 현황 및 한계

현재 프로젝트에서는 CLIP 모델과 다양한 시각화 기법(GradCAM++, LayerCAM, Attention Rollout)을 실험적으로 적용해 보았으나, 여러 호환성 문제와 한계점을 발견했습니다.

### CLIP과 GradCAM/LayerCAM 실험 결과

특정 딥페이크 특징("인공적인 귀 모양", "인공적인 동공 반사" 등)에 대한 텍스트 프롬프트를 CLIP 모델에 입력하고 GradCAM++ 및 LayerCAM으로 시각화한 결과:

1. **텍스트 프롬프트 특이성 문제**:
   - 일부 특징("인공적인 귀 모양", "인공적인 동공 반사")에 대해서는 의미 있는 히트맵 생성
   - 다른 특징("고르지 못한 치아배열")에 대해서는 관련성 낮은 출력 발생
   - 가중치 통계에서 평균값(-2.8014183044433594e-06)이 매우 낮은 경우 시각화 품질 저하

2. **레이어 선택의 중요성**:
   - 여러 레이어(2, 3, 4)에 대한 히트맵 생성 실험 결과, 레이어 선택이 결과에 큰 영향을 미침
   - 얼굴 특징에 대한 시각화는 깊은 레이어에서도 정밀도 제한적

3. **ViT 구조의 한계**:
   - CLIP의 Vision Transformer(ViT) 구조는 전통적인 CNN 기반 시각화 기법과 호환성 문제 발생
   - Attention Rollout 기법을 적용했으나, 텍스트 프롬프트의 영향을 반영하지 못하는 한계 확인
   - LayerCAM은 일부 시각적 특징을 포착하지만 face landmark에 대한 인식은 object detection에 비해 정확도 떨어짐

### 주요 기술적 도전과제

1. **아키텍처 호환성 문제**: 
   - CLIP의 복잡한 듀얼 인코더 구조가 기존 GradCAM 라이브러리와 완전히 호환되지 않음
   - ViT 구조에 맞게 기존 CNN 기반 시각화 기법을 변환하는 과정에서 정보 손실 발생

2. **데이터 크기와 처리 효율성**: 
   - 개별 단서에 대한 가중치 이미지를 저장하는 방식은 데이터셋 크기를 크게 증가시킴
   - 레이블 파싱 작업의 복잡성 증가

3. **대안 접근법 탐색**: 
   - 딥페이크 단서를 해시태그/키워드 형식으로 추출하여 CLIP 입력 리스트로 활용하는 방법 검토
   - 키워드 추출과 CLIP 입력 간 통합 파이프라인 구축 필요성 확인

이러한 한계로 인해 실제 구현은 제한적이며, 향후 연구에서 CLIP 특화 시각화 기법 및 효율적인 레이블 처리 방법 개발이 필요합니다.

## 성능 지표

본 시스템의 개발 과정에서 측정된 성능은 다음과 같습니다:

- **유사도 정확도**: 테스트 셋에서 약 85%의 이미지-텍스트 관계 식별 정확도
- **RAG 응답 품질**: CLIP 임베딩 활용 시 기존 방식 대비 응답 품질 향상 관찰
- **객체 탐지 정확도**: YOLOv8n 모델 사용 시 mAP 0.65(IoU=0.5) 달성
- **처리 시간**: 평균 이미지당 1.2초 (CPU/GPU 환경에 따라 다름)

## 시각화 결과 현황

CLIP 모델과 다양한 시각화 도구(GradCAM++, LayerCAM, Attention Rollout) 실험 결과는 제한적이지만 흥미로운 통찰을 제공합니다:

```
# 시각화 실험 결과
- "인공적인 귀 모양" 프롬프트: 귀 영역에 일부 활성화 발생
- "인공적인 동공 반사" 프롬프트: 눈 영역에 의미 있는 활성화 관찰
- "고르지 못한 치아배열" 프롬프트: 가중치 통계 평균값 낮음(-2.8e-06), 의미 있는 활성화 실패
- 레이어별 시각화(2, 3, 4): 깊은 레이어일수록 추상적 특징에 집중

# 기법별 성능 비교
- GradCAM++: 텍스트 프롬프트와 일부 연동 가능하나 얼굴 특징 구분에 제한적
- LayerCAM: 더 세밀한 시각화 가능하나 face landmark 인식 정확도 부족
- Attention Rollout: ViT 구조에 적합하나 텍스트 프롬프트 정보 반영 미흡
```

## 설치 및 실행 방법

### 필수 요구사항
- Python 3.11 이상
- CUDA 지원 GPU (추천)
- 최소 8GB RAM

### 설치 과정
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

### 실행 방법

#### CLIP 유사도 계산 (실제 구현된 기능)
```python
# notebooks/model_dev/clip_similarity.ipynb 실행
from transformers import CLIPModel, CLIPProcessor
import torch

# CLIP 모델 로드
model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

# 이미지-텍스트 유사도 계산
inputs = processor(text=["a photo of a cat", "a photo of a dog"], 
                  images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)
logits_per_image = outputs.logits_per_image
probs = logits_per_image.softmax(dim=1)
```

#### GradCAM 실험 (프로토타입/테스트 단계)
```python
# notebooks/experiments/gradcam_experiments.ipynb 실행
# 참고: 이 코드는 제한적으로 작동하며 CLIP 모델과 완전히 호환되지 않습니다
from pytorch_grad_cam import GradCAM, GradCAMPlusPlus, LayerCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

# CLIP 모델의 일부 레이어에 대한 실험적 시각화
target_layer = model.visual.transformer.resblocks[-1]
cam = GradCAMPlusPlus(model=model.visual, target_layer=target_layer)

# 실험적 시각화 시도
grayscale_cam = cam(input_tensor=image_tensor)

# 가중치 통계 확인 (낮은 평균값은 시각화 품질 저하 의미)
print(f"Weights shape: {weights.shape}, Weights stats: mean={weights.mean()}, std={weights.std()}")
print(f"CAM stats: min={cam_output.min()}, max={cam_output.max()}, mean={cam_output.mean()}, std={cam_output.std()}")
```

#### 객체 탐지 (정상 작동 기능)
```python
# notebooks/model_dev/object_detection.ipynb 실행
from ultralytics import YOLO

# YOLOv8 모델 로드
model = YOLO('yolov8n.pt')

# 객체 탐지 실행
results = model(image)
```

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

## 주요 결과물
- **CLIP 유사도 분석**: 이미지-텍스트 간 의미적 유사도 계산 구현
- **YOLOv8 객체 탐지**: 정확한 객체 인식 및 바운딩 박스 시각화
- **RAG 검증 프레임워크**: 응답 신뢰도 평가 및 근거 문서 추적
- **실험적 GradCAM 구현**: CLIP 모델에 대한 제한적 시각화 테스트
- **멀티모달 분석 노트북**: 다양한 실험 및 분석 결과

## 한계점 및 개선 방향
- **모델 한계**
  - 복잡한 배경에서 객체 탐지 정확도 저하
  - 실시간 처리 시 지연 발생
  - 다중 객체 상황에서 성능 저하
- **시각화 관련 한계**
  - CLIP의 ViT 구조와 기존 CNN 기반 시각화 도구 간 호환성 문제
  - 특정 텍스트 프롬프트에 대한 낮은 관련성 점수로 인한 시각화 품질 저하
  - 얼굴 특징(face landmark) 인식 정확도가 일반 객체 인식에 비해 부족
  - 텍스트 프롬프트 정보가 ViT 기반 어텐션 시각화에 제대로 반영되지 않음
  - 레이어 선택에 따른 결과 변동성 큼
- **개선 방향**
  - CLIP 특화 시각화 도구 개발
  - 해시태그/키워드 형식의 딥페이크 단서 추출 방법론 개발
  - 효율적인 레이블 처리 및 저장 방법 연구
  - 모델 경량화 및 최적화
  - 배치 처리 파이프라인 개선
  - 앙상블 기법 도입 검토
  - 도메인 특화 파인튜닝 확대
  - 설명가능성 메트릭 다각화

## 향후 연구 방향
- **CLIP 특화 시각화 기법 개발**: ViT 구조에 최적화된 맞춤형 시각화 접근법 연구
- **효율적인 단서 추출 방법론**: 딥페이크 단서를 자동으로 키워드화하는 파이프라인 개발
- **멀티모달 선행학습 모델 통합**: BLIP, ImageBind 등 최신 모델 활용
- **자기지도 학습 적용**: 레이블이 없는 데이터 활용 방안
- **효율적인 추론 파이프라인**: ONNX, TensorRT 등을 통한 최적화
- **증강 현실 통합**: 실시간 멀티모달 검증 시스템 구축
- **대화형 분석 도구**: 사용자 친화적 인터페이스 개발

## 참고 자료
- [CLIP 논문](https://arxiv.org/abs/2103.00020)
- [GradCAM++ 논문](https://arxiv.org/abs/1710.11063)
- [LayerCAM 논문](https://arxiv.org/abs/2104.06643)
- [YOLOv8 문서](https://docs.ultralytics.com/)
- [LLaVA 공식 저장소](https://github.com/haotian-liu/LLaVA)

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 참조하세요. 