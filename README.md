# Swak

파이썬 기반 멀티 OS 에이전트 플랫폼. '스왴'으로 읽는다.

## 무엇?

- 멀티 OS(Windows, Linux, OSX)에서
- 서비스(데몬) 형태로
- 내부 파이썬 코드를 실행하거나
- 외부 프로세스를 실행히주는 
- 틀

## 기본 기능

주된 기능은 로컬 로그를 파싱하고 포워딩하는 것이나, 플러그인이나 외부 프로세스 실행을 통해 어떤 일이라도 할 수 있다.

- 플러그인 방식으로 파이썬 코드 실행 (with 디버깅)
- Stream IN/OUT 형식으로 외부 프로세스 실행
- 공통 로깅
- 로그 파싱
- 데이터 버퍼링
- Failover
- 인터랙티브 환경
- 실행 파일 빌드


## 주요 플러그인
Swak은 기본 기능외 모든 추가 기능들을 플러그인 구조로 구현한다. 대표적인 플러그인은 다음과 같은 것이 있다.

- 파일 Tailing
- DB Tailing
- 시스템(윈도우 이벤트, syslog) 로그
- 프로세스/커넥션 모니터링
- file, fluentd, elasticsearch, logstash로 출력

# Swak 활용하기

## 테스크 파일

테스크 파일은 YAML(`*.yml`) 형식으로 Swak이 할 일을 명시한다. 샘플 테스크 파일을 통해 Swak의 사용법을 살펴보자.

입력과 출력 플러그인은 각각 `in` 및 `out` 로 시작한다.

### 더미 데이터를 표준 출력을 통해 출력

```yml
# 테스크 선언
- task:
  # 더미 데이터 생성
  - in.DummyData:
      type: people
  # 표준 출력으로 스트림 보냄
  - out.Stdout
  # 1초 후 다시 시작
  - sleep:
      seconds: 1
```

`task` 태그 아래에 순차적으로 처리할 일을 명시한다. `out.Stdout` 플러그인은 표준 출력으로 스트림을 보낸다.

### 특정 파일을 테일링하여 Fluentd로 전송

다음은 파일 테일링 테스크 파일의 예이다.

```yml
# 테스크 선언
- task:
  # 대상 파일 테일링
  - in.FileTail:
      path: /var/log/mylog.txt
  # 커스텀 포맷 파서
  - out.MyLogParser
  # 5분 단위로 버퍼링
  - out.TimedBuffer:
      minutes: 5
  # 실패 대응
  - failover:
    outputs:
    # Fluentd 서버 1
    - out.Fluentd:
        ip: 192.168.0.1
    # Fluentd 서버 2            
    - out.Fluentd:
        ip: 169.168.0.2
    # 그래도 실패하면 파일에
    lastfile: /tmp/failed.txt
    # ip값 기반으로 출력 선택
    start_by: ip
```


`in.FileTail`은 지정된 파일에서 추가된 내용을 스트림으로 보낸다.

`out.TimedBuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 시간이 되었을 때만 출력해 지나친 IO를 막아준다.

`failover` 함수는 인자 리스트 중 하나로 출력을 하다, 에러가 발생하면 다른 리스트로 시도한다. 시작 출력은 `start_by`로 지정하는 값에 의존하여 결정된다. 모든 출력이 실패하면 `last`로 지정된 출력으로 스트림을 보낸다. `out.Fluentd` 플러그인은 스트림을 지정된 Fluentd 서버로 보낸다.

### 로그 DB를 테일링

다음은 DB 테일링 테스크 파일의 예이다.

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
    cmd: "/usr/bin/r detect.r",
  # 표준 출력으로 스트림 보냄
  - out.Stdout
```

`in.MySQLTail` 플러그인은 지정된 MySQL DB의 테이블에서 추가되는 내용을 스트림으로 보낸다.

`out.LinedBuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 라인(행) 되었을 때만 출력해 지나친 IO를 막아준다.

`out.Exec` 플러그인은 데이터 스트림을 임시 파일로 저장한 후, 지정된 별도 프로세스에서 처리하게 하고, 결과를 다시 임시 파일로 받는다. 여기에서는 받은 결과를 표준 출력으로 보내고 있다.
    
## 테스크 파일 동작 테스트하기

다음과 같이 실행하면 `task`는 메인 스레드에서 실행된다. 로그를 표준 출력으로 볼 수 있으며, 코드에 중단점을 설정할 수 있어 디버깅에 용이하다.

```
swak test task.yml
```

테스트 모드에서는 하나의 테스크만 실행될 수 있다. 설정파일 파일에 테스크가 하나 이상있다면, 실행할 테스크의 인덱스를 지정하자. (지정하지 않으면 첫 번째 테스크가 실행)

```
swak test task.yml -t 2  # 두 번째 테스크를 실행
```

## 외부 플러그인 설치

필요한 플러그인을 GitHub에서 찾아 설치한다. Swak의 외부 플러그인은 `swak-plugin-`으로 시작한다. 여기서는 스트림을 Fluentd로 전달하는 출력 플러그인을 설치해보겠다.

    git clone https://github.com/haje01/swak-plugin-fluentd.git

폴더로 이동 후 다음과 같이 설치한다.

    cd swak-plugin-fluentd
    python setup.py install

# 배포를 위해 빌드하기

개발 및 테스트는 파이썬 개발 환경이 설치된 곳에서 인터프리터를 이용하는 것이 좋지만, 실제 배포를 위해서는 실행 가능한 형태가 편하다. Swak는 PyInstaller를 통해 파이썬 코드를 실행 파일로 빌드한다.

## PyInstaller 설치

[PyInstaller](http://www.pyinstaller.org) 홈페이지를 참고하여 배포 대상 OS에 맞는 버전의 PyInstaller를 미리 설치하자.

## 빌드 파일
빌드할 때는 사용할 외부 플러그인만 포함하여 빌드하는 것이 좋다. 이를 위해서 **빌드 파일** 이 필요하다. 빌드 파일은 YAML(`*-build.yml`) 형식으로 다음과 같은 구조를 가진다.

```yml
# 빌드명. 생략가능(없으면 기본 이름 swak으로 빌드된다.)
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
- import:
  - swak-plugin-syslog
  - swak-plugin-fluentd
```

이를 이용하여 다음과 같이 실행하면 빌드가 된다.

    swak-build myprj-build.yml

정상적으로 빌드가 되면, `dist/` 폴더 아래 `swak-myprj` 파일이 만들어진다. 이것을 배포하면 된다.

# Swak 플러그인 만들기
플러그인은 크게 표준 플러그인과 외부 플러그인으로 나눈다. 표준 플러그인은 `swak/plugins`에 위치하며, Swak이 기동할 때 자동으로 타입에 맞는 패키지로 로딩된다. 표준 플러그인은 Swak코드 관리자가 만드는 것이기에, 여기에서는 외부 플러그인 만드는 법을 살펴보겠다.

## 외부 플러그인 규칙

여기서 Swak의 플러그인 코드는 GitHub을 통해서 관리되는 것으로 가정하며, 다음과 같은 규칙을 따라야 한다.

- GitHub의 저장소(Repository) 명은 `swak-plugin-` 으로 시작한다.
- 설치를 위한 `setup.py`를 제공해야 한다.
- 버전 정보를 갖는다.

## 샘플 플러그인
간단한 샘플 플러그인(`foo`)을 예제로 하여 알아보자.

1. 먼저 GitHub에서 `swak-plugin-foo`라는 저장소를 만든다.
2. 저장소를 로컬로 `clone`한다.

    `git clone https://github.com/GitHub계정/swak-plugin-foo.git`

3. 폴더로 이동 후, 개발용으로 설치한다.

    `python setup.py install -e .`

## 개발용 실행

