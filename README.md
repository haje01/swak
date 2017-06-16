# Swak

파이썬 기반 멀티 OS 에이전트 플랫폼. '스윀'으로 읽는다.

## 무엇?

- 멀티 OS(Windows, Linux, OSX)에서
- 서비스(데몬) 형태로
- 내부 파이썬 코드를 실행하거나
- 외부 프로세스를 실행히주는 
- 틀

## 기본 기능

- 플러그인 방식으로 파이썬 코드 실행 (with 디버깅)
- Stream IN/OUT 형식으로 외부 프로세스 실행
- Logging
- Parser
- Buffering
- Failover
- 인터랙티브 환경
- 실행 파일 빌드


## 주요 플러그인
- 파일 Tailing
- DB Tailing
- 시스템(윈도우 이벤트, Syslog) 로그
- 프로세스/커넥션 모니터링
- file, fluentd, elasticsearch, logstash로 출력

## 샘플 코드

인터랙티브 환경에서 아래와 같은 코드를 입력하여 테스트 할 수 있다.

# 메인 스레드에서

```python
main(
     # 더미 데이터 생성
     in.DummyData(type="people"),
     # 결과 표준 출력
     out.Stdout()
)
```
    
테스크는 별도 스레드로 동작한다. 다음은 파일 테일링 스크립트의 예이다.

# 테스크 스레드 생성

```python
task(
      # 대상 파일 테일링
      in.FileTailing("/var/log/mylog.txt"),
      # 커스텀 포맷 파서
      out.MyLogParser(),
      # 5분 단위로 버퍼링
      out.TimeSlicedBuffer("5M"),
      # 실패 대응
      failover(
        # Fluentd 서버 1
        out.Fluentd("192.168.0.1"),
        # Fluentd 서버 2            
        out.Fluentd("169.168.0.2"),
        # 그래도 실패하면 파일에
        last=out.File('/tmp/failed.txt'),
        start="ip"
      )
)
```
    
다음은 DB 테일링 스크립트의 예이다.

# 테스크 스레드 생성

```python
task(
    in.MySQLTailing("127.0.0.1", 'logdb'),
    # 100라인 단위로 버퍼링
    out.SizeSlicedBuffer(100),
    # 외부 프로세스 실행
    out.Exec(
        "/usr/bin/r detect.r",
    )
    # 결과 표준 출력
    out.Stdout()
)
```
    
## 폴더 구조
    
    swak/
        bin/  # 실행 파일들
        swak/  # 코드
            plugins/  # 표준 플러그인들

