# Swak

[![Codecov Status](https://codecov.io/gh/haje01/swak/branch/master/graph/badge.svg)](https://codecov.io/gh/haje01/swak)

이 페이지에서는 Swak 사용자를 위한 기본적인 내용을 설명한다. 더 자세한 내용은 아래 링크를 참고한다.

- [개발자 문서](swak/README.md)
- [기본 플러그인 소개](swak/plugins/README.md)

## 무엇인가?

- 멀티 OS(Windows, Linux, macOS)에서
- 서비스(데몬) 형태로
- 다양한 목적을 위한 파이썬 플러그인을 실행하거나
- 외부 프로세스를 실행히주는 
- 틀

## 플러그인 구조

Swak은 어플리케이션의 기본 틀외 모든 기능들을 플러그인으로 구현한다. 다음과 같은 기본 플러그인들이 가진다.

- FileTail - 파일에 추가된 내용 입력으로 가져옴
- Fluentd - Fluentd로 출력
- failover - 출력 실패시 대체

자세한 것은 [기본 플러그인 소개](swak/plugins/README.md)를 참고하자. 

이외에 아래와 같은 다양한 외부 플러그인이 나올 수 있을 것이다.

- DB Tailing
- 시스템(윈도우 이벤트, syslog) 로그 입력으로 가져오기
- 프로세스/커넥션 모니터링
- Elasticsearch, Logstash로 출력

## 코드 설치

> 윈도우에서 설치를 위해서는 사전에 [git 클라이언트](https://git-scm.com/download/win)를 받아서 설치하자.

    git clone https://github.com/haje01/swak.git
    cd swak
    pip install -r requirements.txt
    pip intall .

### 코드 디렉토리 구조

기본적인 코드 디렉토리 구조는 다음과 같다.

```
swak/
  swak/       # 코드 디렉토리
  tests/      # 테스트 코드 디렉토리
  plugins/    # 플러그인 디렉토리

  devhome/    # 개발용 홈 디렉토리
    config.yml  # 개발용 설정 파일
    logs/     # 로그 디렉토리
    run/     # 데몬으로 실행된 경우 .pid 파일 저장
```

## 홈 디렉토리

Swak은 실행을 위해 홈 디렉토리를 필요로 한다. 이것은 다음과 같은 구조를 가진다.

```
  SWAK_HOME\
    config.yml  # 설정 파일
    logs\       # 설정 파일에 따라 실행한 로그가 저장
    run\        # 데몬으로 띄워진 경우 .pid 파일이 저장
```

사용할 홈 디렉토리는 다음과 같은 순서로 결정된다.

1. 스크립트나 실행 파일 인자로 홈 디렉토리 경로를 받은 경우 그것을 이용.
2. `SWAK_HOME` 환경 변수가 설정되어 있으면 그것을 이용.
3. 스크립트나 실행 파일과 같은 디렉토리에 `config.yml`이 있으면 그곳을 홈 디렉토리로 이용.
4. 여기까지 없으면 에러 발생.

필요에 맞게 다음과 같은 식으로 홈 디렉토리를 지정한다.

- 개발을 위해 소스를 받은 경우는 소스 디렉토리 내의  `devhome`의 절대 경로를 스크립트 파일의 인자, 또는 환경 변수로 지정한다. 그러면 그 안의 개발용 `config.yml` 파일을 참고하여 실행된다.
- 본인 만의 커스텀한 설정이 필요한 경우, `devhome/config.yml`을 수정하지 말고, 별도로 디렉토리를 만들고 거기에 `config.yml`을 저장한 후, 홈 디렉토리로 지정해준다. (`logs/`, `run/` 같은 하위 디렉토리는 자동으로 만들어진다.`)
- 바이너리로 빌드되어 배포 될 때는, 일반적으로 실행 파일과 같은 디렉토리에 `config.yml`을 만들어 주면 된다. 

# Swak 활용 예

## Swak 커맨드 라인 명령

Swak은 커맨드라인에서 다양한 명령을 실행할 수 있다.

### 설치된 플러그인 리스트 보기

    swak list

### 특정 플러그인의 도움말 보기

    swak desc in.fakedata

### 간단히 테스트하기

    swak run 'in.fakedata --type people | out.Stdout'

## 설정 파일

설정 파일은 YAML(`*.yml`) 형식으로 Swak이 할 일을 명시한다. 샘플 설정 파일을 통해 Swak의 사용법을 살펴보자.

설정 파일내에 플러그인  플러그인 들은 플러그인 타입별로 각각의 섹션 아래에 선언된다. 예를 들어
입력과 출력 플러그인은 각각 `inputs` 및 `outputs` 섹션의 데이터 스트림 태그 아래에 위치한다.

### 미니멀한 설정 파일의 예

가짜 데이터를 표준 출력을 통해 출력하는 간단한 예이다. `in.fakedata` -> `out.stdout` 순서, 즉 등장 순으로 처리된다.

```yml
streams:
  foo:  # 데이터 스트림 태그
    # 가짜 데이터 생성
    - in.fakedata -type people
    # 표준 출력으로 스트림 보냄
    - out.stdout
```

위의 스크립트는 다음과 같은 식으로 이해하면 된다.
- `inputs`에서는 데이터 스트림 별 입력을 선언한다.
- `foo` 는 데이터 스트림의 태그로, 데이터 스트림을 칭할 때 사용된다.
- `in.fakedata` 플러그인을 통해 가짜 데이터를 생성하고 `foo` 데이터 스트림으로 보낸다.
- `outputs`에서는 데이터 스트림 별 출력을 선언한다.
- `out.stdout` 플러그인은 표준 출력으로 스트림을 보낸다.

### 좀 더 복잡한 예

다음은 특정 파일을 테일링하여 Fluentd로 전송하는 설정 파일의 예이다. 조금 복잡하지만 순서대로 처리된다.

```yml
streams:
  foo:  # 데이터 스트림 태그
    # 주석행을 제거하며 대상 파일 테일링
    - in.filetail -path C:/myprj/logs/mylog.txt -posdir C:/swak_temp/pos -encoding: cp949 --exclude ^\S*#.*
    # 커스텀 포맷 파서
    - par.mylog
    # 5분 단위로 버퍼링
    - buf.file time --min 5
    # Fluentd 전송
    - out.fluentd --server 192.168.0.1 --server: 169.168.0.2 --last /tmp/failed.txt --start_by: ip
```


`in.filetail`은 지정된 파일에서 추가된 내용을 스트림으로 보낸다.

`out.timebuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 시간이 되었을 때만 출력해 지나친 IO를 막아준다.

`out.fluentd` 플러그인은 스트림을 지정된 Fluentd 서버로 보낸다. 이때 하나 이상의 서버를 받고, 에러가 발생하면 다른 리스트로 시도한다. 시작 출력은 `start_by`로 지정하는 값에 의존하여 결정된다. 모든 출력이 실패하면 `last`로 지정된 출력으로 스트림을 보낸다.

### 처리 순서가 순환적인 예

플러그인이 꼭 등장하는 순서대로 시작되는 것은 아니다. 태그의 지정을 통해 순환적으로 처리될 수 있다. 아래의 예를 살펴보자.

```yml
streams:
  detect:
    - tr.exec --cmd "/usr/bin/r /etc/detect_abuse.r"
    - out.stdout

  collect:
    - in.mysqltail --ip 127.0.0.1 --db logdb --table logtbl
    - buf.file size --lines 100 --tag detect
```

이 경우는 먼저 `collect` 스트림에서 `in.mysqltail` -> `buf.file` 처리 후 `detect` 스트림에서 `tr.exec` -> `out.stdout` 순으로 처리된다.

먼저 `in.mysqltail` 플러그인은 지정된 MySQL DB의 테이블에서 추가되는 내용을 스트림으로 보낸다.

`buf.file size`는 스트림의 내용을 파일 버퍼에 쌓아두다가, 지정한 라인(행) 수가 되었을 때 전달해 지나친 IO 사용을 막아준다. 전달시에는 새로운 스트림 `foo.buffered`로 보낸다.

거기에서 `tr.exec` 플러그인은 버퍼링된 청크를 받고, 지정된 별도 프로세스에서 처리한 후, 그 결과를 임시 파일로 받는다. 같은 태그에 관해서는 등장 순서대로 처리되기에, 받은 결과는 `out.stdout` 으로 보내진다.

> 각 스트림은 입력 플러그인이 있다면 등장 순서대로 시작되고, 없다면 매칭되는 데이터가 있을 때 시작된다.

## 설정 파일 테스트하기

커스텀한 설정 파일을 테스트하는 경우를 생각해보자. `my-swak-home`이라는 홈 디렉토리를 만들고, 그 안에 `config.yml`을 원하는 형식으로 편집한다.

그 디렉토리로 들어가 아래와 같이 실행하면, 플러그인들은 메인 스레드에서 실행된다.(이를 테스트 모드라 하겠다.) 로그를 표준 출력으로 볼 수 있으며, 코드에 중단점을 설정할 수 있어 디버깅에 용이하다.

```
swak test
```

테스트 모드에서는 하나의 데이터 스트림에 대해서만 실행할 수 있다. 설정 파일에 데이터 스트림이 여럿있다면, 실행할 데이터 스트림의 태그를 지정하자. (지정하지 않으면 최초로 등장하는 데이터 스트림이 선택)

```
swak test --tag foo  # foo 데이터 스트림에 대해 테스트
```

## 외부 플러그인 설치

필요한 플러그인을 GitHub에서 찾아 설치한다. Swak의 외부 플러그인은 `swak-plugin-`으로 시작한다. 여기서는 스트림을 Fluentd로 전달하는 출력 플러그인을 설치해보겠다.

### 코드 받기
먼저 Swak 소스 코드 디렉토리 아래 `plugins` 디렉토리로 이동하고

    cd swak/plugins

사용할 외부 플러그인을 `clone`한다.

    git clone https://github.com/haje01/swak-plugin-fluentd.git fluentd

마지막 인자로 `swak-plugin-`을 제외한 플러그인 이름만을 디렉토리 명으로 추가한 것에 주의하자. 이렇게 하면 `plugins` 아래 `fluentd` 디렉토리에 플러그인 코드가 받아진다.

다음과 같이 확인할 수 있다.

```
$ swak list
+------------+----------------------------+
| Plugin     | Description                |
|------------+----------------------------|
| in.counter | Emit incremental number.   |
| out.stdout | Output to standard output. |
+------------+----------------------------+
```

플러그인에 따라 의존 패키지 설치가 필요할 수 있다.(자세한 것은 해당 플러그인 `README.md` 를 참고하자.)

### 의존 패키지 설치

플러그인 디렉토리에 `requirements.txt`가 있다면 플러그인이 의존하는 외부 패키지가 있다는 뜻이다. 해당 디렉토리로 이동 후 다음과 같이 설치해주자.

    pip install -r requirements.txt

### 실행

설치된 플러그인은 Swak 기동시에 자동으로 등록되고, 실행할 수 있다.

# 빌드 그리고 배포

개발 및 테스트는 파이썬 개발 환경이 설치된 곳에서 인터프리터를 이용하는 것이 좋지만, 실제 배포를 위해서는 실행 가능한 형태가 편하다. Swak는 PyInstaller를 통해 파이썬 코드를 실행 파일로 빌드한다.

## PyInstaller 설치

[PyInstaller](http://www.pyinstaller.org) 홈페이지를 참고하여 배포 대상 OS에 맞는 버전의 PyInstaller를 미리 설치하자.

> PyEnv를 사용하는 경우 빌드시 동적 라이브러리를 찾지 못해 에러가 나올 수 있다. 이때는 macOS의 경우 `--enable-framework` 옵션으로 파이썬을 빌드하여 설치해야 한다. 자세한 것은 [이 글](https://github.com/pyenv/pyenv/issues/443)을 참고하자. 리눅스의 경우 `--enable-shared` 옵션으로 빌드한다.

> 윈도우에서 파이썬 3.5를 사용할 때 "ImportError: DLL load failed" 에러가 나오는 경우 [Microsoft Visual C++ 2010 Redistributable Package](https://www.microsoft.com/en-us/download/confirmation.aspx?id=5555)를 설치하자.

## 빌드

윈도우에서는 다음과 같이 빌드한다.

```
cd swak
tools\build.bat
```

리눅스/macOS에서는 다음과 같이 빌드한다.

```
cd swak
./tools/build.sh
```

정상적으로 빌드가 되면, `dist/` 디렉토리 아래 `swakd.exe` (윈도우) 또는 `swakd` (리눅스/macOS) 실행 파일이 만들어진다. 이것을 배포하면 된다.

> PyInstaller는 파이썬 3.x에서 실행 파일의 버전 정보 설정에 문제가 있다. 이 [페이지](https://github.com/pyinstaller/pyinstaller/issues/1347)를 참고하자.

## OS별 설치 및 관리

### 윈도우

실행 파일이 있는 디렉토리로 이동해, 다음과 같이 하면 윈도우 리부팅 시에도 서비스가 자동으로 시작하도록 서비스 설치가 된다.

    swakd.exe --startup=auto install

다음과 같이 서비스를 시작하고

    swakd.exe start

다음과 같이 서비스를 종료한다.

    swakd.exe stop

### Unix 계열(Linux/macOS)

다음과 같이 데몬을 시작하고

    swakd start

다음과 같이 데몬을 종료한다.

    swakd stop
