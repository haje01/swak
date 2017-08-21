Swak 로그 설정
--------------

설정 파일안의 ``logger`` 필드 를 이용해서, Swak 자체의 로그 설정을 할 수있다. 기본 설정은 아래와 같다.

.. code-block:: yaml

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


기본 설정은 다음과 같은 뜻이다:

- 로그의 필드 구분자는 탭(``\t``) 이다.
- 표준 출력과 파일 양쪽으로 로그를 남긴다.
- 양쪽 다 로그 레벨은 ``DEBUG`` 이다.
- 로그는 실행 파일이 있는 디렉토리 아래 ``logs/`` 디렉토리에 남는다.
- 파일은 100MiB 단위로 로테이션 하며, 10개이상이면 로그 로테이션을 한다.

만약, 이중 일부의 수정이 필요하다면 수정이 필요한 필드만 계층을 유지하고 기입하면 된다:

.. code-block:: yml

    logger:
        handlers:
            file:
                level: CRITICAL
                filename: C:\logs\{SWAK_SVC_NAME}-log.txt


위와 같이 설정하면 다른 것들은 기본값 그대로 두고, 파일 로그 핸들러의 레벨, 저장 경로만 수정하게 된다.
