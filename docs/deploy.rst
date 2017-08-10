******
빌드와 배포
******

개발 및 테스트는 파이썬 개발 환경이 설치된 곳에서 인터프리터를 이용하는 것이 좋지만, 실제 배포를 위해서는 실행 가능한 형태로 만드는 것이 좋다. Swak는 PyInstaller를 통해 파이썬 코드를 실행 파일로 빌드한다.


PyInstaller 설치
==============

`PyInstaller <http://www.pyinstaller.org>`_ 홈페이지를 참고하여 배포 대상 OS에 맞는 버전의 PyInstaller를 미리 설치하자.

.. note:: PyEnv를 사용하는 경우 빌드시 동적 라이브러리를 찾지 못해 에러가 나올 수 있다. 이때는 macOS의 경우 ``--enable-framework`` 옵션으로 파이썬을 빌드하여 설치해야 한다. 자세한 것은 `이 글 <http://github.com/pyenv/pyenv/issues/443>`_ 을 참고하자. 리눅스의 경우 ``--enable-shared`` 옵션으로 빌드한다.


.. note:: 윈도우에서 파이썬 3.5를 사용할 때 "ImportError: DLL load failed" 에러가 나오는 경우 `Microsoft Visual C++ 2010 Redistributable Package <http://www.microsoft.com/en-us/download/confirmation.aspx?id=5555>`_ 를 설치하자.


빌드
====

윈도우에서는 다음과 같이 빌드한다.::

    cd swak
    tools\build.bat


리눅스/macOS에서는 다음과 같이 빌드한다.::

    cd swak
    ./tools/build.sh


정상적으로 빌드가 되면, ``dist/`` 디렉토리 아래 ``swakd.exe`` (윈도우) 또는 ``swakd`` (리눅스/macOS) 실행 파일이 만들어진다. 이것을 배포하면 된다.

.. note:: PyInstaller는 파이썬 3.x에서 실행 파일의 버전 정보 설정에 문제가 있다. 이 `페이지 <http://github.com/pyinstaller/pyinstaller/issues/1347>`_ 를 참고하자.


OS별 설치 및 관리
===========

윈도우
----

실행 파일이 있는 디렉토리로 이동해, 다음과 같이 하면 윈도우 리부팅 시에도 서비스가 자동으로 시작하도록 서비스 설치가 된다.::

    swakd.exe --startup=auto install

다음과 같이 서비스를 시작하고::

    swakd.exe start

다음과 같이 서비스를 종료한다.::

    swakd.exe stop

Unix 계열(Linux/macOS)
^^^^^^^^^^^^^^^^^^^^

다음과 같이 데몬을 시작하고::

    swakd start

다음과 같이 데몬을 종료한다.::

    swakd stop
