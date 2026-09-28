# Render에 배포하기

이 프로젝트를 실제로 인터넷에서 접속 가능한 주소로 올리는 절차입니다.
아래 단계는 GitHub 계정과 Render 계정이 필요하고, 계정 생성·로그인·결제
정보 입력처럼 본인 확인이 필요한 부분은 직접 진행하셔야 합니다.

## 1. GitHub에 코드 올리기

1. https://github.com 에서 새 저장소(Repository)를 하나 만듭니다.
   이름은 예: `palm-report` (Public/Private 아무거나 상관없습니다).
   "Add a README" 등은 체크하지 말고 빈 저장소로 만드세요.
2. 압축 풀어둔 이 프로젝트 폴더에서 터미널을 열고 아래 명령을 순서대로
   실행합니다(첫 줄의 URL은 방금 만든 저장소 주소로 바꾸세요).

   ```bash
   git remote add origin https://github.com/사용자아이디/palm-report.git
   git branch -M main
   git push -u origin main
   ```

   (이미 이 프로젝트에는 `git init`과 첫 커밋이 되어 있는 상태로
   전달드렸습니다. 위 3줄만 실행하면 됩니다.)

## 2. Render에서 새 서비스 만들기

1. https://render.com 에서 회원가입(GitHub 계정으로 로그인하면 저장소
   연결이 더 편합니다).
2. 대시보드에서 **New +** → **Blueprint** 를 선택하고, 방금 올린
   `palm-report` 저장소를 연결합니다. 저장소 안의 `render.yaml`을
   Render가 자동으로 읽어서 Docker 기반 웹 서비스를 만들어줍니다.
   (Blueprint 메뉴가 안 보이면 **New +** → **Web Service** → 저장소
   선택 → Runtime을 **Docker**로 지정해도 동일하게 됩니다.)
3. 배포 설정 화면에서 **Environment Variables**에 아래 값을 추가합니다.
   - Key: `ANTHROPIC_API_KEY`
   - Value: 발급받으신 실제 키 (`sk-ant-...`)
4. **Create Web Service** (또는 Blueprint 적용)를 누르면 빌드가
   시작됩니다. Dockerfile 안에서 Chromium까지 설치하기 때문에 첫 빌드는
   5~10분 정도 걸릴 수 있습니다.

## 3. 확인

빌드가 끝나면 Render가 `https://palm-report-xxxx.onrender.com` 같은
주소를 줍니다. 그 주소로 접속하면 손 사진 업로드 폼이 뜨고, 제출하면
실제 API로 분석한 PDF가 다운로드됩니다.

무료 플랜은 15분 동안 방문자가 없으면 서버가 잠들고, 다음 방문자가
접속할 때 다시 깨어나는 데 1분 정도 걸립니다(그 사이 로딩 화면을
보게 됩니다). 실제로 손님을 받기 시작해서 이 지연이 불편해지면, 유료
플랜(월 7달러대)으로 올리면 항상 켜져 있는 상태로 바뀝니다.

## 나중에 코드를 수정하면

로컬에서 파일을 고친 뒤 아래처럼 GitHub에 다시 올리면, Render가 자동으로
감지해서 새로 빌드·배포합니다.

```bash
git add .
git commit -m "수정 내용 설명"
git push
```
