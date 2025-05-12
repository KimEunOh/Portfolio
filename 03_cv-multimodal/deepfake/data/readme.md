# 데이터셋

## 구성

### image : 학습 이미지

### test_image : 테스트 이미지

### label_data : 레이블링 데이터

### output_data.jsonl : 학습 데이터. 이미지 url과 label 정보를 jsonl 형식으로 저장

### rag_dataset.json : 외부 RAG를 적용하여, 모델이 real로 예측한 이미지에 대해 관련성이 가장 높은 키워드를 추출하여 매칭한 데이터.

## 데이터셋 출처
https://huggingface.co/datasets/OpenRL/DeepFakeFace/tree/main