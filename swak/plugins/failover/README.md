# failover

`failover`는 출력 실패에 대응한다. 

## 설정 예시
```yml
- failover:
    outputs:
    # Fluentd 서버 1
    - out.Fluentd:
        ip: 192.168.0.1
    # Fluentd 서버 2            
    - out.Fluentd:
        ip: 169.168.0.2
    # 그래도 실패하면
    last:
      out.File:
        path: /tmp/failed.txt
    # ip값 기반으로 출력 선택
    start_by: ip
```

## 동작 방식
- 하나 이상의 출력을 등록해두고, 
- 기동시 그것들 중 하나가 임의 또는 `start_by` 옵션에 따라 선택된다. 
- 사용중인 출력이 동작하지 않으면, 다른 출력을 대신 선택하여 사용한다. 
- 모든 출력이 실패했을때 `last`옵션이 있다면 그쪽으로 출력한다.

## 인자

### outputs (필수)

하나 이상의 출력 플러그인을 등록한다. 

### start_by (옵션)

등록된 출력 선택 방식을 지정한다.

- ip: 로컬 네트워크의 IP주소를 해싱

### last (옵션)

등록된 모든 출력이 실패하면 지정된 출력으로 저장한다.
