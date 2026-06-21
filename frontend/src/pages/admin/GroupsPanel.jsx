import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Space,
  Switch,
  Table,
  Tag,
  message,
} from 'antd';
import { useEffect, useState } from 'react';
import http, { extractErrorMessage } from '../../services/http';
import { formatDate } from '../../utils/date';

const { TextArea } = Input;

function GroupsPanel() {
  const [loading, setLoading] = useState(false);
  const [groups, setGroups] = useState([]);

  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);

  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/admin/groups');
      setGroups(data.data || []);
    } catch (error) {
      message.error(extractErrorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      await http.post('/api/admin/groups', values);
      setCreateOpen(false);
      createForm.resetFields();
      message.success('分组创建成功');
      fetchGroups();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const openEdit = (group) => {
    setEditingGroup(group);
    editForm.setFieldsValue({
      name: group.name,
      description: group.description,
      sort_order: group.sort_order,
      status: group.status,
    });
    setEditOpen(true);
  };

  const handleUpdate = async () => {
    try {
      const values = await editForm.validateFields();
      await http.put(`/api/admin/groups/${editingGroup.id}`, values);
      setEditOpen(false);
      setEditingGroup(null);
      message.success('分组更新成功');
      fetchGroups();
    } catch (error) {
      if (error?.errorFields) {
        return;
      }
      message.error(extractErrorMessage(error));
    }
  };

  const toggleStatus = async (group, enabled) => {
    try {
      await http.patch(`/api/admin/groups/${group.id}/status`, {
        status: enabled ? 'enabled' : 'disabled',
      });
      message.success('状态已更新');
      fetchGroups();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const deleteGroup = async (group) => {
    try {
      await http.delete(`/api/admin/groups/${group.id}`);
      message.success('分组已删除');
      fetchGroups();
    } catch (error) {
      message.error(extractErrorMessage(error));
    }
  };

  const columns = [
    {
      title: '分组名称',
      dataIndex: 'name',
      width: 180,
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (value) => value || '-',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      render: (value, record) => (
        <Space>
          <Tag color={value === 'enabled' ? 'green' : 'default'}>
            {value === 'enabled' ? '启用' : '禁用'}
          </Tag>
          <Switch checked={value === 'enabled'} onChange={(checked) => toggleStatus(record, checked)} />
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (value) => formatDate(value),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确认删除该分组？" onConfirm={() => deleteGroup(record)} okText="确认" cancelText="取消">
            <Button danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="分组管理"
      extra={
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          新增分组
        </Button>
      }
    >
      <Table rowKey="id" loading={loading} columns={columns} dataSource={groups} scroll={{ x: 1000 }} />

      <Modal
        title="新增分组"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreate}
        okText="提交"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={createForm} layout="vertical" initialValues={{ sort_order: 0 }}>
          <Form.Item name="name" label="分组名称" rules={[{ required: true, message: '请输入分组名称' }]}>
            <Input placeholder="例如：运维系统" maxLength={64} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} placeholder="请输入分组描述" maxLength={255} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} placeholder="数字越小越靠前" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑分组"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={handleUpdate}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="name" label="分组名称" rules={[{ required: true, message: '请输入分组名称' }]}>
            <Input maxLength={64} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={3} maxLength={255} />
          </Form.Item>
          <Form.Item name="sort_order" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

export default GroupsPanel;
