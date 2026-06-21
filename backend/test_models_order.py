import sys
sys.path.insert(0, '.')

try:
    from app.models import (
        User,
        BusinessPage,
        user_page_association,
        page_group_association,
        page_tag_association,
        Admin,
        PageGroup,
        PageTag,
        LoginAudit,
        Notification,
        SystemSetting,
        DbConfig,
        PageVisit,
    )
    print("✅ 所有模型和关联表导入成功！")
    print(f"  - User 模型: {User}")
    print(f"  - BusinessPage 模型: {BusinessPage}")
    print(f"  - user_page_association: {user_page_association}")
    print(f"  - page_group_association: {page_group_association}")
    print(f"  - page_tag_association: {page_tag_association}")

    # 验证 User 模型的 relationship 配置正确
    assert hasattr(User, 'authorized_pages'), "User 模型缺少 authorized_pages 属性"
    print("\n✅ User.authorized_pages relationship 配置正确")

    # 验证 BusinessPage 模型的 relationships 配置正确
    assert hasattr(BusinessPage, 'authorized_users'), "BusinessPage 模型缺少 authorized_users 属性"
    assert hasattr(BusinessPage, 'groups'), "BusinessPage 模型缺少 groups 属性"
    assert hasattr(BusinessPage, 'tags'), "BusinessPage 模型缺少 tags 属性"
    print("✅ BusinessPage 所有 relationships 配置正确")

    # 验证关联表引用顺序正确
    import inspect
    user_source = inspect.getsource(User)
    bp_source = inspect.getsource(BusinessPage)

    # 检查 User 类体中引用了 user_page_association 变量
    if 'secondary=user_page_association' in user_source:
        print("✅ User 模型正确引用了 user_page_association 变量")
    else:
        print("❌ User 模型未正确引用 user_page_association")
        sys.exit(1)

    # 检查 BusinessPage 类体中引用了关联表变量
    if 'secondary=page_group_association' in bp_source and 'secondary=page_tag_association' in bp_source:
        print("✅ BusinessPage 模型正确引用了关联表变量")
    else:
        print("❌ BusinessPage 模型未正确引用关联表变量")
        sys.exit(1)

    print("\n🎉 所有验证通过！模型定义顺序正确无误。")

except NameError as e:
    print(f"❌ NameError: {e}")
    print("   这说明关联表定义顺序有问题，变量在引用时尚未定义。")
    sys.exit(1)
except Exception as e:
    print(f"❌ 验证失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
