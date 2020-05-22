import config
import redis

redis = redis.Redis(db=1)


def set_state(id, value):
    redis.hset(id, "state", value)
    return True


def get_current_state(id):
    try:
        return redis.hget(id, "state").decode("utf-8")
    except Exception as e:
        print(f"Exception: {e}")
        return config.States.START_STATE.value


def set_state_value(id, key, value):
    redis.hset(id, key, value)
    return True


def get_values(id):
    return redis.hgetall(id)


def clear_fields(id, *args):
    redis.hdel(id, *args)
    return True
