# 블로그 콘텐츠 동기화 설정 가이드

이 프로젝트는 블로그 레포지토리(`syshin0116.github.io`)의 `content/` 디렉토리를 자동으로 동기화합니다.

## 📁 구조

```
apphub-ai/
  data/
    blog/
      .git/              ← 블로그 레포의 git (무시됨)
      content/           ← 블로그 콘텐츠 (추적됨)
        AI/
        Dev/
        Events/
        ...
```

- `data/blog`는 블로그 레포를 sparse checkout으로 클론한 디렉토리
- `data/blog/.git/`는 .gitignore에 추가되어 무시됨
- `data/blog/content/` 아래 실제 콘텐츠만 apphub-ai 레포에서 추적

---

## 🔧 초기 설정

### 1. 로컬에서 블로그 콘텐츠 가져오기

```bash
cd /Users/syshin/Desktop/Syshin/apphub-ai
rm -rf data
mkdir -p data/blog
cd data/blog

# Git 초기화 및 sparse checkout 설정
git init
git remote add origin https://github.com/syshin0116/syshin0116.github.io.git
git config core.sparseCheckout true
mkdir -p .git/info
echo "content/" > .git/info/sparse-checkout

# content 디렉토리만 가져오기
git pull origin main
```

### 2. 블로그 레포에 워크플로우 추가

블로그 레포(`/Users/syshin/Desktop/Syshin/quartz`)에 워크플로우 파일을 추가해야 합니다.

```bash
# 블로그 레포로 이동
cd /Users/syshin/Desktop/Syshin/quartz

# 워크플로우 디렉토리 생성
mkdir -p .github/workflows

# 워크플로우 파일 복사
cp /Users/syshin/Desktop/Syshin/apphub-ai/notify-apphub.yml .github/workflows/sync-to-apphub.yml

# 커밋 및 푸시
git add .github/workflows/sync-to-apphub.yml
git commit -m "feat: add workflow to sync content to apphub-ai"
git push
```

### 3. GitHub Secret 확인

블로그 레포에 `APPHUB_DISPATCH_TOKEN` Secret이 설정되어 있는지 확인:
- GitHub → 블로그 레포 → Settings → Secrets and variables → Actions
- `APPHUB_DISPATCH_TOKEN` 존재 확인 ✅

---

## 🔄 동작 방식

### 자동 동기화 흐름

```
1. 블로그 content/ 수정 후 push
   ↓
2. 블로그 워크플로우 (.github/workflows/sync-to-apphub.yml) 실행
   ↓
3. apphub-ai 레포 클론
   ↓
4. apphub-ai/data/blog에서 git pull
   ↓
5. 변경사항 커밋 & apphub-ai에 푸시
   ↓
6. apphub-ai의 재배포 CI/CD 자동 실행 (설정 시)
   ↓
7. 최신 블로그 콘텐츠로 RAG 챗봇 업데이트 ✅
```

### 수동 동기화

필요 시 로컬에서 수동으로 업데이트:

```bash
cd /Users/syshin/Desktop/Syshin/apphub-ai/data/blog
git pull origin main
cd ../..
git add data/blog
git commit -m "chore: manual blog content update"
git push
```

---

## 📝 주의사항

### data/blog 디렉토리 관리

- ✅ **DO**: `data/blog/content/` 아래 파일들은 자동으로 추적됨
- ❌ **DON'T**: `data/blog/.git/` 건드리지 않기 (자동 무시됨)
- ❌ **DON'T**: `data/blog`를 삭제하지 않기 (재설정 필요)

### 충돌 발생 시

블로그 레포와 apphub-ai 양쪽에서 동시에 수정하면 충돌 가능:

```bash
# apphub-ai의 data/blog에서
git status
# 충돌 확인 후 해결
git pull origin main
# 충돌 해결
git add .
git commit
```

---

## 🧪 테스트

### 1. 블로그에서 테스트 파일 생성

```bash
cd /Users/syshin/Desktop/Syshin/quartz
echo "# Test Post" > content/test.md
git add content/test.md
git commit -m "test: add test post"
git push
```

### 2. GitHub Actions 확인

- 블로그 레포 → Actions → "Sync to AppHub AI" 워크플로우 실행 확인
- apphub-ai 레포 → 최근 커밋에 "chore: sync blog content" 확인

### 3. 로컬에서 확인

```bash
cd /Users/syshin/Desktop/Syshin/apphub-ai
git pull
ls data/blog/content/test.md  # 파일 존재 확인
```

---

## 🐛 문제 해결

### 워크플로우가 실행되지 않음

1. 블로그 레포 Actions 탭에서 워크플로우 상태 확인
2. `APPHUB_DISPATCH_TOKEN` Secret 확인
3. 워크플로우 파일 경로: `.github/workflows/sync-to-apphub.yml`

### data/blog가 비어있음

```bash
cd /Users/syshin/Desktop/Syshin/apphub-ai/data/blog
git pull origin main
```

### 권한 오류

PAT(Personal Access Token) 권한 확인:
- `repo` 전체
- `workflow`

---

## 📚 참고

- 블로그 레포: https://github.com/syshin0116/syshin0116.github.io
- apphub-ai 레포: https://github.com/syshin0116/apphub-ai
- Sparse Checkout 참고: https://helloinyong.tistory.com/332
