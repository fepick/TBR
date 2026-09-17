# 기획 색인 규약

`catalog.json`은 검색용 메타데이터의 단일 원본입니다. 실제 규칙과 원문은 `path`의 파일에 저장합니다.
색인의 요약은 탐색을 위한 것이므로 구현이나 의사결정 전에 실제 파일을 읽습니다.

## 등록 단위

`planning/` 아래의 모든 MD, JSON, CSV 기획 파일을 각각 한 번 등록합니다.
폴더 탐색 안내만 담는 `README.md`는 예외입니다. 안내 파일에 기획 원본을 숨기지 않습니다.
작업 규약, 템플릿, 검사 도구는 기획 파일이 아니므로 등록하지 않습니다.

| 필드 | 의미 |
| --- | --- |
| `id` | 유형별 접두사와 네 자리 번호. 이동·개명 후에도 유지 |
| `kind` | 아래 유형 중 하나 |
| `status` | 아래 상태 중 해당 유형에 허용된 값 |
| `title` | 사람이 읽는 제목 |
| `path` | 저장소 루트 기준 상대 경로. `/` 사용 |
| `summary` | 검색에 필요한 짧은 요약. 기획 원본을 대체하지 않음 |
| `tags` | 주제와 동의어 등 검색어 배열 |
| `source_ids` | 근거인 사용자 발언 원문 ID 배열. `source` 유형만 참조 |
| `related_ids` | 의존·충돌·대체·설명 등 관련 문서 ID 배열 |
| `created` | 최초 등록일 `YYYY-MM-DD` |
| `updated` | 마지막 내용 또는 메타데이터 변경일 `YYYY-MM-DD` |

날짜는 Asia/Seoul 기준으로 기록합니다. 원문 파일에도 기록일을 명시합니다.
새 번호는 같은 접두사에서 기존 최댓값 다음 번호를 사용합니다. 삭제된 번호를 재사용하지 않습니다.
여러 작업자가 편집할 때에는 최종 저장 전에 최신 색인과 ID 충돌을 확인합니다.

## 유형과 상태

| `kind` | ID 접두사 | 허용 상태 |
| --- | --- | --- |
| `source` | `SRC` | `recorded` |
| `project` | `PRJ` | `draft`, `confirmed`, `superseded`, `archived` |
| `idea` | `IDEA` | `draft`, `proposed`, `confirmed`, `superseded`, `archived` |
| `spec` | `SPEC` | `draft`, `proposed`, `confirmed`, `superseded`, `archived` |
| `decision` | `DEC` | `proposed`, `confirmed`, `superseded`, `archived` |
| `question` | `QUE` | `open`, `resolved`, `archived` |
| `dataset` | `DATA` | `draft`, `proposed`, `confirmed`, `superseded`, `archived` |

- `recorded`: 발언을 저장한 상태. 발언 내용이 확정 기획이라는 뜻은 아닙니다.
- `draft`: 에이전트가 정리하거나 작성 중인 안.
- `proposed`: 검토 대상인 제안. 확정 사항으로 사용하지 않습니다.
- `confirmed`: 사용자가 명시한 결정이나 확정 지시. 근거인 `source_ids`가 필요합니다.
- `open`: 미해결 질문.
- `resolved`: 답과 근거를 본문에 남긴 질문.
- `superseded`: 다른 안으로 대체된 상태. 본문과 `related_ids`에서 후속 기획을 찾을 수 있어야 합니다.
- `archived`: 현재 검토 대상에서 제외한 상태. 이유와 기존 참조를 보존합니다.

확정 상태는 에이전트가 문서를 만들었다는 이유만으로 부여하지 않습니다.
의문문이나 브레인스토밍의 저장은 승인과 다릅니다. 원문과 문맥이 확정 여부의 근거입니다.

## 연결과 데이터

참조 대상은 색인에 있어야 하고 자기 자신을 참조하지 않습니다. 관계는 방향이 있을 수 있으므로 양방향 복제는 필수가 아닙니다.
`source_ids`에는 출처를, `related_ids`에는 관련 기획을 적습니다. 관계의 구체적인 의미는 본문에서 설명합니다.

JSON·CSV 데이터셋은 `dataset`으로 등록하고, 필드와 단위·누락값·고유 키를 설명하는 MD 문서를 `related_ids`로 연결합니다.
데이터 설명 문서는 `spec`으로 별도 색인합니다. `templates/dataset.md`를 사용할 수 있습니다.
내용이 MD인 표는 데이터셋 파일 대신 일반 기획 문서로 등록해도 됩니다.

## 검사 범위

`tools/check_integrity.py`는 필수 필드, ID·경로 중복, 유형·상태 조합, 날짜, 참조, 파일 존재, 미등록 파일,
JSON 파싱 및 CSV 헤더·행 구조, 데이터 설명 문서 연결 여부를 검사합니다.
본문의 Markdown 링크, 단위의 타당성, 사용자 승인 여부, 게임 규칙 사이의 논리적 모순은 사람이 검토합니다.
