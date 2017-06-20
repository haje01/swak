# 기본 플러그인 소개

이 페이지에서는 Swak의 기본 플러그인에 대해 설명한다. 일반적인 내용은 [기본](../../README.md) 페이지를 참고한다.

## 입력 플러그인

### in.FileTail
대상 파일에 새로 추가된 내용을 스트림에 넣는다. 다음과 같은 인자가 있다.

#### path (필수)
감시할 파일의 경로. 다음과 같은 식으로 표현 가능하다.

    path: /path/to/%Y/%m/mylog-%m%d_*.txt

다음과 같은 파일이 선택된다.

    /path/to/2017/06/mylog-0617_1.txt
    /path/to/2017/06/mylog-0617_2.txt
    ...

`,`를 사용해 하나 이상의 경로를 지정할 수 있다.

    path: /path/to/%Y/%m/mylog1-%m%d_*.txt, /path/to/%Y/%m/mylog2-%m%d_*.txt

#### tag (필수)
스트림 태그 정보. `프로젝트.카테고리.타입`형식으로 기입한다.

#### pos_dir (필수)
대상 파일에서 읽어 들인 위치를 저장할 디렉토리를 지정

    pos_dir: $SWAK_TMP/pos/

문제가 발생해 로그가 정상 전송되지 않은 경우는, 이 디렉토리 아래 `*.pos`파일을 지우고 Swak을 다시 시작해준다.

#### encoding (선택)
파일의 인코딩을 명시. UTF8을 제외한 다른 인코딩의 파일은 꼭 명시해야 한다.

## 출력 플러그인

## 보통 플러그인

### failover

`failover`는 출력 실패에 대응한다. 

```yml
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

- 하나 이상의 출력을 등록해두고, 
- 기동시 그것들 중 하나가 임의 또는 `start_by` 옵션에 따라 선택된다. 
- 사용중인 출력이 동작하지 않으면, 다른 출력을 대신 선택하여 사용한다. 
- 모든 출력이 실패했을때 `last`옵션이 있다면 그쪽으로 출력한다.

다음과 같은 인자가 있다.

#### outputs (필수)

하나 이상의 출력 플러그인을 등록한다. 

#### start_by (옵션)

등록된 출력 

#### last (옵션)
등록된 모든 출력이 실패하면 지정된 출력으로 저장한다.

    last:
      out.File:
        path: /tmp/failed.txt
