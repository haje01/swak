# swak-plugin-fluentd

Fluentd 서버로 출력한다.

## 설정 예시

```yml
- fluentd:
  ip: 127.0.0.1
  port: 24224
```

## 동작 방식

## 인자

### ip (필수)
Fluentd 서버의 IP

### port (선택)
Fluentd 서버의 접속 포트. 생략하면 기본값 24224가 이용된다.
