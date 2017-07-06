# Swak 개발자 문서

여기에서는 Swak 자체 또는 Swak의 플러그인 개발자를 위한 내용을 설명한다.

## 로그 설정

설정 파일안의 `logger` 필드 를 이용해서, Swak의 로그에 대한 설정을 할 수있다. 기본 설정은 아래와 같다.

```yml
logger:
    version: 1

    formatters:
        simpleFormater:
            format: '%(asctime)s %(threadName)s [%(levelname)s] - %(message)s'
            datefmt: '%Y-%m-%d %H:%M:%S'

    handlers:
        console:
            class: logging.StreamHandler
            formatter: simpleFormater
            level: DEBUG
            stream: ext://sys.stdout
        file:
            class : logging.handlers.RotatingFileHandler
            formatter: simpleFormater
            level: DEBUG
            filename: '{SWAK_HOME}/logs/{SWAK_SVC_NAME}-log.txt'g
            maxBytes: 10485760
            backupCount: 10

    root:
        level: DEBUG
        handlers: [console, file]
```

기본 로그 설정은 다음과 같은 뜻이다:

- 로그의 필드 구분자는 탭(`\t\`) 이다.
- 표준 출력과 파일 양쪽으로 로그를 남긴다.
- 양족 다 로그 레벨은 `DEBUG`이다. 
- 로그는 실행 파일이 있는 폴더 아래 `logs/`폴더에 남는다.
- 파일은 100MiB 단위로 로테이션 하며, 최대 10개까지 남는다.

만약, 이중에 일부 수정이 필요하다면 수정이 필요한 필드만 계층을 유지하고 기입하면 된다:

```yml
logger:
    handlers:
        file:
            level: CRITICAL
            filename: C:\logs\{SWAK_SVC_NAME}-log.txt
```

위와 같이 설정하면 다른 것들은 기본값 그대로 두고, 파일 로그 핸들러의 레벨, 저장 경로만 수정하게 된다.

# Swak 플러그인 개발

여기에서는 Swak 플러그인 개발에 대해 설명한다.

아래와 같은 다양한 플러그인을 조합하여 개별 테스트를 정의한다.

## 플러그인 분류

플러그인은 크게 입력, 파서, 변환, 버퍼, 출력 그리고 명령 플러그인의 여섯가지 타입으로 나뉜다. 각 타입별 플러그인은 다음과 같은 패키지명 형식으로 시작한다.

- 입력 플러그인: `in.`
- 파서 플러그인: `par.`
- 변환 플러그인: `tr.`
- 버퍼 플러그인: `buf.`
- 출력 플러그인: `out.`
- 명령 플러그인: `cmd.`

이후의 플러그인의 이름은 클래스 이름 형식을 따른다.

### 입/출력 플러그인 처리 흐름

일반적으로 플러그인은 종류별로 다음과 같은 역할을 순서대로 수행한다.

- 입력: 데이터 소스에서 텍스트를 읽거나 생성하여 라인으로 변환
- 파서: 라인을 파싱하여 Dictionary 형태의 레코드로 변환
- 변환: 레코드의 특정 필드를 추가, 삭제, 변경 (선택적)
- 버퍼: 레코드를 일정한 크기 또는 시간을 청크로하여 버퍼링 (선택적)
- 출력: 개별 레코드 또는 버퍼링된 청크를 출력 대상에 쓴다.

이외에 명령 플러그인은 테스크의 단계별로 다양한 일을 한다.

<img src="../images/plugin_flow.png" width="850" />

## 플러그인 기본 클래스

실재 플러그인 구현은 타입별 부모 클래스들을 상속받아 구현한다. 타입별 기본 클래스를 살펴부자. 

> 부모 클래스에서 필수 구현 멤버 함수는 자식 클래스에서도 필수 구현이다.

### BasePlugin 클래스

모든 플러그인은 이 클래스를 상속받는다.

```python
class Plugin(Object):
    
    def configure(self, conf):
        ...

    def start(self):
        ...

    def stop(self):
        ...

    def shutdown(self):
        ...
```

다음과 같은 메소드를 갖고 있다.

#### configure (필수 구현)

```python
def configure(self, conf):
    pass
```

이 메소드는 설정 정보(`conf`)를 받아 다음과 같은 처리를 구현해야 한다.

- 설정 정보가 맞는지 검증
  꼭 필요한 필드가 있는지? 적절한 범위의 값인지? 논리적 오류가 없는지 등을 체크하고, 만약 문제가 있으면 `ConfgError('에러 내용')`으로 예외를 발생시킨다.
- 설정 정보에 이상이 없으면, 관련 멤버 변수로 설정 정보를 저장한다.
- 설정 정보에 없는 변수는 기본 값으로 초기화한다.

#### start

이 메소드는 설정을 처리한 후, 테스크가 시작할 때 호출된다.

플러그인에서 사용할 파일, 스레드 등 리소스 생성을 여기에서 생성한다.

#### stop

이 메소드는 테스크가 종료를 준비할 때 호출된다.

스레드 정지 플래그의 설정 등 실패하지 않는 간단한 일을 해야한다.

#### shutdown

이 메소드는 테스크가 완전 종료되는 시점에서 호출된다.

`start`에서 만들어 두었던 파일, 스레드등 리소스를 여기에서 닫거나 제거한다.

### BaseInput 클래스

이것을 상속받아 입력 플러그인 클래스를 만든다. 

```python
class BaseInput(BasePlugin):
    
    def read(self):
        ...

    def filter(self, text):
        ....
```

다음과 같은 메소드를 갖고 있다.

#### read (필수 구현)

소스에서 라인으로 구분되는 텍스트를 읽어와 라인 단위로 반환

#### filter

읽어온 라인들 중 의미 있는 것만 반환한다. 기본은 모든 라인을 반환.

### BaseParser 클래스

이것을 상속받아 파서 클래스를 만든다.

```python
class BaseParser(BasePlugin):

    def parse(self, text):
        ...
```

다음과 같은 메소드를 갖고 있다.

#### parse (필수 구현)

Input에서 넘어온 텍스트의 파싱하여 레코드를 반환

### BaseTransform 클래스

이것을 상속받아 변환 클래스를 만든다.

```python
class BaseTransform(BasePlugin):

    def transform(self, records):
        ....
```

`configure` 함수에서 받은 레코드에 대해 템플릿을

다음과 같은 메소드를 갖고 있다.

#### transform (필수 구현)

`configure`에서 받은 레코드들에 대해 템플릿을 확장한 후, 인자로 받은 레코드에 수정을 가한다.

### BaseOutput 클래스

이것을 상속받아 출력 클래스를 만든다.

```python
class BaseOutput(Plugin):

    def process(self, records):
        ...

    def write(self, chunk):
        ...
```

다음과 같은 메소드를 갖고 있다.

#### process (또는 write 필수 구현)

건네진 레코드들을 출력

#### write (또는 process 필수 구현)

건네진 청크를 출력

### BaseCommand 클래스

이것을 상속받아 명령 클래스를 만든다.

```python
class BaseCommand(Plugin):
    
    def execute(self)
```

다음과 같은 메소드를 갖고 있다.

#### execute (필수 구현)

명령이 수행할 코드.

## 파이썬 버전

Swak는 파이썬 2.7와 3.5를 지원한다. 

> 3.5를 지원하는 이유는 현재 PyInstaller가 지원하는 가장 높은 버전이기 때문이다.

플러그인 개발자는 다음을 기억하자.

- 가급적 파이썬 2.7와 3.5 양쪽에서 돌아가도록 개발하자. (tox를 활용!)
- 2.7만 지원하는 경우는, 2.7에서만 지원되는 외부 패키지를 사용하기 위해서로 한정
- 2.7만 지원하는 하나의 플러그인을 사용하려면, 사용자는 Swak을 파이썬 2.7로 빌드해야 한다.
- 이는 다른 모든 플러그인도 2.7 기반으로 동작하게 된다는 뜻

# Swak 플러그인 만들기
여기에서는 플러그인 만드는 법을 살펴보겠다. Swak 플러그인은 플러그인 디렉토리(`swak/swak/plugins`)에 위치하며, Swak이 기동할 때 자동으로 로딩된다. 기본 플러그인은 플러그인 디렉토리에 Swak과 함께 배포된다. 외부 플러그인은 누구나 만들어서 플러그인 디렉토리에 추가하면 된다.

## 플러그인 규칙

여기서 Swak의 플러그인 코드는 GitHub을 통해서 관리되는 것으로 가정하며, 다음과 같은 규칙을 따라야 한다.

- GitHub의 저장소(Repository) 이름은 `swak-plugin-` 으로 시작한다.
- 정해진 규칙에 맞게 문서화 되어야 한다.
- 버전 정보를 갖는다.
- 플러그인이 의존하는 패키지가 있는 경우 `requirements.txt` 파일을 만들고 명시한다. (의존 패키지가 없다면 만들지 않는다.)

### 문서화 규칙

각 플러그인은 `README.md` 파일에 문서화를 해야한다. GitHub의 [Markdown 형식](https://guides.github.com/features/mastering-markdown/)에 맞게 다음과 같이 작성한다.

- 처음에 H1(`#`)으로 `swak-plugin-NAME` 형식으로 플러그인의 이름 헤더가 온다.
    - 본문으로 플러그인에 대한 간단한 설명을 한다.
- 그 아래 H2(`##`)로 `설정 예시` 헤더가 온다.
    - 본문으로 설정 파일의 간단한 예를 보여준다.
- 그 아래 H2(`##`)로 `동작 방식` 헤더가 온다.
    - 본문으로 플러그인의 내부 동작에 관한 설명을 한다.
- 그 아래 H2(`##`)로 `인자들` 헤더가 온다.
    - 그 아래 각 인자에 대해 H3(`###`) 헤더가 온다.
        - 본문으로 인자에 대해 설명한다.

즉, 아래와 같은 구조를 같는다.

```markdown
# swak-plugin-NAME

## 설정 예시

## 동작 방식

## 인자들
```

### 플러그인 버전 규칙

[유의적 버전 문서](http://semver.org/lang/ko/)를 참고하여 플러그인 버전을 명시한다.

> 요약) 버전을 주.부.수 숫자로 하고:
> 
> 기존 버전과 호환되지 않게 API가 바뀌면 “주(主) 버전”을 올리고,
> 기존 버전과 호환되면서 새로운 기능을 추가할 때는 “부(部) 버전”을 올리고,
> 기존 버전과 호환되면서 버그를 수정한 것이라면 “수(修) 버전”을 올린다.

### 환경 버전 규칙

플러그인은 파이썬 및 Swak 환경 아래에서 동작한다. 따라서 플러그인 개발자가 지원하는 파이썬 및 Swak 버전을 명기해야 한다.

## 샘플 플러그인
각 행마다 행번호를 붙여주는 간단한 출력용 플러그인 `linenumber`을 예제로 알아보자.

1. 먼저 GitHub에서 `swak-plugin-linenumber`라는 빈 저장소를 만든다. (이때 원하는 라이센스를 선택하고 README.md 생성을 체크한다.)
2. Swak의 `plugins` 폴더로 이동한다.
3. 저장소를 `clone`한다.

    `git clone https://github.com/GitHub계정/swak-plugin-linenumber.git linenumber`

4. `main.py` 파일을 만들고 플러그인 코드를 작성한다.
5. 테스트용 설정 파일 `cfg-test.yml`을 작성한다.
6. Swak의 기본 폴더로 돌아와 `python swak.runner swak/plugins/linenumber/cfg-test.yml`로 실행해본다.

## 개발용 실행

## 외부 프로세스 호출

### 외부 프로세스 호출 흐름
외부 실행파일이나 스크립트를 실행할 수 있다. 단, 그것들은 입력 파일명과 출력 파일명을 인자로 받아 실행하도록 구성되어야 한다.

<img src="../images/process_flow.png" width="700" />
