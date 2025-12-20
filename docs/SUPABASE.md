# Supabase Integration Guide

이 문서는 Portfolio AI에서 Supabase를 활용하는 방법을 설명합니다.

## 목차

1. [개요](#개요)
2. [설정 방법](#설정-방법)
3. [LangGraph Checkpointing](#langgraph-checkpointing)
4. [대화 히스토리 관리](#대화-히스토리-관리)
5. [추가 활용 방안](#추가-활용-방안)

## 개요

Supabase는 PostgreSQL 기반의 오픈소스 Firebase 대안입니다. Portfolio AI에서는 다음 용도로 활용할 수 있습니다:

### 현재 구현된 기능

1. **LangGraph Checkpointing** - AsyncPostgresSaver를 통한 대화 상태 저장
2. **대화 히스토리** - 사용자별 대화 기록 조회 및 관리
3. **데이터베이스 연결 풀링** - 효율적인 연결 관리

### 추가 활용 가능한 기능

4. **벡터 임베딩 저장** - pgvector 확장을 통한 RAG
5. **사용자 인증** - Supabase Auth 연동
6. **실시간 기능** - Supabase Realtime
7. **파일 스토리지** - Supabase Storage
8. **블로그 콘텐츠 저장**

## 설정 방법

### 1. Supabase 프로젝트 생성

1. [supabase.com](https://supabase.com)에서 프로젝트 생성
2. 데이터베이스 비밀번호 설정
3. Project Settings → Database에서 Connection String 복사

### 2. 환경 변수 설정

`.env` 파일에 연결 문자열 추가:

```bash
SUPABASE_CONNECTION_STRING="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
```

### 3. 필요한 패키지 확인

`pyproject.toml`에 이미 포함되어 있습니다:

```toml
dependencies = [
    "langgraph-checkpoint-postgres>=2.0.10",
    "psycopg[binary]>=3.2.0",
]
```

## LangGraph Checkpointing

### 자동 테이블 생성

AsyncPostgresSaver는 첫 실행 시 자동으로 다음 테이블을 생성합니다:

- `checkpoints` - 그래프 상태 스냅샷 저장
- `checkpoint_writes` - 보류 중인 쓰기 작업
- `checkpoint_migrations` - 스키마 마이그레이션 추적

**별도 스키마 작성 불필요!** 자동으로 생성됩니다.

### 사용 방법

#### 기본 사용

```python
from src.agent.graph import create_multi_rag_graph

# 그래프 생성 (checkpointer 자동 포함)
graph = create_multi_rag_graph(["metadata_search"])

# thread_id로 대화 세션 구분
config = {
    "configurable": {
        "thread_id": "user-123-session-1"
    }
}

# 대화 실행
response = await graph.ainvoke(
    {"messages": [{"role": "user", "content": "안녕하세요"}]},
    config=config
)

# 같은 thread_id로 다시 실행하면 이전 상태 복원
response = await graph.ainvoke(
    {"messages": [{"role": "user", "content": "이전 대화 기억해?"}]},
    config=config
)
```

#### 새 대화 시작

```python
from src.core.conversation import generate_thread_id

# 새 thread_id 생성
thread_id = generate_thread_id()  # "thread-550e8400-e29b-41d4-a716-446655440000"

config = {"configurable": {"thread_id": thread_id}}
```

### Checkpointing 동작 방식

1. **자동 저장**: 각 노드 실행 후 자동으로 상태 저장
2. **멀티 스레드**: thread_id별로 독립적인 세션 유지
3. **상태 복원**: 동일한 thread_id로 실행 시 이전 상태에서 이어감
4. **Time Travel**: 이전 체크포인트로 롤백 가능

## 대화 히스토리 관리

### 대화 조회

```python
from src.core.conversation import get_conversation_history

# 특정 스레드의 대화 내역 가져오기
messages = await get_conversation_history(
    thread_id="thread-123",
    limit=10  # 최근 10개 메시지
)

for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

### 대화 목록 조회

```python
from src.core.conversation import list_conversations

# 모든 대화 목록
conversations = await list_conversations(limit=50)

for conv in conversations:
    print(f"Thread: {conv['thread_id']}")
    print(f"Messages: {conv['message_count']}")
    print(f"Last updated: {conv['last_updated']}")
    print(f"Preview: {conv['first_message']}")
```

### 대화 삭제

```python
from src.core.conversation import delete_conversation

# 특정 대화 삭제
success = await delete_conversation("thread-123")
if success:
    print("대화가 삭제되었습니다")
```

### 체크포인트 메타데이터

```python
from src.core.conversation import get_checkpoint_metadata

metadata = await get_checkpoint_metadata("thread-123")
print(f"Last updated: {metadata['last_updated']}")
print(f"Metadata: {metadata['metadata']}")
```

## 추가 활용 방안

### 1. 벡터 임베딩 저장 (RAG)

Supabase는 `pgvector` 확장을 지원합니다.

#### 확장 활성화

Supabase SQL Editor에서:

```sql
-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 임베딩 테이블 생성
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW 인덱스 생성 (빠른 벡터 검색)
CREATE INDEX ON document_embeddings
USING hnsw (embedding vector_cosine_ops);
```

#### Python에서 사용

```python
from src.core.database import get_supabase_client
import json

client = get_supabase_client()

# 임베딩 저장
await client.execute_command(
    """
    INSERT INTO document_embeddings (content, embedding, metadata)
    VALUES (%s, %s, %s)
    """,
    (
        "문서 내용",
        "[0.1, 0.2, ...]",  # OpenAI embedding
        json.dumps({"source": "blog", "author": "syshin"})
    )
)

# 유사도 검색
results = await client.execute_query(
    """
    SELECT content, metadata,
           1 - (embedding <=> %s::vector) AS similarity
    FROM document_embeddings
    WHERE 1 - (embedding <=> %s::vector) > 0.7
    ORDER BY embedding <=> %s::vector
    LIMIT 5
    """,
    (query_embedding, query_embedding, query_embedding)
)
```

### 2. 여러 데이터베이스 연결

각기 다른 용도로 여러 DB를 사용할 수 있습니다:

```python
from src.core.database import SupabaseClient

# Supabase: 메인 데이터 + checkpointing
supabase_client = SupabaseClient(
    os.getenv("SUPABASE_CONNECTION_STRING")
)
await supabase_client.initialize()

# 별도 PostgreSQL: 분석/로그
analytics_client = SupabaseClient(
    os.getenv("ANALYTICS_CONNECTION_STRING")
)
await analytics_client.initialize()

# Pinecone/Weaviate: 벡터 검색 (필요시)
# from pinecone import Pinecone
# pinecone = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
```

### 3. Supabase Auth 연동

```python
# Supabase Python 클라이언트 설치 필요
# pip install supabase

from supabase import create_client, Client

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# 사용자 인증
user = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password"
})

# 인증된 사용자 정보를 thread_id와 연결
thread_id = f"user-{user.user.id}-{uuid4()}"
```

### 4. Supabase Realtime (실시간 기능)

```python
# WebSocket을 통한 실시간 업데이트 구독
channel = supabase.channel('conversation-updates')

def handle_update(payload):
    print(f"New message: {payload}")

channel.on('INSERT', lambda payload: handle_update(payload)).subscribe()
```

### 5. Supabase Storage (파일 저장)

```python
# 파일 업로드
with open('document.pdf', 'rb') as f:
    supabase.storage.from_('documents').upload('path/document.pdf', f)

# 파일 URL 가져오기
url = supabase.storage.from_('documents').get_public_url('path/document.pdf')
```

## 데이터베이스 모니터링

### Supabase Dashboard

1. **Database** 탭에서 테이블 확인
2. **SQL Editor**에서 직접 쿼리 실행
3. **Table Editor**에서 데이터 조회/수정

### 체크포인트 테이블 확인

```sql
-- 모든 스레드 목록
SELECT DISTINCT thread_id, COUNT(*) as checkpoint_count
FROM checkpoints
GROUP BY thread_id
ORDER BY MAX(ts) DESC;

-- 특정 스레드 상세
SELECT *
FROM checkpoints
WHERE thread_id = 'thread-123'
ORDER BY ts DESC;

-- 저장 공간 확인
SELECT
    pg_size_pretty(pg_total_relation_size('checkpoints')) as checkpoints_size,
    pg_size_pretty(pg_total_relation_size('checkpoint_writes')) as writes_size;
```

## 성능 최적화

### 연결 풀링

`database.py`에서 이미 구현됨:

```python
# 연결 풀 설정
AsyncConnectionPool(
    conninfo=connection_string,
    min_size=2,   # 최소 연결 수
    max_size=10,  # 최대 연결 수
    timeout=30,   # 타임아웃 (초)
)
```

### 체크포인트 정리

오래된 체크포인트 삭제:

```sql
-- 30일 이상 된 체크포인트 삭제
DELETE FROM checkpoints
WHERE ts < NOW() - INTERVAL '30 days';

-- 특정 스레드의 오래된 체크포인트만 유지
DELETE FROM checkpoints
WHERE thread_id = 'thread-123'
  AND checkpoint_id NOT IN (
    SELECT checkpoint_id
    FROM checkpoints
    WHERE thread_id = 'thread-123'
    ORDER BY ts DESC
    LIMIT 100
  );
```

## 트러블슈팅

### 연결 문제

```python
# 연결 테스트
from src.core.database import get_supabase_client

try:
    client = get_supabase_client()
    await client.execute_query("SELECT 1")
    print("✅ 연결 성공")
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

### 체크포인트 문제

```python
# setup() 수동 실행
from src.core.database import get_supabase_client

client = get_supabase_client()
await client.checkpointer.setup()
```

### 로그 확인

```python
from src.core.logger import get_logger

logger = get_logger(__name__)
logger.setLevel("DEBUG")  # 상세 로그
```

## 참고 자료

- [Supabase 공식 문서](https://supabase.com/docs)
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [pgvector 가이드](https://github.com/pgvector/pgvector)
- [AsyncPostgresSaver API](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver)
