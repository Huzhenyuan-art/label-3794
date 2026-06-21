import logging
import sys
from datetime import datetime

sys.path.insert(0, ".")

from app.utils import (
    safe_getattr,
    safe_list,
    safe_serialize_iterable,
    safe_serialize_related,
    serialize_group,
    serialize_groups_collection,
    serialize_tag,
    serialize_tags_collection,
    to_iso,
)


logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


class MockPartialGroup:
    def __init__(self, id_val=None, name_val=None, missing_field=False):
        self.id = id_val
        if not missing_field:
            self.name = name_val
        self.description = "Test"

    def __getattr__(self, item):
        if item == "sort_order":
            raise AttributeError("sort_order 属性被意外删除")
        raise AttributeError(item)


class MockPartialTag:
    def __init__(self, id_val=None, name_val=None, color_val=None):
        self.id = id_val
        self.name = name_val
        if color_val is not None:
            self.color = color_val


class MockPartialPage:
    def __init__(self, page_id=1, name="Test", groups=None, tags=None, bad_attr=False):
        self.id = page_id
        self.name = name
        self.description = "Desc"
        self.category = "Cat"
        self.developer = "Dev"
        self.main_page = "index.html"
        self.storage_folder = "folder"
        self.route_path = "/pages/x"
        self.table_prefix = "pre"
        self.table_name = "tbl"
        self.status = "enabled"
        self.uploader_admin_id = 1
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self._groups = groups or []
        self._tags = tags or []
        self._bad_attr = bad_attr

    @property
    def groups(self):
        if self._bad_attr and self._groups is None:
            raise RuntimeError("DetachedInstanceError: 会话已关闭，无法加载 groups")
        return self._groups

    @property
    def tags(self):
        if self._bad_attr and self._tags is None:
            raise RuntimeError("DetachedInstanceError: 会话已关闭，无法加载 tags")
        return self._tags


passed = 0
failed = 0


def assert_eq(name, actual, expected):
    global passed, failed
    if actual == expected:
        logger.info("  [PASS] %s", name)
        passed += 1
    else:
        logger.error("  [FAIL] %s | 期望=%r 实际=%r", name, expected, actual)
        failed += 1


def test_safe_getattr():
    logger.info("测试 1: safe_getattr - 空值与异常属性")
    assert_eq("None 对象返回默认值", safe_getattr(None, "x", 42), 42)

    class A:
        x = None

    assert_eq("属性为 None 返回默认值", safe_getattr(A(), "x", "default"), "default")

    assert_eq("属性正常返回", safe_getattr(A(), "x", "default", ), "default")

    class B:
        pass

    assert_eq("不存在属性返回默认值", safe_getattr(B(), "y", "missing"), "missing")

    class C:
        @property
        def bad(self):
            raise ValueError("内部异常")

    assert_eq("属性抛出异常返回默认值", safe_getattr(C(), "bad", "fallback"), "fallback")
    logger.info("")


def test_to_iso():
    logger.info("测试 2: to_iso - 日期边界情况")
    assert_eq("None 返回 None", to_iso(None), None)
    assert_eq("正常日期格式化", isinstance(to_iso(datetime(2024, 1, 1, 12, 0, 0)), str), True)

    class BadDate:
        def __bool__(self):
            return True

        def strftime(self, _fmt):
            raise TypeError("非标准日期对象")

    assert_eq("异常日期返回 None", to_iso(BadDate()), None)
    logger.info("")


def test_safe_list():
    logger.info("测试 3: safe_list - 集合转换")
    assert_eq("None → []", safe_list(None), [])
    assert_eq("正常列表", safe_list([1, 2, 3]), [1, 2, 3])
    assert_eq("元组 → 列表", safe_list((1, 2)), [1, 2])

    class BadIter:
        def __iter__(self):
            raise RuntimeError("迭代器损坏")

    assert_eq("损坏迭代器 → []", safe_list(BadIter()), [])
    logger.info("")


def test_safe_serialize_related():
    logger.info("测试 4: safe_serialize_related - 关联对象序列化")
    assert_eq("None 对象 → None", safe_serialize_related(None, [("id", 1)]), None)

    g = MockPartialGroup(id_val=5, name_val="GroupA")
    result = safe_serialize_related(g, [("id", None), ("name", ""), ("sort_order", 0)])
    assert_eq("正常字段序列化", result["id"], 5)
    assert_eq("正常字段序列化 name", result["name"], "GroupA")
    assert_eq("抛错属性返回默认值", result["sort_order"], 0)

    g2 = MockPartialGroup(id_val=6, name_val="GroupB", missing_field=True)
    result2 = safe_serialize_related(g2, [("id", None), ("name", "X")])
    assert_eq("缺失字段返回默认值", result2["name"], "X")
    logger.info("")


def test_serialize_group_tag():
    logger.info("测试 5: serialize_group / serialize_tag - 独立对象")
    g = MockPartialGroup(id_val=10, name_val="运维组")
    result = serialize_group(g)
    assert_eq("分组 id 正确", result["id"], 10)
    assert_eq("分组 name 正确", result["name"], "运维组")
    assert_eq("分组 description 默认值正确", result["description"], "Test")

    t = MockPartialTag(id_val=20, name_val="重要")
    result_t = serialize_tag(t)
    assert_eq("标签 id 正确", result_t["id"], 20)
    assert_eq("标签 name 正确", result_t["name"], "重要")
    assert_eq("标签缺失 color 返回默认 blue", result_t["color"], "blue")

    assert_eq("None group 返回 None", serialize_group(None), None)
    assert_eq("None tag 返回 None", serialize_tag(None), None)
    logger.info("")


def test_serialize_collections():
    logger.info("测试 6: 集合序列化 - 空 / 部分缺失 / 有 None")

    result = serialize_groups_collection([])
    assert_eq("空列表返回空", result, [])

    result = serialize_groups_collection(None)
    assert_eq("None 返回空列表", result, [])

    groups = [
        MockPartialGroup(id_val=1, name_val="G1"),
        None,
        MockPartialGroup(id_val=None, name_val="NoID"),
        MockPartialGroup(id_val=2, name_val="G2"),
    ]
    result = serialize_groups_collection(groups)
    assert_eq("过滤 None 和无 ID 对象，返回 2 个", len(result), 2)
    assert_eq("第 1 个 id=1", result[0]["id"], 1)
    assert_eq("第 2 个 id=2", result[1]["id"], 2)

    tags = [
        MockPartialTag(id_val=1, name_val="T1", color_val="red"),
        MockPartialTag(id_val=2, name_val=None, color_val="green"),
        MockPartialTag(id_val=3, name_val="T3"),
    ]
    result_t = serialize_tags_collection(tags)
    assert_eq("3 个有效标签", len(result_t), 3)
    assert_eq("缺失 name 返回空", result_t[1]["name"], "")
    assert_eq("缺失 color 返回 blue", result_t[2]["color"], "blue")
    logger.info("")


def test_page_serialize_simulated():
    logger.info("测试 7: 页面完整序列化（模拟 admin_pages._serialize_page）")

    from app.routes.admin_pages import _serialize_page
    from app.models import BusinessPage

    g1 = MockPartialGroup(id_val=99, name_val="财务系统")
    t1 = MockPartialTag(id_val=77, name_val="核心", color_val="red")

    page = MockPartialPage(page_id=1, name="工资核算", groups=[g1, None], tags=[t1])

    result = _serialize_page(page)
    assert_eq("页面 id=1", result["id"], 1)
    assert_eq("页面 name", result["name"], "工资核算")
    assert_eq("过滤 None group 后 1 个", len(result["groups"]), 1)
    assert_eq("group name", result["groups"][0]["name"], "财务系统")
    assert_eq("tags 数量 1", len(result["tags"]), 1)
    assert_eq("tag color", result["tags"][0]["color"], "red")

    page2 = MockPartialPage(page_id=2, name="空关联页面", groups=[], tags=[])
    result2 = _serialize_page(page2)
    assert_eq("空 groups", result2["groups"], [])
    assert_eq("空 tags", result2["tags"], [])

    page3 = MockPartialPage(page_id=3, name="抛出异常页", groups=None, tags=None, bad_attr=True)
    result3 = _serialize_page(page3)
    assert_eq("异常降级 groups 空", result3["groups"], [])
    assert_eq("异常降级 tags 空", result3["tags"], [])
    logger.info("")


def test_public_serialize_simulated():
    logger.info("测试 8: 门户页面序列化（模拟 public._serialize）")
    from app.routes.public import _serialize

    t_bad = MockPartialTag(id_val=None, name_val="NoID")
    page = MockPartialPage(page_id=42, name="门户页", tags=[t_bad])
    result = _serialize(page)
    assert_eq("无 ID tag 被过滤", result["tags"], [])
    assert_eq("groups 空", result["groups"], [])
    logger.info("")


def test_iterable_serialize_with_exceptions():
    logger.info("测试 9: safe_serialize_iterable - 迭代过程中抛异常")

    class BadItem:
        pass

    def bad_serializer(item):
        if isinstance(item, BadItem):
            raise RuntimeError("序列化失败")
        return {"ok": item}

    items = [1, 2, BadItem(), 4]
    result = safe_serialize_iterable(items, bad_serializer)
    assert_eq("跳过失败元素，保留 3 个", len(result), 3)
    logger.info("")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始运行序列化健壮性测试")
    logger.info("=" * 60)
    try:
        test_safe_getattr()
        test_to_iso()
        test_safe_list()
        test_safe_serialize_related()
        test_serialize_group_tag()
        test_serialize_collections()
        test_page_serialize_simulated()
        test_public_serialize_simulated()
        test_iterable_serialize_with_exceptions()
    except Exception as exc:
        logger.exception("测试过程中出现未捕获异常：%s", exc)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("测试完成：通过=%d | 失败=%d", passed, failed)
    logger.info("=" * 60)
    sys.exit(0 if failed == 0 else 1)
