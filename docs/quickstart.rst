
********
시작하기
********

여기서는 Swak의 활용 예를 통해 설명하겠다. 먼저 기본 용어부터 설명하겠다.

기본 용어
=========

- **데이터** - Swak은 기본적으로 **텍스트** 데이터를 다룬다.(만약 바이너리 데이터를 다루어야 한다면, 그것을 위한 플러그인을 통해 변환 후 가능할 것이다.) 내부적으로 Swak은 모든 텍스트를 **utf8** 로 인코딩하여 사용한다.
- **라인(행)** - 개행문자 ``\n`` 으로 분리되는 텍스트 데이터를 **라인** 또는 **행** 이라 한다.
- **레코드** - 라인을 의미 단위로 파싱한 결과물을 말한다. 레코드는 '키': '밸류' 형식, 즉 파이썬의 Dictonary 형식이다.
- **이벤트** - 레코드에 발생 시간 필드가 추가된 것을 이벤트 또는 **데이터 이벤트** 라고 한다.
- **태그** - 이벤트를 분류하기 위한 정보. 자세한 것은 :ref:`event_tag` 를 참고하자.
- **청크** - 버퍼는 레코드를 모아서 처리하는데, 이 단위를 청크라 한다.


사용해 보기
===========

설치가 끝났으면 간단하게 사용해보자.


커맨드 라인 명령
================

Swak은 커맨드라인에서 다양한 명령을 실행할 수 있다.

설치된 플러그인 리스트 보기
---------------------------

.. code-block:: shell

    swak list

특정 플러그인의 도움말 보기
---------------------------

특정 플러그인의 도움말을 보기 위해서 ``desc`` 명령을 사용한다.

.. code-block:: shell

    swak desc in.counter

아래와 같은 결과가 나온다.

.. code-block:: shell

    Usage: in.counter [OPTIONS]

      Generate incremental numbers.

    Options:
      -c, --count INTEGER  Count to emit.  [default: 3]
      -f, --field INTEGER  Count of fields.  [default: 1]
      -d, --delay FLOAT    Delay seconds before next count.  [default: 0.0]
      --help               Show this message and exit.


테스트 커맨드로 간단히 테스트하기
---------------------------------

Swak은 정식 설정파일을 작성하기 전에 플러그인의 기능을 테스트할 수 있는 **테스트 커맨드** 를 지원한다. 테스트 커맨드는 유닉스 쉘 명령어 형식으로 사용한다. 다음의 예를 보자.

.. code-block:: shell

    swak run 'in.counter | out.stdout'

파이프 기호 ``|`` 를 통해 플러그인이 연쇄적으로 동작한다. 예는 아래와 같은 일을 한다.

1. ``in.counter`` 플러그인으로 카운트 데이터를 생성
2. 표준 출력으로 출력

실행 결과는 아래와 같다

.. code-block:: shell

    ["test", 1504687495.505614, {"f1": 1}]
    ["test", 1504687495.505723, {"f1": 2}]
    ["test", 1504687495.505755, {"f1": 3}]

첫 번째 값은 테스트 커맨드의 스트림 태그, 두 번째 값은 emit 시간, 그리고 마지막 값은 레코드이다.

.. note:: 마지막의 ``out.stdout`` 은 생략해도 된다. 즉 아래도 같은 결과가 나온다.

    .. code-block:: shell

        swak run 'in.counter'



설정 파일
=========

설정 파일은 YAML(``*.yml``) 형식으로 Swak이 할 일을 명시한다. 샘플 설정 파일을 통해 Swak의 사용법을 살펴보자.

설정 파일에서 가장 핵심은 ``tags`` 필드이다. 이 아래에 여러 이벤트 태그가 필드로 등장한다. 각 태그는 하나 이상의 플러그인의 리스트로 구성된다.

미니멀한 설정 파일의 예
-----------------------

가짜 데이터를 표준 출력을 통해 출력하는 간단한 예를 살펴보자.

.. code-block:: yaml

    sources:
        - in.counter --tag test # 'test' 이벤트 스트림으로 카운트 이벤트 보냄

    matches:
        test:  # 'test' 이벤트 스트림의 이벤트를
            - out.stdout  # 표준 출력에 출력

위의 스크립트는 다음과 같은 식으로 이해하면 된다.

1. ``sources`` 아래 다양한 입력 플러그인들을 선언한다.
2. ``in.counter`` 에서 발생한 이벤트의 태그를 ``--tag test`` 로 지정한다.
3. ``matches`` 아래 다양한 태그를 위한 처리 플러그인이 정의된다.
4. ``test`` 태그로 보내진 이벤트를 ``out.stdout`` 플러그인을 통해 표준 출력으로 보낸다.

좀 더 복잡한 예
---------------

다음은 특정 파일을 테일링하여 Fluentd로 전송하는 설정 파일의 예이다. 조금 복잡하지만 순서대로 처리되기에 어려울 것은 없다.

.. code-block:: yaml

    sources:
      # 주석행을 제거하며 대상 파일 테일링하고 'test' 이벤트 스트림으로 보냄.
      - in.filetail --tag test --path C:\myprj\logs\mylog.txt --posdir C:\swak_temp\p

    matches:
      test:  # 이벤트 태그
        # 커스텀 포맷 파서
        - par.mylog
        # 5분 단위로 버퍼링
        - buf.file time --minute 5
        # Fluentd 전송
        - out.fluentd --server 192.168.0.1 --server: 169.168.0.2 --last /tmp/failed.txt --start_by: ip

1. ``in.filetail`` 은 지정된 파일에서 추가된 행을 보낸다.
2. ``par.mylog`` 는 행을 파싱하여 레코드 형태로 보낸다.
3. ``out.timebuffer`` 는 레코드를 버퍼에 쌓다가, 지정한 시간이 되었을 때 한 번씩 출력해 지나친 IO를 막아준다.
4. ``out.fluentd`` 플러그인은 버퍼에서 받은 데이터를 지정된 Fluentd 서버로 보낸다. 이때 하나 이상의 서버를 받고, 에러가 발생하면 다른 서버로 시도한다. 시작 출력은 ``start_by`` 로 지정하는 값에 의존하여 결정된다. 모든 출력이 실패하면 ``last`` 로 지정된 출력으로 이벤트를 보낸다.


다양한 경로를 거치는 처리
-------------------------

데이터가 항상 플러그인이 등장하는 순서대로 처리되는 것은 아니다. 새로운 태그의 지정을 통해 다양한 경로로 처리될 수 있다. 아래의 예를 살펴보자.

.. code-block:: yaml

    sources:
      - in.counter --tag started

    matches:
      started:
        - mod.reform -w host ${hostname} --tag modified

      modified:
        - out.stdout


이 경우는 ``in.counter`` 에서 생성된 이벤트가 ``started`` 태그를 통해 ``mod.reform`` 에서 처리되고, 다시 ``modified`` 태그로 ``out.stdout`` 플러그인에 전달된다.


설정 파일 테스트
================

커스텀한 설정 파일을 테스트하는 경우를 생각해보자. ``my-swak-home`` 이라는 홈 디렉토리를 만들고, 그 안에 ``config.yml`` 을 원하는 형식으로 편집한다.

그 디렉토리로 들어가 아래와 같이 실행하면, 플러그인들은 메인 스레드에서 실행된다.(이를 테스트 모드라 하겠다.) 로그를 표준 출력으로 볼 수 있으며, 코드에 중단점을 설정할 수 있어 디버깅에 용이하다.

.. code-block:: shell

    swak test


테스트 모드에서는 하나의 기본 태그로만 이벤트를 다룰 수 있다. 설정 파일에 태그가 여럿있다면, 아래와 같이 실행할 태그를 지정하자. (지정하지 않으면 최초로 등장하는 태그가 선택)

.. code-block:: shell

    swak test --tag foo  # foo 태그에 대해 테스트


외부 플러그인 설치
==================


필요한 플러그인을 GitHub에서 찾아 설치한다. Swak의 외부 플러그인의 저장소명은 ``swak-`` 으로 시작한다. 여기서는 이벤트를 Fluentd로 전달하는 출력 플러그인을 설치해보겠다.


코드 받기
---------

먼저 Swak 소스 코드 디렉토리 아래 ``plugins`` 디렉토리로 이동하고,

.. code-block:: shell

    cd swak/plugins

사용할 외부 플러그인을 ``clone`` 한다.

.. code-block:: shell

    git clone https://github.com/haje01/swak-fluentd.git

이렇게 하면 ``plugins`` 아래 ``swak-fluentd`` 디렉토리에 플러그인 코드가 받아진다.

.. note:: ``stdplugins`` 는 Swak의 표준 플러그인이 있는 디렉토리이다. 이곳에 있는 파일을 수정하거나, 이 디렉토리에 새로운 파일을 받지 않도록 주의하자.



다음과 같이 설치된 것을 확인할 수 있다.

.. code-block:: shell

    Swak has 2 plugin(s):
    +------------+----------------------------+
    | Plugin     | Description                |
    |------------+----------------------------|
    | in.counter | Emit incremental number.   |
    | out.stdout | Output to standard output. |
    +------------+----------------------------+

플러그인에 따라 의존 패키지 설치가 필요할 수 있다.(자세한 것은 해당 플러그인의 ``README.md`` 를 참고하자.)


의존 패키지 설치
----------------

플러그인 디렉토리에 ``requirements.txt`` 가 있다면 플러그인이 의존하는 외부 패키지가 있다는 뜻이다. 해당 디렉토리로 이동 후 다음과 같이 설치해주자.

.. code-block:: shell

    pip install -r requirements.txt


실행
----

설치된 플러그인은 Swak 기동시에 자동으로 등록되고, 실행할 수 있다.

