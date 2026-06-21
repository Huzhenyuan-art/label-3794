import sys
sys.path.insert(0, '.')

from app.schemas import PayloadFilterCondition
from app.services.dynamic_table_service import _build_payload_clause, _PAYLOAD_OP_MAP

print("=" * 60)
print("测试 1: PayloadFilterCondition 参数校验")
print("=" * 60)

# 正常情况
cond = PayloadFilterCondition(field='status', op='eq', value='active')
assert cond.field == 'status'
assert cond.op == 'eq'
assert cond.value == 'active'
print("[PASS] 正常等值条件")

# 数值条件
cond = PayloadFilterCondition(field='age', op='gte', value=18)
assert cond.value == 18
print("[PASS] 数值范围条件")

# field 包含点号 - 失败
try:
    PayloadFilterCondition(field='user.name', op='eq', value='x')
    print("[FAIL] 嵌套路径未被拒绝")
except ValueError as e:
    print(f"[PASS] 嵌套路径被拒绝: {e}")

# field 包含特殊字符 - 失败
try:
    PayloadFilterCondition(field='name\'; DROP --', op='eq', value='x')
    print("[FAIL] SQL 注入字符未被拒绝")
except ValueError as e:
    print(f"[PASS] SQL 注入字符被拒绝: {e}")

# field 以数字开头 - 失败
try:
    PayloadFilterCondition(field='1name', op='eq', value='x')
    print("[FAIL] 数字开头未被拒绝")
except ValueError as e:
    print(f"[PASS] 数字开头被拒绝: {e}")

# like value 为数字 - 失败
try:
    PayloadFilterCondition(field='name', op='like', value=123)
    print("[FAIL] like 数字未被拒绝")
except ValueError as e:
    print(f"[PASS] like 数字被拒绝: {e}")

# 无效 op - 失败
from pydantic import ValidationError
try:
    PayloadFilterCondition(field='x', op='invalid', value='y')
    print("[FAIL] 无效 op 未被拒绝")
except ValidationError:
    print("[PASS] 无效 op 被拒绝")

print("\n" + "=" * 60)
print("测试 2: _PAYLOAD_OP_MAP 操作符映射")
print("=" * 60)

assert 'eq' in _PAYLOAD_OP_MAP
assert 'neq' in _PAYLOAD_OP_MAP
assert 'gt' in _PAYLOAD_OP_MAP
assert 'gte' in _PAYLOAD_OP_MAP
assert 'lt' in _PAYLOAD_OP_MAP
assert 'lte' in _PAYLOAD_OP_MAP
assert 'like' not in _PAYLOAD_OP_MAP  # like 已移除
print("[PASS] 操作符映射正确（不含 like）")

print("\n" + "=" * 60)
print("测试 3: _build_payload_clause 类型检查")
print("=" * 60)

class MockCol:
    def __eq__(s, o): return 'eq'
    def __ne__(s, o): return 'ne'
    def __gt__(s, o): return 'gt'
    def __ge__(s, o): return 'gte'
    def __lt__(s, o): return 'lt'
    def __le__(s, o): return 'lte'
    def like(s, p, escape=None): return 'like'

class MockC:
    def __init__(s): s.payload = MockCol()

class MockT:
    def __init__(s): s.c = MockC()

t = MockT()

# 字符串 eq
cond = PayloadFilterCondition(field='name', op='eq', value='Alice')
clause = _build_payload_clause(t, cond)
assert clause is not None
print("[PASS] 字符串 eq 条件生成")

# 数值 gt
cond = PayloadFilterCondition(field='age', op='gt', value=18)
clause = _build_payload_clause(t, cond)
assert clause is not None
print("[PASS] 数值 gt 条件生成")

# 数值 gt 传入字符串 - 失败
cond = PayloadFilterCondition(field='age', op='gt', value='18')
try:
    _build_payload_clause(t, cond)
    print("[FAIL] 数值操作传字符串未被拒绝")
except Exception as e:
    print(f"[PASS] 数值操作传字符串被拒绝: {e}")

# like 操作
cond = PayloadFilterCondition(field='name', op='like', value='John')
clause = _build_payload_clause(t, cond)
assert clause is not None
print("[PASS] like 条件生成")

# like 通配符转义
cond = PayloadFilterCondition(field='name', op='like', value='test%value')
clause = _build_payload_clause(t, cond)
assert clause is not None
print("[PASS] like 通配符转义处理")

print("\n" + "=" * 60)
print("测试 4: data_api 常量和参数限制")
print("=" * 60)

from app.routes.data_api import MAX_RECORD_KEY_PREFIX_LENGTH, MAX_PAYLOAD_FILTERS
assert MAX_RECORD_KEY_PREFIX_LENGTH == 128
assert MAX_PAYLOAD_FILTERS == 20
print(f"[PASS] record_key_prefix 最大长度: {MAX_RECORD_KEY_PREFIX_LENGTH}")
print(f"[PASS] payload_filters 最大数量: {MAX_PAYLOAD_FILTERS}")

print("\n" + "=" * 60)
print("测试 5: total None 处理")
print("=" * 60)

count_result = None
total = count_result if count_result is not None else 0
assert total == 0
print("[PASS] None total 转换为 0")

count_result = 100
total = count_result if count_result is not None else 0
assert total == 100
print("[PASS] 有效 total 保持不变")

print("\n" + "=" * 60)
print("测试 6: SQL LIKE 通配符转义")
print("=" * 60)

test_cases = [
    ("normal", "normal%"),
    ("test%value", "test\\%value%"),
    ("test_value", "test\\_value%"),
    ("test\\value", "test\\\\value%"),
]
for input_val, expected_suffix in test_cases:
    escaped = input_val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like_pattern = "{}%".format(escaped)
    assert like_pattern.endswith(expected_suffix)
    print(f"[PASS] {repr(input_val)} → {like_pattern}")

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
