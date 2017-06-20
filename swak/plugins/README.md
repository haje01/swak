# 기본 플러그인 소개

이 페이지에서는 Swak의 기본 플러그인에 대해 설명한다. 일반적인 내용은 [기본](../../README.md) 페이지를 참고한다.

## in.FileTail
대상 파일에 새로 추가된 내용을 스트림에 넣는다.

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

## encoding (선택)
파일의 인코딩을 명시. UTF8을 제외한 다른 인코딩의 파일은 꼭 명시해야 한다.

