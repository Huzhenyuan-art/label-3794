import { AppstoreOutlined } from '@ant-design/icons';
import {
  Button,
  Card,
  Checkbox,
  Col,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';
import { formatDate } from '../../utils/date';

const { Text, Paragraph } = Typography;

function UsersPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [form] = Form.useForm();
  const [allPages, setAllPages] = useState([]);
  const [selectedPageIds, setSelectedPageIds] = useState([]);
  const [authLoading, setAuthLoading] = useState(false);
  const [savingAuth, setSavingAuth] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/users');
      setUsers(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const openCreate = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ status: 'active' });
    setOpen(true);
  };

  const openEdit = (user) => {
    setEditingUser(user);
    form.resetFields();
    form.setFieldsValue({
      username: user.username,
      display_name: user.display_name || '',
      status: user.status,
      password: '',
    });
    setOpen(true);
  };

  const submit = async () => {
    try {
      const values = await form.validateFields();
      if (editingUser) {
        const payload = {
          display_name: values.display_name || null,
          status: values.status,
        };
        if (values.password && values.password.trim()) {
          payload.password = values.password;
        }
        await http.put(`/api/admin/users/${editingUser.id}`, payload);
        message.success('用户更新成功');
      } else {
        await http.post('/api/admin/users', values);
        message.success('用户创建成功');
      }
      setOpen(false);
      fetchUsers();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const removeUser = async (user) => {
    try {
      await http.delete(`/api/admin/users/${user.id}`);
      message.success('用户删除成功');
      fetchUsers();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const openAuth = async (user) => {
    setAuthUser(user);
    setAuthLoading(true);
    try {
      const { data } = await http.get(`/api/admin/users/${user.id}/authorized-pages`);
      setAllPages(data.data.all_pages || []);
      setSelectedPageIds(data.data.authorized_page_ids || []);
      setAuthOpen(true);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setAuthLoading(false);
    }
  };

  const saveAuth = async () => {
    setSavingAuth(true);
    try {
      await http.put(`/api/admin/users/${authUser.id}/authorized-pages`, {
        page_ids: selectedPageIds,
      });
      message.success('页面授权已更新');
      setAuthOpen(false);
      fetchUsers();
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setSavingAuth(false);
    }
  };

  const togglePage = (pageId) => {
    setSelectedPageIds((prev) =>
      prev.includes(pageId) ? prev.filter((id) => id !== pageId) : [...prev, pageId]
    );
  };

  const selectAllPages = () => {
    setSelectedPageIds(allPages.map((p) => p.id));
  };

  const clearAllPages = () => {
    setSelectedPageIds([]);
  };

  const columns = [
    { title: '用户名', dataIndex: 'username', width: 180 },
    { title: '显示名称', dataIndex: 'display_name', width: 180 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      render: (value) => (
        <Tag color={value === 'active' ? 'green' : 'default'}>{value === 'active' ? '启用' : '禁用'}</Tag>
      ),
    },
    {
      title: '授权页面数',
      dataIndex: 'authorized_page_ids',
      width: 120,
      render: (ids) => (
        <Tag color="blue">{(ids || []).length} 个</Tag>
      ),
    },
    {
      title: '上次登录',
      dataIndex: 'last_login_at',
      width: 180,
      render: (value) => formatDate(value),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (value) => formatDate(value),
    },
    {
      title: '操作',
      width: 240,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Button size="small" type="primary" onClick={() => openAuth(record)}>
            授权页面
          </Button>
          <Popconfirm title="确认删除该用户？" onConfirm={() => removeUser(record)} okText="确认" cancelText="取消">
            <Button size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="用户管理"
      extra={
        <Button type="primary" onClick={openCreate}>
          新增用户
        </Button>
      }
    >
      <Table rowKey="id" dataSource={users} columns={columns} loading={loading} scroll={{ x: 1200 }} />

      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={submit}
        okText={editingUser ? '保存' : '创建'}
        cancelText="取消"
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          {!editingUser && (
            <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
              <Input />
            </Form.Item>
          )}
          <Form.Item name="display_name" label="显示名称">
            <Input placeholder="请输入显示名称" />
          </Form.Item>
          <Form.Item
            name="password"
            label={editingUser ? '新密码（留空不修改）' : '密码'}
            rules={editingUser ? [] : [{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder={editingUser ? '留空则不修改密码' : '请输入密码'} />
          </Form.Item>
          <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select
              options={[
                { value: 'active', label: '启用' },
                { value: 'disabled', label: '禁用' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`为用户「${authUser?.username || ''}」授权业务页面`}
        open={authOpen}
        onCancel={() => setAuthOpen(false)}
        onOk={saveAuth}
        okText="保存授权"
        cancelText="取消"
        confirmLoading={savingAuth}
        width={720}
        destroyOnClose
      >
        {authLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Empty description="加载中..." />
          </div>
        ) : allPages.length === 0 ? (
          <Empty description="暂无可授权的业务页面，请先创建页面" />
        ) : (
          <>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text type="secondary">
                已选择 <Tag color="blue">{selectedPageIds.length}</Tag> / {allPages.length} 个页面
              </Text>
              <Space>
                <Button size="small" onClick={selectAllPages}>全选</Button>
                <Button size="small" onClick={clearAllPages}>清空</Button>
              </Space>
            </div>
            <div
              style={{
                border: '1px solid #f0f0f0',
                borderRadius: 8,
                padding: 16,
                maxHeight: 420,
                overflowY: 'auto',
                background: '#fafafa',
              }}
            >
              <Row gutter={[12, 12]}>
                {allPages.map((page) => {
                  const checked = selectedPageIds.includes(page.id);
                  const disabled = page.status !== 'enabled';
                  return (
                    <Col xs={24} md={12} key={page.id}>
                      <div
                        onClick={() => !disabled && togglePage(page.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 10,
                          padding: 12,
                          borderRadius: 8,
                          background: checked ? '#e6f4ff' : '#fff',
                          border: `1px solid ${checked ? '#1677ff' : '#e8e8e8'}`,
                          cursor: disabled ? 'not-allowed' : 'pointer',
                          opacity: disabled ? 0.5 : 1,
                          transition: 'all 0.2s',
                        }}
                      >
                        <Checkbox checked={checked} disabled={disabled} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                            <AppstoreOutlined style={{ color: '#4a7dff' }} />
                            <Text strong style={{ color: disabled ? '#999' : '#162338' }}>
                              {page.name}
                            </Text>
                            {disabled && <Tag color="default">已禁用</Tag>}
                          </div>
                          <Paragraph
                            ellipsis={{ rows: 2 }}
                            style={{ marginBottom: 4, color: '#666', fontSize: 13 }}
                          >
                            {page.description || '暂无描述'}
                          </Paragraph>
                          <Tag color="geekblue" style={{ fontSize: 12 }}>{page.category}</Tag>
                        </div>
                      </div>
                    </Col>
                  );
                })}
              </Row>
            </div>
          </>
        )}
      </Modal>
    </Card>
  );
}

export default UsersPanel;
