# 프로젝트 파일/폴더 구조 및 보안 이슈 점검

## 1. 파일/폴더 트리 (진행 중)

- 전체 디렉토리 및 파일 구조를 자동으로 탐색하여 기록합니다.
- 각 파일별로 보안 이슈(민감정보 포함 여부)를 점검합니다.

---

## 2. 체크 완료 파일 리스트 (자동 관리)

- 아래 리스트는 점검이 완료된 파일의 전체 경로를 기록합니다.
- 중복/누락 없이 관리되며, 보안 이슈 점검 결과와 연동됩니다.

- 00_docs/api_key/git_key.txt
- 01_agents/approval_agent/gw_agent/tmp/api_agent.py
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/LLaVA_tuning.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/detection/QwQ_detection.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/detection/Llama_detection.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/fine.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/finetuning_model.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/QwQ_rag.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/rag_performance_visual.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/Llama_rag.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/Llama_rag copy.ipynb
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/CLIP_RAG.ipynb
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_local.py
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_remote.py
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_rag.py
- 99_archive/MCP_example/langgraph-mcp-agents/README.md
- 99_archive/MCP_example/langgraph-mcp-agents/README_KOR.md
- 99_archive/MCP_example/langgraph-mcp-agents/MCP-HandsOn-KOR.ipynb
- 99_archive/MCP_example/langgraph-mcp-agents/requirements.txt
- 99_archive/MCP_example/langgraph-mcp-agents/pyproject.toml
- 99_archive/MCP_example/langgraph-mcp-agents/.gitignore

---

## 3. 보안 이슈 점검 (진행 중)

- 각 파일별로 API Key, 비밀번호, 토큰, IP 등 민감 정보 포함 여부를 점검합니다.
- 발견된 이슈는 아래에 계속 추가됩니다.

---

### [진행상황 예시]

- 00_docs/api_key/git_key.txt : [O] GitHub Personal Access Token 포함 (유출 금지)
- 01_agents/approval_agent/gw_agent/tmp/api_agent.py : [△] .env에서 API Key 로드, 코드 내 직접 노출 없음
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/LLaVA_tuning.ipynb : [X] 민감정보 없음 (상단 기준)
- 03_cv-multimodal/deepfake/notebooks/model_dev/detection/QwQ_detection.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/detection/Llama_detection.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/fine.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/finetuning/finetuning_model.ipynb : [X] 민감정보 없음 (상단 기준)
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/QwQ_rag.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/rag_performance_visual.ipynb : [X] 민감정보 없음 (상단 기준)
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/Llama_rag.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/Llama_rag copy.ipynb : [O] Together API Key 하드코딩 (유출 금지)
- 03_cv-multimodal/deepfake/notebooks/model_dev/rag/CLIP_RAG.ipynb : [△] OpenAI API Key는 .env에서 로드, 코드 내 직접 노출 없음
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_local.py : [X] 민감정보 없음 (host=0.0.0.0은 개발/테스트용, 실서비스시 주의)
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_remote.py : [X] 민감정보 없음 (host=0.0.0.0은 개발/테스트용, 실서비스시 주의)
- 99_archive/MCP_example/langgraph-mcp-agents/mcp_server_rag.py : [△] .env에서 API Key 로드, 코드 내 직접 노출 없음
- 99_archive/MCP_example/langgraph-mcp-agents/README.md : [X] 실제 키/비밀번호 등 민감정보 없음, 예시만 존재
- 99_archive/MCP_example/langgraph-mcp-agents/README_KOR.md : [X] 실제 키/비밀번호 등 민감정보 없음, 예시만 존재
- 99_archive/MCP_example/langgraph-mcp-agents/MCP-HandsOn-KOR.ipynb : [△] .env에서 API Key 로드, 코드 내 직접 노출 없음
- 99_archive/MCP_example/langgraph-mcp-agents/requirements.txt : [X] 민감정보 없음, python-dotenv 등 환경변수 패키지 사용
- 99_archive/MCP_example/langgraph-mcp-agents/pyproject.toml : [X] 민감정보 없음, python-dotenv 등 환경변수 패키지 사용
- 99_archive/MCP_example/langgraph-mcp-agents/.gitignore : [O] .env 등 민감정보 파일 git 추적 제외

---

> 이 문서는 자동으로 계속 업데이트됩니다. 