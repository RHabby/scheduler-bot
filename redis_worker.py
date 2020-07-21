import json

import redis

import config

redis = redis.Redis(db=1)


def set_state(id: int, value: str) -> bool:
    redis.hset(id, "state", value)
    return True


def set_kboard(id: int, key: str, value: str) -> bool:
    try:
        kboard = json.loads(get_value(id, key))
        kboard.append(value)
    except TypeError:
        kboard = [value]

    set_state_value(id, key, json.dumps(kboard))
    return True


def get_current_state(id: int) -> str:
    try:
        return redis.hget(id, "state").decode("utf-8")
    except Exception as e:
        print(f"Exception: {e}")
        return config.States.START_STATE.value


def set_state_value(id: int, key: str, value: str) -> bool:
    redis.hset(id, key, value)
    return True


def get_value(id: int, key: str) -> str:
    return redis.hget(id, key)


def get_values(id: int) -> dict:
    return redis.hgetall(id)


def clear_fields(id: int, *args) -> bool:
    redis.hdel(id, *args)
    return True


def add_to_queue(name: str, data: str) -> bool:
    # добавляем в лист rpush
    redis.rpush(name, data)
    return True


def get_from_queue(name: str):
    # удаляем и возвращаем первое значение в лист lpop
    if redis.llen(name) > 0:
        file = json.loads(redis.lpop(name))
        return file
    else:
        return False


def queue_len(key: str) -> int:
    return redis.llen(key)


def queue_entities(key: str) -> list:
    entities = [json.loads(x.decode("utf-8"))
                for x in redis.lrange(key, 0, -1)]
    return entities


if __name__ == "__main__":
    # print(get_value(25043361, "channels"))
    print(queue_len("queue"))
    print(queue_entities("queue"))
