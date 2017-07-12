# Swak

[![Travis Status](https://travis-ci.org/haje01/swak.svg?branch=master)](https://travis-ci.org/haje01/swak)
[![AppVeyor Status](https://ci.appveyor.com/api/projects/status/1u1ku2s75ny38na1?svg=true)](https://ci.appveyor.com/project/haje01/swak)
[![Codecov Status](https://codecov.io/gh/haje01/swak/branch/master/graph/badge.svg)](https://codecov.io/gh/haje01/swak)

파이썬 기반 다목적 에이전트 플랫폼. '스왴'으로 읽는다. 

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
- 바이너리로 빌드되어 배포 될 때는, 일반적으로 실행 파일과 같은 폴더에 `config.yml`을 만들어 주면 된다. 

# Swak 활용 예

## Swak 커맨드 라인 명령

Swak은 커맨드라인에서 다양한 명령을 실행할 수 있다.

### 설치된 플러그인 리스트 보기

    swak list

### 특정 플러그인의 도움말 보기

    swak desc in.FakeData

### 특정 플러그인 설정을 YAML로 출력하기

    swak yaml in.SizeBuffer --max-chunk 1048576 --yaml --with-default

### 간단히 테스트하기

    swak run 'in.FakeData --type people | out.Stdout'

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
  - cmd.Sleep:
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
        type: FileTail
        path: C:/myprj/logs/mylog.txt
        pos_dir: C:/swak_temp/pos
        encoding: cp949

    # 주석 라인 제거
    # fil.Filter:
      exclude: ^\s*#.*

    # 커스텀 포맷 파서
    - par.MyLogParser

    # 5분 단위로 버퍼링
    - buf.TimeBuffer:
        minutes: 5

    # 출력 실패 대응
    - cmd.Failover:
        outputs:
          # Fluentd 서버 1
          - out.Fluentd
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
    - buf.LineBuffer:
        lines: 100

    # 외부 프로세스 실행
    - out.Exec:
        cmd: "/usr/bin/r /etc/detect_abuse.r",

    # 표준 출력으로 스트림 보냄
    - out.Stdout
```

`in.MySQLTail` 플러그인은 지정된 MySQL DB의 테이블에서 추가되는 내용을 스트림으로 보낸다.

`out.LineBuffer`는 스트림의 내용을 버퍼에 쌓아두다가, 지정한 라인(행) 되었을 때만 출력해 지나친 IO를 막아준다.

`out.Exec` 플러그인은 데이터 스트림을 임시 파일로 저장한 후, 지정된 별도 프로세스에서 처리하게 하고, 결과를 다시 임시 파일로 받는다. 여기에서는 받은 결과를 표준 출력으로 보내고 있다.

    
## 설정 파일 테스트하기

커스텀한 설정 파일을 테스트하는 경우를 생각해보자. `my-swak-home`이라는 홈 디렉토리를 만들고, 그 안에 `config.yml`을 원하는 형식으로 편집한다.

이제 아래와 같이 실행하면 설정 파일내 `task`는 메인 스레드에서 실행된다.(이를 테스트 모드라 하겠다.) 로그를 표준 출력으로 볼 수 있으며, 코드에 중단점을 설정할 수 있어 디버깅에 용이하다.

```
python -m swak.test --home my-swak-home
```

테스트 모드에서는 하나의 테스크만 실행될 수 있다. 설정 파일에 테스크가 하나 이상있다면, 실행할 테스크의 번호를 지정하자. (지정하지 않으면 첫 번째 테스크가 실행)

```
python -m swak.test --home my-swak-home --task 2  # 두 번째 테스크를 실행
```

`SWAK_HOME` 환경 파일을 설정해 두면, 매번 `--home` 옵션을 주지 않아도 된다.

```
python -m swak.test --task 2
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
Swak has 1 plugin(s):
------------------------------------
in.Counter   - Emit incremental number.
out.Fluentd  - Output to Fluentd.
------------------------------------
```

플러그인에 따라 의존 패키지 설치가 필요할 수 있다. 자세한 것은 해당 플러그인 `README.md` 를 참고하자.

### 의존 패키지 설치

플러그인 디렉토리에 `requirements.txt`가 있다면 플러그인이 의존하는 외부 패키지가 있다는 뜻이다. 다음과 같이 설치해주자.

    pip install -r requirements.txt

### 실행

설치된 플러그인은 Swak 기동시에 자동으로 등록되고, 실행할 수 있다.

# 빌드 그리고 배포

개발 및 테스트는 파이썬 개발 환경이 설치된 곳에서 인터프리터를 이용하는 것이 좋지만, 실제 배포를 위해서는 실행 가능한 형태가 편하다. Swak는 PyInstaller를 통해 파이썬 코드를 실행 파일로 빌드한다.

## PyInstaller 설치

[PyInstaller](http://www.pyinstaller.org) 홈페이지를 참고하여 배포 대상 OS에 맞는 버전의 PyInstaller를 미리 설치하자.

> PyEnv를 사용하는 경우 빌드시 동적 라이브러리를 찾지 못해 에러가 나올 수 있다. 이때는 macOS의 경우 `--enable-framework` 옵션으로 파이썬을 빌드하여 설치해야 한다. 자세한 것은 [이 글](https://github.com/pyenv/pyenv/issues/443)을 참고하자. Linux의 경우 `--enable-shared` 옵션으로 빌드한다.

> 윈도우에서 파이썬 3.5를 사용할 때 "ImportError: DLL load failed" 에러가 나오는 경우 [Microsoft Visual C++ 2010 Redistributable Package](https://www.microsoft.com/en-us/download/confirmation.aspx?id=5555)를 설치하자.

## 빌드

윈도우에서는 다음과 같이 빌드한다.

```
cd swak
tools\build.bat
```

Linux/macOS에서는 다음과 같이 빌드한다.

```
cd swak
./tools/build.sh
```

정상적으로 빌드가 되면, `dist/` 폴더 아래 `swakd.exe` (윈도우) 또는 `swakd` (Linux/macOS) 실행 파일이 만들어진다. 이것을 배포하면 된다.

> PyInstaller는 파이썬 3.x에서 실행 파일의 버전 정보 설정에 문제가 있다. 이 [페이지](https://github.com/pyinstaller/pyinstaller/issues/1347)를 참고하자.

## OS별 설치 및 관리

### 윈도우

실행 파일이 있는 폴더로 이동해, 다음과 같이 하면 윈도우 리부팅 시에도 서비스가 자동으로 시작하도록 서비스 설치가 된다.

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

### 실행 파일로 설정 파일 테스트

개발/빌드 머신에서 잘 되다가 설치시 장비에서 문제가 발생하거나, 현장에서 설정 파일을 변경해야 하는 경우가 있다. 빌드된 실행 파일로 테스트는 다음과 같이 한다.

    swakd test -c config.yml

테스트 모드에서는 하나의 테스크만 실행될 수 있다. 설정 파일에 테스크가 하나 이상있다면, 실행할 테스크의 번호를 지정하자. (지정하지 않으면 첫 번째 테스크가 실행)

    swakd test config.yml -t 2  # 두 번째 테스크를 실행
