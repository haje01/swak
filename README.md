# Swak

파이썬 기반 멀티 OS 에이전트 플랫폼. '스왴'으로 읽는다. 

이 페이지에서는 Swak 사용자를 위한 기본적인 내용을 설명한다. 더 자세한 내용은 아래 링크를 참고한다.

- [개발자 문서](swak/README.md)
- [기본 플러그인 소개](swak/plugins/README.md)

## 무엇인가?

- 멀티 OS(Windows, Linux, OS X)에서
- 서비스(데몬) 형태로
- 내부 파이썬 코드를 실행하거나
- 외부 프로세스를 실행히주는 
- 틀

## 플러그인 구조

Swak은 어플리케이션의 기본 틀외 모든 기능들을 플러그인으로 구현한다. 다음과 같은 기본 플러그인들이 있다.

- FileTail - 파일에 추가된 내용 입력으로 가져옴
- Fluentd - Fluentd로 출력
- failover - 출력 실패시 대체

자세한 것은 [기본 플러그인 소개](swak/plugins/README.md)를 참고하자. 

이외에 아래와 같은 다양한 외부 플러그인이 나올 수 있을 것이다.

- DB Tailing
- 시스템(윈도우 이벤트, syslog) 로그 입력으로 가져오기
- 프로세스/커넥션 모니터링
- Elasticsearch, Logstash로 출력

## 설치

    git clone https://github.com/haje01/swak.git
    cd swak
    pip install -r requirements.txt
    pip intall .

# Swak 활용 예

## 설정 파일

설정 파일은 YAML(`*.yml`) 형식으로 Swak이 할 일을 명시한다. 샘플 설정 파일을 통해 Swak의 사용법을 살펴보자.

입력과 출력 플러그인은 각각 `in` 및 `out` 로 시작한다. `task` 태그 아래에 순차적으로 처리할 일을 명시한다. 

### 가짜 데이터를 표준 출력을 통해 출력

```yml
# 테스크 선언
- task:
  # 가짜 데이터 생성
  - in.FakeData:
      type: people

  # 표준 출력으로 스트림 보냄
  - out.Stdout

  # 1초 후 다시 시작
  - sleep:
      seconds: 1
```

위의 스크립트는 다음과 같은 식으로 진행된다:

1. `FakeData` 플러그인을 통해 가짜 데이터를 생성하고 
2. `out.Stdout` 플러그인은 표준 출력으로 스트림을 보낸다.
3. 1초 쉬었다가 다시 처음부터 재개한다.

### 특정 파일을 테일링하여 Fluentd로 전송

다음은 파일 테일링 설정 파일의 예이다.

```yml
# 테스크 선언
- task:
  # 대상 파일 테일링
  - in.FileTail:
      path: C:/myprj/logs/mylog.txt
      pos_dir: C:/swak_temp/pos
      encoding: cp949

  # 커스텀 포맷 파서
  - out.MyLogParser

  # 5분 단위로 버퍼링
  - out.TimedBuffer:
      minutes: 5

  # 출력 실패 대응
  - failover:
    outputs:
    # Fluentd 서버 1
    - out.Fluentd:
        ip: 192.168.0.1
    # Fluentd 서버 2            
    - out.Fluentd:
        ip: 169.168.0.2
    # 그래도 실패하면 파일에
    last: 
      out.File: 
        path: /tmp/failed.txt
    # ip값 기반으로 출력 선택
    start_by: ip
```


`in.FileTail`은 지정된 파일에서 추가된 내용을 스트림으로 보낸다.

`out.TimedBuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 시간이 되었을 때만 출력해 지나친 IO를 막아준다.

`failover` 함수는 인자 리스트 중 하나로 출력을 한다, 에러가 발생하면 다른 리스트로 시도한다. 시작 출력은 `start_by`로 지정하는 값에 의존하여 결정된다. 모든 출력이 실패하면 `last`로 지정된 출력으로 스트림을 보낸다. `out.Fluentd` 플러그인은 스트림을 지정된 Fluentd 서버로 보낸다.

### 로그 DB를 테일링

다음은 DB 테일링 설정 파일의 예이다.

```yml
# 테스크 스레드 생성
- task:
  - in.MySQLTail:
    ip: 127.0.0.1
    db: logdb
    table: logtbl

  # 100라인 단위로 버퍼링
  - out.LinedBuffer:
    lines: 100

  # 외부 프로세스 실행
  - out.Exec:
    cmd: "/usr/bin/r /etc/detect_abuse.r",

  # 표준 출력으로 스트림 보냄
  - out.Stdout
```

`in.MySQLTail` 플러그인은 지정된 MySQL DB의 테이블에서 추가되는 내용을 스트림으로 보낸다.

`out.LinedBuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 라인(행) 되었을 때만 출력해 지나친 IO를 막아준다.

`out.Exec` 플러그인은 데이터 스트림을 임시 파일로 저장한 후, 지정된 별도 프로세스에서 처리하게 하고, 결과를 다시 임시 파일로 받는다. 여기에서는 받은 결과를 표준 출력으로 보내고 있다.
    
## 스크립트로 설정 파일 테스트하기

다음과 같이 실행하면 설정 파일내 `task`는 메인 스레드에서 실행된다. 로그를 표준 출력으로 볼 수 있으며, 코드에 중단점을 설정할 수 있어 디버깅에 용이하다.

```
python -m swak.test config.yml
```

테스트 모드에서는 하나의 테스크만 실행될 수 있다. 설정 파일에 테스크가 하나 이상있다면, 실행할 테스크의 번호를 지정하자. (지정하지 않으면 첫 번째 테스크가 실행)

```
python -m swak.test config.yml -t 2  # 두 번째 테스크를 실행
```

## 외부 플러그인 설치

필요한 플러그인을 GitHub에서 찾아 설치한다. Swak의 외부 플러그인은 `swak-plugin-`으로 시작한다. 여기서는 스트림을 Fluentd로 전달하는 출력 플러그인을 설치해보겠다.

### 코드 받기
먼저 Swak 소스 코드 디렉토리 아래 `plugins` 디렉토리로 이동하고

    cd swak/plugins

사용할 외부 플러그인을 `clone`한다.

    git clone https://github.com/haje01/swak-plugin-fluentd.git fluentd

마지막 인자로 `swak-plugin-`을 제외한 플러그인 이름만을 디렉토리 명으로 추가한 것에 주의하자. 이렇게 하면 `plugins` 아래 `fluentd` 디렉토리에 플러그인 코드가 받아진다.

### 의존 패키지 설치

플러그인 디렉토리에 `requirements.txt`가 있다면 플러그인이 의존하는 패키지가 있다는 뜻이다. 다음과 같이 설치해주자.

    pip install -r requirements.txt

### 실행

설치된 플러그인은 Swak 기동시에 자동으로 등록되고, 실행할 수 있다.

# 빌드, 배포, 그리고 설치

개발 및 테스트는 파이썬 개발 환경이 설치된 곳에서 인터프리터를 이용하는 것이 좋지만, 실제 배포를 위해서는 실행 가능한 형태가 편하다. Swak는 PyInstaller를 통해 파이썬 코드를 실행 파일로 빌드한다.

## PyInstaller 설치

[PyInstaller](http://www.pyinstaller.org) 홈페이지를 참고하여 배포 대상 OS에 맞는 버전의 PyInstaller를 미리 설치하자.

> PyEnv를 사용하는 경우 빌드시 동적 라이브러리를 찾지 못해 에러가 나올 수 있다. 이때는 OS X의 경우 `--enable-framework` 옵션으로 파이썬을 빌드하여 설치해야 한다. 자세한 것은 [이 글](https://github.com/pyenv/pyenv/issues/443)을 참고하자. Linux의 경우 `--enable-shared` 옵션으로 빌드한다.

## 빌드 파일
빌드할 때는 사용할 외부 플러그인만 포함하여 빌드하는 것이 좋다. 이를 위해서 **빌드 파일** 이 필요하다. 빌드 파일은 YAML(`*-build.yml`) 형식으로 다음과 같은 구조를 가진다.

```yml
# 빌드명. 생략가능(없으면 기본 이름 swak으로 빌드된다. 하나 이상의 빌드가 필요한 경우 사용한다.)
-name: [빌드명]

# 사용할 외부 플러그인 리스트
-plugins:
  - [참조할 외부 플러그인1]
  - [참조할 외부 플러그인2]
  ...
```

예를 들어 다음과 같은 빌드 설정파일 `myprj-build.yml`이 있다고 할 때,

```yml
- name: myprj
- plugins:
  - swak-plugin-syslog
  - swak-plugin-fluentd
```

아래와 같이 실행하면 빌드가 된다.

    swak-build myprj-build.yml

정상적으로 빌드가 되면, `dist/` 폴더 아래 `swak-myprj` 실행 파일이 만들어진다. 이것을 배포하면 된다. 필요에 따라 목적에 맞는 Swak 실행 파일을 만들어 관리하자.

> 빌드명이 없으면 기본 파일명 `swak`로 빌드된다. 이후 설명에서는 `swak`을 기준으로 하겠다.

## OS별 설치 및 관리

### 윈도우

실행 파일이 있는 폴더로 이동해, 다음과 같이 하면 윈도우 리부팅 시에도 서비스가 자동으로 시작하도록 서비스 설치가 된다.

    swak --startup=auto install

다음과 같이 서비스를 시작하고

    swak start

다음과 같이 서비스를 종료한다.

    swak stop

### Unix 계열(Linux/OS X)

다음과 같이 데몬을 시작하고

    swak start

다음과 같이 데몬을 종료한다.

    swak stop

### 실행 파일로 설정 파일 테스트

개발/빌드 머신에서 잘 되다가 설치시 장비에서 문제가 발생하거나, 현장에서 설정 파일을 변경해야 하는 경우가 있다. 빌드된 실행 파일로 테스트는 다음과 같이 한다.

    swak test config.yml

테스트 모드에서는 하나의 테스크만 실행될 수 있다. 설정 파일에 테스크가 하나 이상있다면, 실행할 테스크의 번호를 지정하자. (지정하지 않으면 첫 번째 테스크가 실행)

    swak test config.yml -t 2  # 두 번째 테스크를 실행
