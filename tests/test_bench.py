"""Test benchmark."""
import time
from threading import Thread, Lock

from queue import Queue


from swak.data import MultiDataStream


def test_bench_queue_events():
    """Bench queue with individual event."""
    num_thread = 5
    num_events = 10000
    events_per_stream = 10
    total = [0]
    total_lock = Lock()
    q = Queue()

    def inp(count):
        """Input."""
        for i in range(int(count / events_per_stream)):
            times = [time.time()] * events_per_stream
            records = [dict(name="kjj", score=100, host="localhost")] * \
                events_per_stream
            ds = MultiDataStream(times, records)
            try:
                q.put(ds)
            except Exception as e:
                print(e)

    def out():
        """Output."""
        max_qsize = 0
        while True:
            i = q.get()
            if i is None:
                break
            with total_lock:
                total[0] += 1
            q.task_done()
            qsize = q.qsize()
            if max_qsize < qsize:
                max_qsize = qsize
        print("max_qsize: {}".format(max_qsize))

    # output thread
    ot = Thread(target=out)
    ot.start()

    threads = []
    # input threads
    for t in range(num_thread):
        t = Thread(target=inp, args=(num_events,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    q.put(None)
    ot.join()
    assert total[0] == int(num_events * num_thread / events_per_stream)
