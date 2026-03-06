import { Button, Card, Form, Input, Modal, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';
import { formatDate } from '../../utils/date';

function UsersPanel() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();

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
        // 编辑时，如果密码为空则不传 password 字段
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
      width: 160,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            编辑
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
      <Table rowKey="id" dataSource={users} columns={columns} loading={loading} scroll={{ x: 1000 }} />

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
    </Card>
  );
}

export default UsersPanel;
