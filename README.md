# TBR

Totally Broken. RPG 게임의 기획을 보관하고 발전시키는 저장소입니다.
개발자와 에이전트가 같은 설계를 읽을 수 있도록 일반 텍스트 파일과 상대 경로를 사용합니다.

## 시작하기

1. [작업 규칙](AGENTS.md)을 읽습니다.
2. [프로젝트 기준](planning/project.md)에서 범위와 원칙을 확인합니다.
3. [기획 색인](index/catalog.json)에서 ID, 제목, 태그로 관련 문서를 찾습니다.
4. [미정 사항](planning/questions.md)과 관련 원문을 읽고 작업을 이어갑니다.

대화 기록이나 특정 서비스의 메모리가 없어도 이 순서로 문맥을 복원할 수 있어야 합니다.

## 파일 구조

| 경로 | 역할 |
| --- | --- |
| `planning/project.md` | 사용자가 확정한 프로젝트 범위와 원칙 |
| `planning/inbox/` | 사용자 발언 원문과 아직 정리되지 않은 입력 |
| `planning/questions.md` | 현재 미정 사항과 확인이 필요한 질문 |
| `planning/design/` | 주제별 기획. 실제 내용이 생길 때 생성 |
| `planning/data/` | 구조화된 JSON·CSV 기획 데이터. 필요할 때 생성 |
| `planning/decisions/` | 선택한 안, 근거, 대체한 결정. 필요할 때 생성 |
| `planning/archive/` | 폐기하거나 대체된 문서. 필요할 때 생성 |
| `index/` | 기획 파일의 위치, 상태, 출처, 관계를 담은 색인 |
| `templates/` | 새 문서를 위한 작성 틀 |
| `tools/` | 설계 파일의 구조적 무결성 검사 |

빈 게임 시스템이나 임의의 설정은 미리 만들지 않습니다. 폴더는 실제 기획 내용에 맞춰 늘립니다.

## 검증

Python 3.10 이상이 있으면 저장소 루트에서 실행합니다. 외부 패키지는 필요하지 않습니다.

```text
python tools/check_integrity.py
python -m unittest discover -s tests
```

검사기는 색인, 파일, 참조, JSON·CSV 형식을 확인합니다. 기획의 논리적 모순이나 재미를 판정하지는 않습니다.
설계 자체를 읽거나 편집하는 데 Python은 필요하지 않습니다.
