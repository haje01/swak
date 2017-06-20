# in.FileTail

대상 파일에 새로 추가된 내용을 스트림에 넣는다.

## 설정 예시
```yml
- in.FileTail:
  path: C:/myprj/logs/mylog.txt
  pos_dir: C:/swak_temp/pos
  tag: myprj.log
  encoding: cp949
```

## 동작 방식
- `path`로 지정된 파일들을 감시한다.
- 파일의 크기가 변했으면 변한 부분을 읽어들인다.
- 연결된 최종 출력 플러그인이 출력에 성공하면, 읽어들인 위치를 `pos_dir`아래 `[감시하는 파일명].pos`파일로 기록한다.

## 인자

### path (필수)
감시할 파일의 경로. 다음과 같은 식으로 표현 가능하다.

    path: /path/to/%Y/%m/mylog-%m%d_*.txt

다음과 같은 파일이 선택된다.

    /path/to/2017/06/mylog-0617_1.txt
    /path/to/2017/06/mylog-0617_2.txt
    ...

`,`를 사용해 하나 이상의 경로를 지정할 수 있다.

    path: /path/to/%Y/%m/mylog1-%m%d_*.txt, /path/to/%Y/%m/mylog2-%m%d_*.txt

### tag (필수)
스트림 태그 정보. `프로젝트.카테고리.타입`형식으로 기입한다.

### pos_dir (필수)
대상 파일에서 읽어 들인 위치를 저장할 디렉토리를 지정

    pos_dir: $SWAK_TMP/pos/

문제가 발생해 로그가 정상 전송되지 않은 경우는, 이 디렉토리 아래 `*.pos`파일을 지우고 Swak을 다시 시작해준다.

### encoding (선택)
파일의 인코딩을 명시. UTF8을 제외한 다른 인코딩의 파일은 꼭 명시해야 한다.

